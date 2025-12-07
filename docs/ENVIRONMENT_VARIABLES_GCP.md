# Environment Variables Management in Google Cloud

## Overview

When deploying to Google Cloud, your `.env` file data is split into two places:

1. **Google Cloud Secret Manager** - For sensitive data (API keys, passwords, tokens)
2. **Cloud Run Environment Variables** - For non-sensitive configuration (URLs, feature flags, etc.)

## Where Your .env Variables Go

### 1. Secret Manager (Sensitive Data)

**Store these in Secret Manager:**
- API Keys (Gemini, Groq, OpenAI, etc.)
- Database passwords
- JWT secrets
- OAuth client secrets
- Service account keys
- Webhook secrets

### 2. Cloud Run Environment Variables (Non-Sensitive)

**Store these as environment variables:**
- Base URLs (can be updated later)
- Domain names (can be updated later)
- Feature flags
- Timeout values
- Rate limits
- Log levels
- CORS origins

## Initial Deployment (Without Domain)

### Step 1: Store Secrets in Secret Manager

#### Windows CMD (Command Prompt)

```cmd
REM Get your project ID first
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Sensitive API keys
echo your-gemini-api-key | gcloud secrets create gemini-api-key --data-file=- --project=%PROJECT_ID%
echo your-groq-api-key | gcloud secrets create groq-api-key --data-file=- --project=%PROJECT_ID%
echo your-openai-api-key | gcloud secrets create openai-api-key --data-file=- --project=%PROJECT_ID%

REM Database credentials
echo your-supabase-url | gcloud secrets create supabase-url --data-file=- --project=%PROJECT_ID%
echo your-supabase-anon-key | gcloud secrets create supabase-anon-key --data-file=- --project=%PROJECT_ID%
echo your-supabase-service-key | gcloud secrets create supabase-service-key --data-file=- --project=%PROJECT_ID%

REM JWT secret
echo your-jwt-secret | gcloud secrets create jwt-secret --data-file=- --project=%PROJECT_ID%

REM Other sensitive keys
echo your-paystack-secret-key | gcloud secrets create paystack-secret-key --data-file=- --project=%PROJECT_ID%
```

#### Linux/Mac (Bash)

```bash
# Sensitive API keys
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your-groq-api-key" | gcloud secrets create groq-api-key --data-file=-
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Database credentials
echo -n "your-supabase-url" | gcloud secrets create supabase-url --data-file=-
echo -n "your-supabase-anon-key" | gcloud secrets create supabase-anon-key --data-file=-
echo -n "your-supabase-service-key" | gcloud secrets create supabase-service-key --data-file=-

# JWT secret
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret --data-file=-

# Other sensitive keys
echo -n "your-paystack-secret-key" | gcloud secrets create paystack-secret-key --data-file=-
```

### Step 2: Deploy with Temporary URLs

#### Windows CMD (Command Prompt)

```cmd
REM Get your project ID first
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Get your Cloud Run URLs (these are temporary until you set up a domain)
for /f "tokens=*" %%i in ('gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)" --project=%PROJECT_ID%') do set BACKEND_URL=%%i
for /f "tokens=*" %%i in ('gcloud run services describe agent47-frontend --region us-central1 --format="value(status.url)" --project=%PROJECT_ID%') do set FRONTEND_URL=%%i

REM Deploy backend with temporary URLs
gcloud run deploy agent47-backend --image us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/backend:latest --region us-central1 --set-env-vars "ENVIRONMENT=production,DEBUG=false" --set-env-vars "BASE_URL=%BACKEND_URL%" --set-env-vars "API_BASE_URL=%BACKEND_URL%" --set-env-vars "ADMIN_BASE_URL=%BACKEND_URL%/admin" --set-env-vars "FRONTEND_URL=%FRONTEND_URL%" --set-env-vars "BACKEND_CORS_ORIGINS=[\"%FRONTEND_URL%\"]" --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_ANON_KEY=supabase-anon-key:latest,JWT_SECRET=jwt-secret:latest" --project=%PROJECT_ID%

REM Deploy frontend with temporary URLs
gcloud run deploy agent47-frontend --image us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/frontend:latest --region us-central1 --set-env-vars "NEXT_PUBLIC_API_URL=%BACKEND_URL%" --set-env-vars "NEXT_PUBLIC_SUPABASE_URL=your-supabase-url" --set-env-vars "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key" --project=%PROJECT_ID%
```

#### Linux/Mac (Bash)

```bash
# Get your Cloud Run URLs (these are temporary until you set up a domain)
BACKEND_URL=$(gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)")
FRONTEND_URL=$(gcloud run services describe agent47-frontend --region us-central1 --format="value(status.url)")

# Get your project ID first (replace with your actual project ID)
export PROJECT_ID=$(gcloud config get-value project)

# Deploy backend with temporary URLs
gcloud run deploy agent47-backend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest \
    --region us-central1 \
    --set-env-vars "ENVIRONMENT=production,DEBUG=false" \
    --set-env-vars "BASE_URL=${BACKEND_URL}" \
    --set-env-vars "API_BASE_URL=${BACKEND_URL}" \
    --set-env-vars "ADMIN_BASE_URL=${BACKEND_URL}/admin" \
    --set-env-vars "FRONTEND_URL=${FRONTEND_URL}" \
    --set-env-vars "BACKEND_CORS_ORIGINS=[\"${FRONTEND_URL}\"]" \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_ANON_KEY=supabase-anon-key:latest,JWT_SECRET=jwt-secret:latest"

# Deploy frontend with temporary URLs
gcloud run deploy agent47-frontend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/frontend:latest \
    --region us-central1 \
    --set-env-vars "NEXT_PUBLIC_API_URL=${BACKEND_URL}" \
    --set-env-vars "NEXT_PUBLIC_SUPABASE_URL=your-supabase-url" \
    --set-env-vars "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key"
```

## Updating Environment Variables Later

### Method 1: Update Cloud Run Service (Recommended)

```bash
# Update backend environment variables
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-env-vars "BASE_URL=https://yourdomain.com,API_BASE_URL=https://api.yourdomain.com,ADMIN_BASE_URL=https://admin.yourdomain.com" \
    --update-env-vars "BACKEND_CORS_ORIGINS=[\"https://yourdomain.com\",\"https://www.yourdomain.com\"]"

# Update frontend environment variables
gcloud run deploy agent47-frontend \
    --region us-central1 \
    --update-env-vars "NEXT_PUBLIC_API_URL=https://api.yourdomain.com"
```

### Method 2: Update via Google Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service (e.g., `agent47-backend`)
3. Click **"EDIT & DEPLOY NEW REVISION"**
4. Scroll to **"Variables & Secrets"**
5. Update environment variables
6. Click **"DEPLOY"**

### Method 3: Update Secrets

```bash
# Update an existing secret
echo -n "new-api-key-value" | gcloud secrets versions add gemini-api-key --data-file=-

# The service will automatically use the latest version
# Or force update by redeploying:
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

## Domain Setup Workflow

### Phase 1: Initial Deployment (No Domain)

```bash
# Use Cloud Run URLs temporarily
BASE_URL=https://agent47-backend-xxxxx.run.app
API_BASE_URL=https://agent47-backend-xxxxx.run.app
FRONTEND_URL=https://agent47-frontend-xxxxx.run.app
```

### Phase 2: After Getting Domain

1. **Map Domain to Cloud Run:**
```bash
# Map custom domain
gcloud run domain-mappings create \
    --service agent47-frontend \
    --domain yourdomain.com \
    --region us-central1

# Map API subdomain
gcloud run domain-mappings create \
    --service agent47-backend \
    --domain api.yourdomain.com \
    --region us-central1
```

2. **Update DNS Records:**
   - Add CNAME records as shown in Cloud Console
   - Wait for DNS propagation (can take up to 48 hours)

3. **Update Environment Variables:**
```bash
# Update backend
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-env-vars "BASE_URL=https://yourdomain.com,API_BASE_URL=https://api.yourdomain.com"

# Update frontend
gcloud run services update agent47-frontend \
    --region us-central1 \
    --update-env-vars "NEXT_PUBLIC_API_URL=https://api.yourdomain.com"
```

4. **Update Third-Party Services:**
   - Update callback URLs in:
     - Facebook Developer Console
     - Google Cloud Console (OAuth)
     - LinkedIn Developer Portal
     - Twitter Developer Portal
     - Slack App Settings
     - Stripe Dashboard
     - PayPal Developer Dashboard
     - And all other integrated services

## Complete Environment Variables List

### Secrets (Store in Secret Manager)

```bash
# Core Secrets
GEMINI_API_KEY
GROQ_API_KEY
OPENAI_API_KEY
JWT_SECRET
SECURITY_SECRET_KEY

# Database
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_DB_URL

# OAuth Secrets
FACEBOOK_APP_SECRET
GOOGLE_CLIENT_SECRET
LINKEDIN_CLIENT_SECRET
TWITTER_API_SECRET
INSTAGRAM_APP_SECRET

# Payment
PAYSTACK_SECRET_KEY
STRIPE_SECRET_KEY

# Webhook Secrets
WEBHOOK_SECRET_KEY
SLACK_SIGNING_SECRET
STRIPE_WEBHOOK_SECRET
PAYSTACK_WEBHOOK_SECRET

# Email
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
EMAIL_SMTP_PASSWORD

# Other API Keys
TWILIO_AUTH_TOKEN
SENDGRID_API_KEY
MAILCHIMP_API_KEY
```

### Environment Variables (Store in Cloud Run)

```bash
# URLs (Update these when you get a domain)
BASE_URL=https://yourdomain.com
API_BASE_URL=https://api.yourdomain.com
ADMIN_BASE_URL=https://admin.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# CORS
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Environment
ENVIRONMENT=production
DEBUG=false

# Feature Flags
IMAGE_GENERATION_ENABLED=true
VOICE_PROCESSING_ENABLED=true

# Timeouts
REQUEST_TIMEOUT=60
GEMINI_REQUEST_TIMEOUT=120

# Rate Limits
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
```

## Updating Callback URLs in Third-Party Services

When you update your domain, you need to update callback URLs in all integrated services:

### 1. Facebook
- Go to: https://developers.facebook.com/apps
- Settings > Basic > Add Platform > Website
- Site URL: `https://yourdomain.com`
- Valid OAuth Redirect URIs: `https://yourdomain.com/auth/facebook/callback`

### 2. Google Cloud Console
- Go to: https://console.cloud.google.com/apis/credentials
- Edit OAuth 2.0 Client
- Authorized redirect URIs: `https://yourdomain.com/auth/google/callback`

### 3. LinkedIn
- Go to: https://www.linkedin.com/developers/apps
- Auth tab > Redirect URLs
- Add: `https://yourdomain.com/auth/linkedin/callback`

### 4. Twitter
- Go to: https://developer.twitter.com/en/portal/dashboard
- App Settings > User authentication settings
- Callback URI: `https://yourdomain.com/auth/twitter/callback`

### 5. Slack
- Go to: https://api.slack.com/apps
- OAuth & Permissions > Redirect URLs
- Add: `https://yourdomain.com/auth/slack/callback`

### 6. Stripe
- Go to: https://dashboard.stripe.com/webhooks
- Add endpoint: `https://api.yourdomain.com/webhooks/stripe`

### 7. PayPal
- Go to: https://developer.paypal.com/dashboard/applications
- Webhooks: `https://api.yourdomain.com/webhooks/paypal`

## Quick Update Script

Create a script to update all environment variables at once:

```bash
#!/bin/bash
# update-env-vars.sh

DOMAIN="yourdomain.com"
BACKEND_SERVICE="agent47-backend"
FRONTEND_SERVICE="agent47-frontend"
REGION="us-central1"

# Update backend
gcloud run services update ${BACKEND_SERVICE} \
    --region ${REGION} \
    --update-env-vars "BASE_URL=https://${DOMAIN},API_BASE_URL=https://api.${DOMAIN},ADMIN_BASE_URL=https://admin.${DOMAIN}" \
    --update-env-vars "BACKEND_CORS_ORIGINS=[\"https://${DOMAIN}\",\"https://www.${DOMAIN}\"]" \
    --update-env-vars "FRONTEND_URL=https://${DOMAIN}"

# Update frontend
gcloud run services update ${FRONTEND_SERVICE} \
    --region ${REGION} \
    --update-env-vars "NEXT_PUBLIC_API_URL=https://api.${DOMAIN}"

echo "Environment variables updated for ${DOMAIN}"
```

## Best Practices

### 1. Use Secret Manager for All Secrets
- Never put API keys or passwords in environment variables
- Always use Secret Manager for sensitive data

### 2. Version Your Secrets
- Secret Manager automatically versions secrets
- Use `:latest` to always get the newest version
- Or pin to specific version: `secret-name:1`

### 3. Update URLs Gradually
- Start with Cloud Run URLs
- Update to custom domain when ready
- Test each service after updating URLs

### 4. Document Your Variables
- Keep a list of all environment variables
- Document which services need callback URL updates
- Track when you update each variable

### 5. Test After Updates
- Always test after updating environment variables
- Check logs for any errors
- Verify third-party integrations still work

## Troubleshooting

### Issue: Environment variables not updating
```bash
# Force a new revision
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-env-vars "FORCE_RELOAD=$(date +%s)"
```

### Issue: Secrets not accessible
```bash
# Get your project ID
export PROJECT_ID=$(gcloud config get-value project)

# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:agent47-run@*"

# Grant secret accessor role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:agent47-run@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Issue: CORS errors after domain update
```bash
# Update CORS origins
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-env-vars "BACKEND_CORS_ORIGINS=[\"https://yourdomain.com\",\"https://www.yourdomain.com\",\"https://api.yourdomain.com\"]"
```

## Summary

1. **Initial Deployment**: Use Cloud Run URLs, store secrets in Secret Manager
2. **After Getting Domain**: Map domain, update environment variables, update third-party callbacks
3. **Ongoing Updates**: Use `gcloud run services update` or Cloud Console
4. **Secrets**: Always update via Secret Manager, never in environment variables

Your `.env` file data is safely stored and easily updatable in Google Cloud! 🚀

