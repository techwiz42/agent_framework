import logging
from typing import Optional
from app.services.email_service import email_service
from app.models.domain.models import Thread, ThreadParticipant
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    async def send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification link."""
        try:
            return await email_service.send_verification_email(email, token)
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False

    async def send_thread_invitation(self, thread: Thread, participant: ThreadParticipant) -> bool:
        """Send an invitation email to a thread participant."""
        try:
            return await email_service.send_thread_invitation(
                thread_title=thread.title,
                thread_description=thread.description,
                owner_name=thread.owner.username,
                invitation_link=f"{settings.FRONTEND_URL}/join-conversation/{participant.invitation_token}",
                to_email=participant.email
            )
        except Exception as e:
            logger.error(f"Error sending thread invitation: {e}")
            return False

    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email."""
        try:
            return await email_service.send_password_reset_email(email, reset_token)
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False
