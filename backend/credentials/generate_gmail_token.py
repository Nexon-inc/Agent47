import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_token():
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('gmail_token.json'):
        creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('gmail_token.json', 'w') as token:
            token.write(creds.to_json())
    
    print("✅ Token generated successfully!")
    print(f"📧 Access Token: {creds.token}")
    print(f"🔄 Refresh Token: {creds.refresh_token}")
    print(f"📁 Token saved to: gmail_token.json")

if __name__ == '__main__':
    generate_token()