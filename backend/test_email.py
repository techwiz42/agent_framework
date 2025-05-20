from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_email():
    # Get settings from environment variables
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_from = os.getenv('SMTP_FROM_EMAIL')

    print(f"Using SMTP settings:")
    print(f"Host: {smtp_host}")
    print(f"Port: {smtp_port}")
    print(f"User: {smtp_user}")
    print(f"From: {smtp_from}")

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = 'your-test-email@example.com'  # Replace with your email
    msg['Subject'] = 'Test Email from Cyberiad'
    
    body = 'If you receive this, the SMTP setup is working!'
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_email()
