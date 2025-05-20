import os
import logging
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from app.core.config import settings
from dotenv import load_dotenv
import dkim  # You'll need to install the 'dkim' package

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = settings.SMTP_FROM_EMAIL
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        self.sender_name = settings.SMTP_FROM_NAME
        self.dkim_private_key_path = os.getenv('DKIM_PRIVATE_KEY_PATH')
        self.dkim_public_key_path = os.getenv('DKIM_PUBLIC_KEY_PATH')       

    def _sign_email_with_dkim(self, message: MIMEMultipart) -> bytes:
        """Sign the email with DKIM"""
        if not self.dkim_private_key_path:
            logger.warning("DKIM private key path not set")
            return None

        try:
            # Read the private key
            with open(self.dkim_private_key_path, 'rb') as key_file:
                private_key = key_file.read()

            # Prepare DKIM signing parameters
            dkim_options = {
                'domain': 'cyberiad.ai',
                'selector': 'selector',
                'privkey': private_key,
                'headers': ['From', 'To', 'Subject', 'Date', 'Message-ID']
            }

            # Convert message to string
            message_string = message.as_string().encode('utf-8')

            # Sign the message
            signature = dkim.sign(
                message_string, 
                **dkim_options
            )

            return signature
        except Exception as e:
            logger.error(f"DKIM signing failed: {str(e)}")
            return None

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        try:
            message = MIMEMultipart()
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # DKIM sign the message
            dkim_signature = self._sign_email_with_dkim(message)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                
                # If DKIM signature is available, add it to the message
                if dkim_signature:
                    message['DKIM-Signature'] = dkim_signature.decode('utf-8')
                
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    async def send_verification_email(self, email: str, token: str) -> bool:
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{token}"
        year = datetime.now().year
        
        html_content = VERIFICATION_EMAIL_TEMPLATE.format(
            verification_link=verification_link,
            year=year
        )
        
        return self._send_email(
            to_email=email,
            subject="Verify your Cyberiad account",
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
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{reset_token}"
        year = datetime.now().year
        
        html_content = PASSWORD_RESET_TEMPLATE.format(
            reset_link=reset_link,
            year=year
        )
        
        return self._send_email(
            to_email=email,
            subject="Reset your Cyberiad password",
            html_content=html_content
        )

# HTML Email Templates
VERIFICATION_EMAIL_TEMPLATE = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb;">Welcome to Cyberiad!</h1>
    </div>

    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <p>Thanks for signing up! To complete your registration and start using Cyberiad, please verify your email address:</p>

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
        <p style="color: #64748b; font-size: 14px;">Your account is initially credited with 50,000 tokens</p>
    </div>

    <div style="margin-top: 30px; font-size: 14px; color: #64748b; text-align: center;">
        <p>© {year} Cyberiad.ai - All rights reserved</p>
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
        <p><strong>{owner_name}</strong> has invited you to join a conversation on Cyberiad:</p>
        
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
        <p>© {year} Cyberiad.ai - All rights reserved</p>
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
        <p>You have requested to reset your Cyberiad password. Click the button below to set a new password:</p>

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
        <p>© {year} Cyberiad.ai - All rights reserved</p>
    </div>
</body>
</html>
"""

email_service = EmailService()
