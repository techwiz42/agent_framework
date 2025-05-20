from fastapi import HTTPException
import stripe
import traceback
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, User
from typing import Optional, Dict, Any
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Configure Customer Portal settings when service initializes
        self._configure_customer_portal()
        
        self.price_mapping = {
            settings.STRIPE_PRICE_10K_TOKENS: {
                'tokens': 10000,
                'name': '10K Tokens',
                'product_id': settings.STRIPE_PROD_10K_TOKENS
            },
            settings.STRIPE_PRICE_50K_TOKENS: {
                'tokens': 50000,
                'name': '50K Tokens',
                'product_id': settings.STRIPE_PROD_50K_TOKENS
            },
            settings.STRIPE_PRICE_100K_TOKENS: {
                'tokens': 100000,
                'name': '100K Tokens',
                'product_id': settings.STRIPE_PROD_100K_TOKENS
            },
            settings.STRIPE_PRICE_BASIC_SUB: {
                'tokens_per_month': 50000,
                'name': 'Basic Plan',
                'product_id': settings.STRIPE_PROD_BASIC_SUB
            },
            settings.STRIPE_PRICE_PRO_SUB: {
                'tokens_per_month': 300000,
                'name': 'Pro Plan',
                'product_id': settings.STRIPE_PROD_PRO_SUB
            }
        }

    def _configure_customer_portal(self):
        """Configure Stripe Customer Portal settings"""
        try:
            stripe.billing_portal.Configuration.create(
                business_profile={
                    "headline": "Cyberiad.ai Subscription Management",
                    "privacy_policy_url": f"{settings.FRONTEND_URL}/privacy",
                    "terms_of_service_url": f"{settings.FRONTEND_URL}/terms",
                },
                features={
                    "subscription_cancel": {
                        "enabled": True,
                        "mode": "at_period_end",
                        "proration_behavior": "none"
                    },
                    "subscription_pause": {
                        "enabled": False
                    },
                    "payment_method_update": {
                        "enabled": True
                    },
                    "invoice_history": {
                        "enabled": True
                    }
                },
                default_return_url=f"{settings.FRONTEND_URL}/billing"
            )
        except Exception as e:
            logger.error(f"Error configuring customer portal: {e}")
            # Don't raise - allow service to continue even if portal config fails

    async def get_or_create_customer(self, db: AsyncSession, user_id: str, email: str) -> str:
        """Get existing Stripe customer or create new one"""
        try:
            logger.info(f"Getting/creating customer for user_id: {user_id}, email: {email}")
            
            # Check if user already has stripe_customer_id
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            logger.info(f"Found user: {user}")
            logger.info(f"Current stripe_customer_id: {user.stripe_customer_id if user else None}")
            
            if user and user.stripe_customer_id:
                logger.info(f"Returning existing stripe customer: {user.stripe_customer_id}")
                return user.stripe_customer_id
                    
            # Create new Stripe customer
            logger.info("Creating new Stripe customer...")
            customer = stripe.Customer.create(
                email=email,
                metadata={
                    "user_id": user_id
                }
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            
            # Update user with new stripe_customer_id
            if user:
                logger.info(f"Updating user with stripe_customer_id: {customer.id}")
                user.stripe_customer_id = customer.id
                await db.commit()
                logger.info("Database update committed")
            
            return customer.id
                
        except Exception as e:
            logger.error(f"Error getting/creating Stripe customer: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def create_checkout_session(self, user_id: str, price_id: str) -> str:
        """Create Stripe checkout session"""
        try:
            logger.info(f"Creating checkout session for user {user_id}, price {price_id}")
            
            async with AsyncSessionLocal() as db:
                # Get user details
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User not found: {user_id}")
                    raise HTTPException(status_code=404, detail="User not found")

                logger.info(f"Found user {user.email}")

                # Get/create Stripe customer
                customer_id = await self.get_or_create_customer(db, str(user.id), user.email)
                logger.info(f"Got/created customer_id: {customer_id}")
                
                # Get product details
                product_info = self.price_mapping.get(price_id)
                if not product_info:
                    logger.error(f"Invalid product: {price_id}")
                    raise HTTPException(status_code=400, detail="Invalid product selection")

                logger.info(f"Product info: {product_info}")

                # Create checkout session
                session_params = {
                    'customer': customer_id,
                    'client_reference_id': user_id,
                    'payment_method_types': ['card'],
                    'line_items': [{
                        'price': price_id,
                        'quantity': 1,
                    }],
                    'mode': 'subscription' if 'tokens_per_month' in product_info else 'payment',
                    'success_url': f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                    'cancel_url': f"{settings.FRONTEND_URL}/billing/cancel",
                    'metadata': {
                        'user_id': str(user_id),
                        'tokens': str(product_info.get('tokens', 0)),
                        'tokens_per_month': str(product_info.get('tokens_per_month', 0)),
                        'name': product_info['name']
                    }
                }

                logger.info(f"Creating checkout session with params: {session_params}")
                checkout_session = stripe.checkout.Session.create(**session_params)
                return checkout_session.url
                    
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def create_portal_session(self, customer_id: str) -> str:
        """Create Stripe Customer Portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"{settings.FRONTEND_URL}/billing"
            )
            return session.url
        except Exception as e:
            logger.error(f"Error creating portal session: {str(e)}")
            raise

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Handle Stripe webhooks for successful payments and subscription events"""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )

            logger.info(f"Processing webhook event: {event.type}")

            if event.type == 'checkout.session.completed':
                session = event.data.object
                await self._handle_checkout_completed(session)
            elif event.type == 'invoice.payment_succeeded':
                invoice = event.data.object
                await self._handle_subscription_renewal(invoice)

        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _handle_checkout_completed(self, session):
        """Handle token addition for both one-time and subscription purchases"""
        try:
            user_id = session.metadata.get('user_id')
        
            # Determine tokens based on purchase type
            if session.mode == 'subscription':
                tokens = int(session.metadata.get('tokens_per_month', 0))
            else:  # one-time purchase
                tokens = int(session.metadata.get('tokens', 0))

            if not user_id or tokens <= 0:
                logger.error(f"Invalid purchase: user_id={user_id}, tokens={tokens}")
                return

            async with AsyncSessionLocal() as db:
                # Update user's token balance
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        tokens_purchased=User.tokens_purchased + tokens
                    )
                )
                await db.execute(stmt)
                await db.commit()

            logger.info(f"Added {tokens} tokens for user {user_id}")

        except Exception as e:
            logger.error(f"Error processing checkout: {str(e)}")
            raise

    async def _handle_successful_payment(self, session):
        """Handle successful one-time token purchase"""
        try:
            user_id = session.metadata.get('user_id')
            tokens = int(session.metadata.get('tokens', 0))
        
            if not user_id:
                logger.error("No user_id in session metadata")
                return
                
            if tokens <= 0:
                logger.error(f"Invalid token amount: {tokens}")
                return

            logger.info(f"Processing token purchase: {tokens} tokens for user {user_id}")
   
            async with AsyncSessionLocal() as db:
                # Update user's token balance
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        tokens_purchased=User.tokens_purchased + tokens
                    )
                )
                await db.execute(stmt)
                await db.commit()

            logger.info(f"Successfully added {tokens} tokens to user {user_id}")

        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            raise

    async def _handle_subscription_renewal(self, invoice):
        """Handle monthly subscription renewal and token grant"""
        try:
            subscription = await stripe.Subscription.retrieve(invoice.subscription)
            user_id = subscription.metadata.get('user_id')
            tokens_per_month = int(subscription.metadata.get('tokens_per_month', 0))

            if not user_id or tokens_per_month <= 0:
                logger.error(f"Invalid subscription metadata: user_id={user_id}, tokens={tokens_per_month}")
                return

            logger.info(f"Processing subscription renewal: {tokens_per_month} tokens for user {user_id}")

            async with AsyncSessionLocal() as db:
                # Update user's token balance
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        tokens_purchased=User.tokens_purchased + tokens_per_month
                    )
                )
                await db.execute(stmt)
                await db.commit()

                logger.info(f"Successfully added {tokens_per_month} subscription tokens to user {user_id}")

        except Exception as e:
            logger.error(f"Error processing subscription renewal: {str(e)}")
            raise

    async def _handle_subscription_cancelled(self, subscription):
        """Handle subscription cancellation"""
        try:
            user_id = subscription.metadata.get('user_id')
            if not user_id:
                logger.error("No user_id in subscription metadata")
                return

            logger.info(f"Processing subscription cancellation for user {user_id}")
            logger.info(f"Subscription cancelled for user {user_id}")

        except Exception as e:
            logger.error(f"Error processing subscription cancellation: {str(e)}")
            raise

stripe_service = StripeService()
