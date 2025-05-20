# test_oauth_email.py

from gmail_setup import setup_gmail_oauth
from email_service import EmailService

def test_oauth_email():
    # Get credentials
    creds = setup_gmail_oauth()

    # Initialize email service
    email_service = EmailService(creds)

    # Send test email
    email_service.send_email(
        to_email="bartelby@gmail.com",  # Replace with your email
        subject="Test OAuth2.0 Email from Cyberiad",
        body="If you receive this, the OAuth2.0 setup is working!"
    )

if __name__ == "__main__":
    test_oauth_email()
