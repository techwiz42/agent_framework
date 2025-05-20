import json
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
import sys

def setup_gmail_oauth():
    secret_path = Path('client_secret.json')
    print(f"Looking for file at: {secret_path.absolute()}")
    
    # First verify we can read the file
    try:
        with open(secret_path) as f:
            secret_data = json.load(f)
            print("Successfully loaded JSON data")
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            ['https://mail.google.com/']
        )
        print("Created flow object")
        
        creds = flow.run_local_server()
        print("Got credentials")
        
        # Save the credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("Saved credentials")
        
        return creds
        
    except Exception as e:
        print(f"Error in OAuth flow: {e}")
        print(f"Type of error: {type(e)}")
        return None

if __name__ == "__main__":
    try:
        creds = setup_gmail_oauth()
        if creds:
            print("Success!")
        else:
            print("Failed to get credentials")
    except Exception as e:
        print(f"Top level error: {e}")
    
    input("Press Enter to exit...")
