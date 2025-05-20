# gmail_setup.py

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pathlib import Path

def setup_gmail_oauth():
    """Set up Gmail OAuth2.0 credentials"""
    creds = None
    token_path = Path('token.pickle')
    
    # Load existing token if it exists
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let's get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load client secrets from downloaded JSON
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json',  # Your downloaded OAuth2.0 JSON
                ['https://mail.google.com/']
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

