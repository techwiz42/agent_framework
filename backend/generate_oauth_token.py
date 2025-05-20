from google_auth_oauthlib.flow import Flow
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_token():
    # Path to your OAuth 2.0 client configuration file
    client_secrets_file = '/etc/cyberiad/credentials.json'
    
    # Create the flow using the client secrets file
    flow = Flow.from_client_secrets_file(
        client_secrets_file, 
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Console-based flow
    )
    
    # Generate the authorization URL
    authorization_url, _ = flow.authorization_url(
        prompt='consent',  # Force showing consent screen
        access_type='offline'  # Request a refresh token
    )
    
    print("Please go to this URL and authorize the application:")
    print(authorization_url)
    
    # Manual input of authorization code
    authorization_code = input("Enter the authorization code: ")
    
    # Exchange the authorization code for credentials
    flow.fetch_token(code=authorization_code)
    credentials = flow.credentials
    
    # Save the credentials
    with open('/etc/cyberiad/token.pickle', 'wb') as token:
        pickle.dump(credentials, token)
    
    print("Token generated and saved successfully!")

if __name__ == '__main__':
    generate_token()
