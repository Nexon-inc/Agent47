# Gmail API Setup Guide for Agent47

This guide will help you set up Gmail API integration for email verification in Agent47, replacing Supabase email verification.

## Prerequisites

- Google Cloud Platform account
- Gmail account for sending emails
- Python 3.8+ installed
- Agent47 backend running

## Step 1: Google Cloud Project Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `Agent47-Gmail-API`
4. Click "Create"

### 1.2 Enable Gmail API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" and click "Enable"

### 1.3 Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields:
     - App name: `Agent47`
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes: `https://www.googleapis.com/auth/gmail.send`
   - Add test users: Your Gmail address
4. Choose "Desktop application" as application type
5. Name it: `Agent47 Gmail Client`
6. Click "Create"
7. Download the JSON file and save it as `credentials/gmail_credentials.json`

## Step 2: OAuth2 Token Generation

### 2.1 Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2.2 Generate Initial Token

Create a script to generate the initial OAuth2 token:

```python
# generate_gmail_token.py
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_token():
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('credentials/gmail_token.json'):
        creds = Credentials.from_authorized_user_file('credentials/gmail_token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('credentials/gmail_token.json', 'w') as token:
            token.write(creds.to_json())
    
    print("Token generated successfully!")
    print(f"Access Token: {creds.token}")
    print(f"Refresh Token: {creds.refresh_token}")

if __name__ == '__main__':
    generate_token()
```

Run the script:

```bash
python generate_gmail_token.py
```

This will:
1. Open a browser window for OAuth2 authentication
2. Ask you to sign in to your Google account
3. Request permission to send emails on your behalf
4. Generate and save the tokens

## Step 3: Environment Configuration

### 3.1 Update .env File

Add the following to your `.env` file:

```env
# Gmail API Configuration
GMAIL_CLIENT_ID=your-client-id-from-credentials-file
GMAIL_CLIENT_SECRET=your-client-secret-from-credentials-file
GMAIL_REFRESH_TOKEN=your-refresh-token-from-token-generation
GMAIL_ACCESS_TOKEN=your-access-token-from-token-generation
GMAIL_CREDENTIALS_FILE=./credentials/gmail_credentials.json
GMAIL_TOKEN_FILE=./credentials/gmail_token.json
GMAIL_FROM_EMAIL=your-gmail-address@gmail.com
GMAIL_FROM_NAME=Agent47 Support
GMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS=24
```

### 3.2 Create Credentials Directory

```bash
mkdir -p credentials
```

Move your downloaded credentials file:

```bash
mv ~/Downloads/your-credentials-file.json credentials/gmail_credentials.json
```

## Step 4: Database Migration

### 4.1 Run Database Migration

```bash
cd backend
python migrations/add_email_verification_tokens.py
```

This will create the `email_verification_tokens` table in your database.

## Step 5: Supabase Configuration

### 5.1 Disable Supabase Email Confirmation

1. Go to your Supabase project dashboard
2. Navigate to "Authentication" → "Settings"
3. Under "Email Confirmation", turn OFF "Enable email confirmations"
4. Save changes

This prevents Supabase from sending its own verification emails.

## Step 6: Testing

### 6.1 Run Gmail Tests

```bash
cd tests
python run_gmail_tests.py
```

### 6.2 Test Email Verification Flow

1. Start your backend server
2. Try signing up a new user
3. Check that verification email is sent via Gmail
4. Click the verification link
5. Verify the user is marked as verified

## Step 7: Production Deployment

### 7.1 Update OAuth Consent Screen

For production:

1. Go to "APIs & Services" → "OAuth consent screen"
2. Change from "Testing" to "Production"
3. Add your domain to authorized domains
4. Submit for verification if needed

### 7.2 Environment Variables

Update your production environment with:

```env
GMAIL_CLIENT_ID=your-production-client-id
GMAIL_CLIENT_SECRET=your-production-client-secret
GMAIL_REFRESH_TOKEN=your-production-refresh-token
GMAIL_ACCESS_TOKEN=your-production-access-token
GMAIL_FROM_EMAIL=your-production-gmail@gmail.com
GMAIL_FROM_NAME=Your Company Name
```

## Troubleshooting

### Common Issues

1. **"Access blocked" error**
   - Make sure your Gmail account is added as a test user
   - Check OAuth consent screen configuration

2. **"Invalid credentials" error**
   - Regenerate the OAuth2 token
   - Check that credentials file path is correct

3. **"Quota exceeded" error**
   - Gmail API has daily limits
   - Consider implementing rate limiting

4. **"Permission denied" error**
   - Check that Gmail API is enabled
   - Verify OAuth2 scopes include `gmail.send`

### Debug Mode

Enable debug logging by setting:

```env
LOG_LEVEL=DEBUG
```

### Token Refresh

Tokens automatically refresh, but if you encounter issues:

1. Delete `credentials/gmail_token.json`
2. Run the token generation script again
3. Update your `.env` file with new tokens

## Security Considerations

1. **Never commit credentials to version control**
2. **Use environment variables for production**
3. **Regularly rotate OAuth2 tokens**
4. **Monitor API usage and quotas**
5. **Implement rate limiting**

## API Limits

- Gmail API: 1 billion quota units per day
- Sending emails: 100 quota units per email
- Daily limit: ~10 million emails per day

## Support

If you encounter issues:

1. Check the logs in `backend/logs/agent47.log`
2. Verify all environment variables are set
3. Test Gmail API connectivity
4. Check database migration status

## Next Steps

After successful setup:

1. Test the complete signup flow
2. Monitor email delivery rates
3. Set up email templates customization
4. Implement email analytics
5. Configure backup email providers if needed
