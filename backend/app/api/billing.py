from fastapi import APIRouter, Depends, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update
from pydantic import BaseModel, Field
from typing import Optional, List
from app.db.session import db_manager, User
from app.core.security import auth_manager
from app.core.config import settings
from app.services.stripe_service import stripe_service
import stripe
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])

class Product(BaseModel):
    id: str
    name: str
    price: float
    description: str
    tokens: Optional[int] = None
    tokens_per_month: Optional[int] = None

class BillingProducts(BaseModel):
    one_time: List[Product]
    subscriptions: List[Product]

class CheckoutRequest(BaseModel):
    product_key: str = Field(..., description="Key of the product to purchase")

class CheckoutResponse(BaseModel):
    checkout_url: str = Field(..., description="URL for the Stripe checkout session")

class WebhookResponse(BaseModel):
    status: str = Field(..., description="Status of webhook processing")
    detail: Optional[str] = None

class PaymentStatusResponse(BaseModel):
    status: str
    message: str
    tokens_purchased: int = 0
    product_name: str = ""

@router.get("/products", response_model=BillingProducts)
async def get_products(
    user = Depends(auth_manager.get_current_user)
):
    """Get available token purchase options and subscriptions"""
    try:
        return BillingProducts(
            one_time=[
                Product(
                    id=settings.STRIPE_PRICE_10K_TOKENS,
                    name="10,000 Tokens",
                    price=5.00,
                    description="Perfect for getting started",
                    tokens=10000
                ),
                Product(
                    id=settings.STRIPE_PRICE_50K_TOKENS,
                    name="50,000 Tokens",
                    price=20.00,
                    description="Most popular option",
                    tokens=50000
                ),
                Product(
                    id=settings.STRIPE_PRICE_100K_TOKENS,
                    name="100,000 Tokens",
                    price=35.00,
                    description="Best value for power users",
                    tokens=100000
                )
            ],
            subscriptions=[
                Product(
                    id=settings.STRIPE_PRICE_BASIC_SUB,
                    name="Basic Plan",
                    price=15.00,
                    description="50,000 tokens monthly",
                    tokens_per_month=50000
                ),
                Product(
                    id=settings.STRIPE_PRICE_PRO_SUB,
                    name="Pro Plan",
                    price=50.00,
                    description="300,000 tokens monthly",
                    tokens_per_month=300000
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch products")

@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,  # This should match your current model
    user = Depends(auth_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
):
    try:
        checkout_url = await stripe_service.create_checkout_session(
            user_id=str(user.id), 
            price_id=request.product_key  # This looks correct
        )
        return CheckoutResponse(checkout_url=checkout_url)
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.get("/success", response_model=PaymentStatusResponse)
async def checkout_success(
    session_id: str,
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Handle successful checkout redirection for both one-time payments and subscriptions."""
    try:
        # Retrieve the Stripe checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Extract common data
        user_id = checkout_session.client_reference_id
        if not user_id:
            raise HTTPException(status_code=400, detail="No user associated with this session")

        # Get the user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Quick hack to prevent double processing
        if hasattr(checkout_session, '_tokens_processed'):
            logger.info("Tokens already processed for this session")
            return PaymentStatusResponse(
                status="success",
                message="Payment already processed",
                tokens_purchased=0,
                product_name=""
            )
        
        # Add a flag to prevent reprocessing
        checkout_session._tokens_processed = True

        # Handle different payment types
        if checkout_session.mode == 'subscription':
            tokens_per_month = int(checkout_session.metadata.get('tokens_per_month', 0))
            if tokens_per_month <= 0:
                logger.error("Invalid tokens_per_month in subscription metadata")
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid subscription configuration"
                )

            try:
                # Update user's token balance with initial subscription grant
                user.tokens_purchased += tokens_per_month
                await db.commit()
                
                logger.info(f"Added {tokens_per_month} subscription tokens to user {user_id}")

                return PaymentStatusResponse(
                    status="success",
                    message="Subscription activated successfully",
                    tokens_purchased=tokens_per_month,
                    product_name=checkout_session.metadata.get('name', 'Subscription Plan')
                )

            except SQLAlchemyError as e:
                logger.error(f"Database error updating subscription tokens: {str(e)}")
                await db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update subscription tokens"
                )

        else:  # One-time payment
            tokens = int(checkout_session.metadata.get('tokens', 0))
            if tokens <= 0:
                logger.error("Invalid tokens amount in payment metadata")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid payment configuration"
                )

            try:
                # Update user's token balance for one-time purchase
                user.tokens_purchased += tokens
                await db.commit()
                
                logger.info(f"Added {tokens} one-time tokens to user {user_id}")

                return PaymentStatusResponse(
                    status="success",
                    message="Payment processed successfully",
                    tokens_purchased=tokens,
                    product_name=checkout_session.metadata.get('name', 'Token Package')
                )

            except SQLAlchemyError as e:
                logger.error(f"Database error updating one-time tokens: {str(e)}")
                await db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update token balance"
                )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in checkout success: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in checkout success: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred processing your payment"
        )

@router.post("/create-portal-session", response_model=CheckoutResponse)
async def create_portal_session(
    user = Depends(auth_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Create a Stripe Customer Portal session for subscription management"""
    try:
        # Get customer ID from Stripe metadata
        result = await db.execute(
            select(User).where(User.id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=db_user.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/billing",
        )

        return CheckoutResponse(checkout_url=session.url)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

@router.get("/cancel", response_model=PaymentStatusResponse)
async def checkout_cancel():
    """Handle checkout cancellation"""
    return PaymentStatusResponse(
        status="cancelled",
        message="Payment was cancelled",
        tokens_purchased=0,
        product_name=""
    )

@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """Handle Stripe webhook events"""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe signature header")

    try:
        # Read the raw body
        payload = await request.body()
        
        logger.info("Processing Stripe webhook")
        await stripe_service.handle_webhook(payload, stripe_signature)
        
        return WebhookResponse(status="success")
        
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid Stripe signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook-test", include_in_schema=False)
async def test_webhook(
    request: Request,
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Test endpoint for webhook handling (development only)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
        
    try:
        payload = await request.json()
        await stripe_service.handle_webhook(payload, "test-signature")
        return WebhookResponse(status="success")
    except Exception as e:
        logger.error(f"Error in test webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
