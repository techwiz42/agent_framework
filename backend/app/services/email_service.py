"""
Simplified version of email_service.py from Cyberiad.
This stub implementation maintains the same interface but logs emails instead of sending them.
"""
import logging
from datetime import datetime
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sender_email = settings.SMTP_FROM_EMAIL if hasattr(settings, 'SMTP_FROM_EMAIL') else "noreply@example.com"
        self.sender_name = settings.SMTP_FROM_NAME if hasattr(settings, 'SMTP_FROM_NAME') else "Agent Framework"
        self.frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000"

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Stub implementation that logs the email instead of sending it.
        """
        try:
            message = MIMEMultipart()
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Log the email information instead of sending
            logger.info(f"=== EMAIL WOULD BE SENT ===")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"From: {self.sender_name} <{self.sender_email}>")
            logger.info(f"Content length: {len(html_content)} characters")
            logger.info(f"=== END EMAIL ===")
            
            return True

        except Exception as e:
            logger.error(f"Failed to process email: {str(e)}")
            return False

    async def send_verification_email(self, email: str, token: str) -> bool:
        verification_link = f"{self.frontend_url}/verify-email/{token}"
        year = datetime.now().year
        
        html_content = VERIFICATION_EMAIL_TEMPLATE.format(
            verification_link=verification_link,
            year=year
        )
        
        return self._send_email(
            to_email=email,
            subject="Verify your account",
            html_content=html_content
        )

    async def send_thread_invitation(self, thread_title: str, thread_description: str, 
                                   owner_name: str, invitation_link: str, to_email: str) -> bool:
        year = datetime.now().year
        
        html_content = THREAD_INVITATION_TEMPLATE.format(
            thread_title=thread_title,
            thread_description=thread_description or "No description provided",
            owner_name=owner_name,
            invitation_link=invitation_link,
            year=year
        )
        
        return self._send_email(
            to_email=to_email,
            subject=f"You're invited to join a conversation: {thread_title}",
            html_content=html_content
        )

    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        reset_link = f"{self.frontend_url}/reset-password/{reset_token}"
        year = datetime.now().year
        
        html_content = PASSWORD_RESET_TEMPLATE.format(
            reset_link=reset_link,
            year=year
        )
        
        return self._send_email(
            to_email=email,
            subject="Reset your password",
            html_content=html_content
        )

# Simplified HTML Email Templates
VERIFICATION_EMAIL_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Welcome!</h1>
    </div>

    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <p>Thanks for signing up! To complete your registration, please verify your email address:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_link}"
               style="background-color: #4CAF50;
                      color: white;
                      padding: 12px 25px;
                      text-decoration: none;
                      border-radius: 5px;
                      display: inline-block;
                      font-weight: bold;">
                Verify Email Address
            </a>
        </div>

        <p style="color: #64748b; font-size: 14px;">This link will expire in 24 hours.</p>
    </div>

    <div style="margin-top: 30px; font-size: 14px; color: #64748b; text-align: center;">
        <p>© {year} All rights reserved</p>
    </div>
</body>
</html>
"""

THREAD_INVITATION_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">You've Been Invited!</h1>
    </div>

    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <p><strong>{owner_name}</strong> has invited you to join a conversation:</p>
        
        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h2 style="color: #1a365d; margin: 0 0 10px 0;">{thread_title}</h2>
            <p style="color: #4a5568; margin: 0;">{thread_description}</p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{invitation_link}"
               style="background-color: #4CAF50;
                      color: white;
                      padding: 12px 25px;
                      text-decoration: none;
                      border-radius: 5px;
                      display: inline-block;
                      font-weight: bold;">
                Join Conversation
            </a>
        </div>
    </div>

    <div style="margin-top: 30px; font-size: 14px; color: #64748b; text-align: center;">
        <p>© {year} All rights reserved</p>
    </div>
</body>
</html>
"""

PASSWORD_RESET_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Reset Your Password</h1>
    </div>

    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <p>You have requested to reset your password. Click the button below to set a new password:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}"
               style="background-color: #4CAF50;
                      color: white;
                      padding: 12px 25px;
                      text-decoration: none;
                      border-radius: 5px;
                      display: inline-block;
                      font-weight: bold;">
                Reset Password
            </a>
        </div>

        <p style="color: #64748b; font-size: 14px;">This link will expire in 1 hour. If you didn't request this reset, please ignore this email.</p>
    </div>

    <div style="margin-top: 30px; font-size: 14px; color: #64748b; text-align: center;">
        <p>© {year} All rights reserved</p>
    </div>
</body>
</html>
"""

email_service = EmailService()