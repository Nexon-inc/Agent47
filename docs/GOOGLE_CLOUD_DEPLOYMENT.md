# Google Cloud Deployment Guide for Agent47

This guide will walk you through deploying Agent47 to Google Cloud Platform (GCP).

**Important**: This guide uses your existing Google Cloud project "Agent47 Backend". 

**Current Status**: Your project already has:
- ✅ Gemini API enabled
- ✅ Billing set up

**What You Need to Set Up** (everything else):
- Cloud Run API
- Secret Manager API
- Artifact Registry API
- Cloud Build API
- Service accounts
- Secrets storage
- Docker image deployment

The project ID will be automatically detected, or you can set it manually.

## Quick Start

### Windows CMD (Command Prompt)

```cmd
REM 1. Set your project ID (replace with your actual project ID)
set PROJECT_ID=agent47-backend
gcloud config set project %PROJECT_ID%

REM 2. Enable required APIs (these are NOT set up yet - only Gemini API is enabled)
gcloud services enable run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage-component.googleapis.com --project=%PROJECT_ID%

REM 3. Continue with Step 1 below for full setup
```

### Linux/Mac (Bash)

```bash
# 1. Get your project ID
export PROJECT_ID=$(gcloud projects list --filter="name:Agent47 Backend" --format="value(projectId)" | head -1)
gcloud config set project $PROJECT_ID

# 2. Enable required APIs (these are NOT set up yet - only Gemini API is enabled)
gcloud services enable run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage-component.googleapis.com --project=$PROJECT_ID

# 3. Continue with Step 1 below for full setup
```

## Prerequisites

1. **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK**: Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install [Docker](https://www.docker.com/get-started)
4. **Domain Name** (optional): For custom domain setup

## Architecture Overview

We'll deploy:
- **Backend API**: Cloud Run (serverless, auto-scaling)
- **Frontend**: Cloud Run or Cloud Storage + Cloud CDN
- **Database**: Cloud SQL (PostgreSQL) or Supabase (managed)
- **Storage**: Cloud Storage or Supabase Storage
- **Redis**: Memorystore (managed Redis)
- **Secrets**: Secret Manager

## Step 1: Initial Setup

### 1.1 Use Your Existing GCP Project

```bash
# Login to GCP
gcloud auth login

# Get your existing project ID (replace with your actual project ID if different)
# Option 1: List your projects to find the ID
gcloud projects list

# Option 2: If you know the display name is "Agent47 Backend", get the project ID
gcloud projects list --filter="name:Agent47 Backend" --format="value(projectId)"

# Set your project ID as a variable (replace with your actual project ID)
export PROJECT_ID=$(gcloud projects list --filter="name:Agent47 Backend" --format="value(projectId)" | head -1)

# Or set it manually if you know the project ID
# export PROJECT_ID="your-actual-project-id"

# Set as active project
gcloud config set project $PROJECT_ID

# Verify you're using the correct project
gcloud config get-value project

# Enable billing (required for Cloud Run) - if not already enabled
# Go to: https://console.cloud.google.com/billing
```

### 1.2 Enable Required APIs

**Note**: Your project already has Gemini API enabled and billing set up. You need to enable the following APIs:

```bash
# Get your project ID first (if not already set)
export PROJECT_ID=$(gcloud config get-value project)

# Enable Cloud Run API (required for deploying services)
gcloud services enable run.googleapis.com --project=$PROJECT_ID

# Enable Secret Manager API (required for storing secrets)
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

# Enable Cloud Storage API (required for file storage)
gcloud services enable storage-component.googleapis.com --project=$PROJECT_ID

# Enable Artifact Registry API (required for Docker images)
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID

# Enable Cloud Build API (required for building Docker images)
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID

# Enable Cloud SQL API (optional - only if using Cloud SQL instead of Supabase)
# gcloud services enable sqladmin.googleapis.com --project=$PROJECT_ID

# Note: Gemini API is already enabled in your project, so we skip that

# Verify APIs are enabled
gcloud services list --enabled --project=$PROJECT_ID
```

### 1.3 Set Up Authentication

```bash
# Get your project ID first (if not already set)
export PROJECT_ID=$(gcloud config get-value project)

# Create service account for Cloud Run (if it doesn't exist)
# Check if service account already exists
if ! gcloud iam service-accounts describe agent47-run@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID 2>/dev/null; then
    echo "Creating service account..."
    gcloud iam service-accounts create agent47-run \
        --display-name="Agent47 Cloud Run Service Account" \
        --project=$PROJECT_ID
else
    echo "Service account 'agent47-run' already exists, skipping creation."
fi

# Grant necessary permissions
echo "Granting permissions to service account..."

# Grant Secret Manager access (for reading API keys and secrets)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:agent47-run@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant Storage access (for file uploads/downloads)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:agent47-run@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Grant Cloud Run Invoker (for service-to-service communication)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:agent47-run@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

echo "Service account setup complete!"
```

## Step 2: Database Setup

### Option A: Cloud SQL (PostgreSQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create agent47-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create agent47 --instance=agent47-db

# Get connection name
gcloud sql instances describe agent47-db --format="value(connectionName)"
# Save this for later: $PROJECT_ID:us-central1:agent47-db
```

### Option B: Supabase (Recommended - Already Using)

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Get your connection details from Project Settings > Database
4. Save:
   - Database URL
   - Anon Key
   - Service Role Key

## Step 3: Redis Setup (Memorystore)

```bash
# Create Redis instance
gcloud redis instances create agent47-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0 \
    --tier=basic

# Get Redis IP
gcloud redis instances describe agent47-redis --region=us-central1 --format="value(host)"
```

## Step 4: Storage Setup

### Option A: Cloud Storage

```bash
# Create bucket (using your project ID)
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://agent47-storage

# Make bucket public for images (or use signed URLs)
gsutil iam ch allUsers:objectViewer gs://agent47-storage
```

### Option B: Supabase Storage (Recommended - Already Using)

Use your existing Supabase Storage bucket.

## Step 5: Store Secrets

**Important**: Replace all placeholder values with your actual credentials from your `.env` file.

```bash
# Get your project ID first (if not already set)
export PROJECT_ID=$(gcloud config get-value project)

# Store Supabase URL (replace with your actual Supabase URL from .env)
echo -n "https://your-project.supabase.co" | \
    gcloud secrets create supabase-url --data-file=- --project=$PROJECT_ID

# Store Supabase Anon Key (replace with your actual key from .env)
echo -n "your-anon-key" | \
    gcloud secrets create supabase-anon-key --data-file=- --project=$PROJECT_ID

# Store Supabase Service Role Key (replace with your actual key from .env)
echo -n "your-service-role-key" | \
    gcloud secrets create supabase-service-key --data-file=- --project=$PROJECT_ID

# Store JWT Secret (replace with a strong random secret from .env)
echo -n "your-jwt-secret-key" | \
    gcloud secrets create jwt-secret --data-file=- --project=$PROJECT_ID

# Store Google Gemini API Key (get this from your .env file - you already have Gemini API enabled)
echo -n "your-gemini-api-key" | \
    gcloud secrets create gemini-api-key --data-file=- --project=$PROJECT_ID

# Store other API keys as needed (replace with your actual keys from .env)
echo -n "your-groq-api-key" | \
    gcloud secrets create groq-api-key --data-file=- --project=$PROJECT_ID

echo -n "your-openai-api-key" | \
    gcloud secrets create openai-api-key --data-file=- --project=$PROJECT_ID

# Optional: Store database URL if using Cloud SQL instead of Supabase
# echo -n "postgresql://user:pass@host:5432/dbname" | \
#     gcloud secrets create database-url --data-file=- --project=$PROJECT_ID

# Verify secrets were created
gcloud secrets list --project=$PROJECT_ID
```

## Step 6: Build and Deploy Backend

### 6.1 Create Artifact Registry

```bash
# Get your project ID first (if not already set)
export PROJECT_ID=$(gcloud config get-value project)

# Create repository (if it doesn't exist)
# Check if repository exists first
if ! gcloud artifacts repositories describe agent47-repo --location=us-central1 --project=$PROJECT_ID 2>/dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create agent47-repo \
        --repository-format=docker \
        --location=us-central1 \
        --description="Agent47 Docker images" \
        --project=$PROJECT_ID
else
    echo "Repository 'agent47-repo' already exists, skipping creation."
fi
```

### 6.2 Build Docker Image

**Option A: Build from GitHub (Recommended - Since you've uploaded to GitHub)**

#### Windows CMD (Command Prompt)

```cmd
REM Get your project ID first
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Build from GitHub repository
REM Replace YOUR_USERNAME with your GitHub username
REM Replace Agent47 with your repository name if different
gcloud builds submit --config=infrastructure/cloudbuild.yaml --project=%PROJECT_ID% https://github.com/YOUR_USERNAME/Agent47.git

REM Or build just the backend from GitHub
gcloud builds submit --tag us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/backend:latest --substitutions=_BUILD_CONTEXT=backend https://github.com/YOUR_USERNAME/Agent47.git
```

#### Linux/Mac (Bash)

```bash
# Get your project ID first
export PROJECT_ID=$(gcloud config get-value project)

# Build from GitHub repository
# Replace YOUR_USERNAME with your GitHub username
# Replace Agent47 with your repository name if different
gcloud builds submit --config=infrastructure/cloudbuild.yaml --project=$PROJECT_ID https://github.com/YOUR_USERNAME/Agent47.git

# Or build just the backend from GitHub
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest --substitutions=_BUILD_CONTEXT=backend https://github.com/YOUR_USERNAME/Agent47.git
```

**Option B: Build from Local Directory**

#### Windows CMD (Command Prompt)

```cmd
REM Get your project ID first
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Navigate to project root (where backend folder is located)
cd C:\Users\John Kyalo\Desktop\Agent47

REM Build and push image using Cloud Build (recommended)
REM This will build the Docker image in the cloud
gcloud builds submit --tag us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/backend:latest ./backend --project=%PROJECT_ID%
```

#### Linux/Mac (Bash)

```bash
# Get your project ID first
export PROJECT_ID=$(gcloud config get-value project)

# Navigate to project root (where backend folder is located)
cd /path/to/Agent47

# Build and push image using Cloud Build (recommended)
# This will build the Docker image in the cloud
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest ./backend --project=$PROJECT_ID

# Alternative: Build locally and push (requires Docker Desktop)
# First, authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev --project=$PROJECT_ID

# Then build and push
cd backend
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest .
docker push us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest
```

### 6.3 Deploy to Cloud Run

```bash
# Deploy backend (using your project ID)
gcloud run deploy agent47-backend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account agent47-run@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars "ENVIRONMENT=production" \
    --set-secrets "DATABASE_URL=database-url:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_ANON_KEY=supabase-anon-key:latest,JWT_SECRET=jwt-secret:latest,GEMINI_API_KEY=gemini-api-key:latest" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1

# Get backend URL
gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)"
# Save this URL: https://agent47-backend-xxxxx.run.app
```

## Step 7: Deploy Frontend

### Option A: Cloud Run (Recommended)

```bash
# Navigate to frontend directory
cd frontend

# Build and push frontend image (using your project ID)
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/frontend:latest

# Deploy frontend
gcloud run deploy agent47-frontend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "NEXT_PUBLIC_API_URL=https://agent47-backend-xxxxx.run.app,NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co,NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 5

# Get frontend URL
gcloud run services describe agent47-frontend --region us-central1 --format="value(status.url)"
```

### Option B: Cloud Storage + Cloud CDN (Static Site)

```bash
# Build Next.js static export
cd frontend
npm run build
npm run export  # If configured for static export

# Upload to Cloud Storage
gsutil -m rsync -r out/ gs://agent47-frontend/

# Enable website hosting
gsutil web set -m index.html -e 404.html gs://agent47-frontend

# Set up Cloud CDN (optional)
# Create load balancer with Cloud CDN backend pointing to bucket
```

## Step 8: Environment Variables

**Important**: Your `.env` file data is split into:
- **Secret Manager**: For sensitive data (API keys, passwords, tokens)
- **Cloud Run Environment Variables**: For non-sensitive config (URLs, feature flags)

**See `docs/ENVIRONMENT_VARIABLES_GCP.md` for complete guide on managing environment variables.**

### Quick Setup (Without Domain Yet)

You can deploy without a domain first, then update URLs later:

Update your `.env` file or Cloud Run environment variables:

```bash
# Backend Environment Variables
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
JWT_SECRET=your-jwt-secret
REDIS_URL=redis://your-redis-ip:6379

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_PRO_IMAGE_MODEL=gemini-1.5-pro-latest
GEMINI_FLASH_IMAGE_MODEL=gemini-1.5-flash-latest

# Other AI Services
GROQ_API_KEY=your-groq-key
OPENAI_API_KEY=your-openai-key

# CORS (Update with your actual Cloud Run URL first, then domain later)
BACKEND_CORS_ORIGINS=https://agent47-frontend-xxxxx.run.app
# After getting domain, update to: https://yourdomain.com,https://www.yourdomain.com

# Frontend Environment Variables
NEXT_PUBLIC_API_URL=https://agent47-backend-xxxxx.run.app
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Step 9: Updating Environment Variables After Getting Domain

**See `docs/ENVIRONMENT_VARIABLES_GCP.md` for detailed instructions.**

Quick update commands:
```bash
# Update backend URLs
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-env-vars "BASE_URL=https://yourdomain.com,API_BASE_URL=https://api.yourdomain.com"

# Update frontend URLs
gcloud run services update agent47-frontend \
    --region us-central1 \
    --update-env-vars "NEXT_PUBLIC_API_URL=https://api.yourdomain.com"
```

## Step 10: Custom Domain (Optional)

### 9.1 Map Custom Domain to Cloud Run

```bash
# Add domain mapping
gcloud run domain-mappings create \
    --service agent47-frontend \
    --domain yourdomain.com \
    --region us-central1

# Follow instructions to verify domain ownership
# Add DNS records as shown in the output
```

### 9.2 SSL Certificate

Cloud Run automatically provisions SSL certificates for custom domains.

## Step 11: Monitoring and Logging

### 10.1 Enable Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Set up log-based alerts
# Go to: https://console.cloud.google.com/logs/alerting
```

### 10.2 Set Up Monitoring

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
# Go to: https://console.cloud.google.com/monitoring/uptime
```

## Step 12: CI/CD Setup (Optional)

### 11.1 Create Cloud Build Trigger

```bash
# Create trigger for GitHub
gcloud builds triggers create github \
    --name="agent47-deploy" \
    --repo-name="your-repo" \
    --repo-owner="your-username" \
    --branch-pattern="^main$" \
    --build-config="infrastructure/cloudbuild.yaml"
```

### 12.2 cloudbuild.yaml Location

The `cloudbuild.yaml` file is located in the `infrastructure/` folder. This file:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:$SHORT_SHA', './backend']
  
  # Push backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:$SHORT_SHA']
  
  # Deploy backend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'agent47-backend'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-central1-docker.pkg.dev/${PROJECT_ID}/agent47-repo/frontend:$SHORT_SHA', './frontend']
  
  # Push frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/${PROJECT_ID}/agent47-repo/frontend:$SHORT_SHA']
  
  # Deploy frontend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'agent47-frontend'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/frontend:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
```

## Step 13: Cost Optimization

### 12.1 Set Up Budget Alerts

```bash
# Create budget
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT_ID \
    --display-name="Agent47 Budget" \
    --budget-amount=100USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

### 12.2 Optimize Resources

- Use Cloud Run min-instances=0 for development
- Use appropriate instance sizes
- Enable Cloud CDN for static assets
- Use Cloud SQL read replicas if needed

## Step 14: Security

### 13.1 Enable IAM

```bash
# Restrict Cloud Run access
gcloud run services update agent47-backend \
    --region us-central1 \
    --no-allow-unauthenticated

# Create authorized service account
gcloud run services add-iam-policy-binding agent47-backend \
    --member="serviceAccount:agent47-frontend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region us-central1
```

### 13.2 Set Up VPC (Optional)

For private networking between services.

## Step 15: Testing

### 14.1 Test Backend

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)")

# Test health endpoint
curl $BACKEND_URL/health

# Test API
curl $BACKEND_URL/api/v1/auth/login \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123"}'
```

### 14.2 Test Frontend

```bash
# Get frontend URL
FRONTEND_URL=$(gcloud run services describe agent47-frontend --region us-central1 --format="value(status.url)")

# Open in browser
open $FRONTEND_URL
```

## Step 16: Post-Deployment

### 15.1 Run Database Migrations

```bash
# Connect to Cloud Run instance
gcloud run services update agent47-backend \
    --region us-central1 \
    --update-env-vars "RUN_MIGRATIONS=true"

# Or run migrations manually
gcloud run jobs create agent47-migrations \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/agent47-repo/backend:latest \
    --region us-central1 \
    --set-env-vars "ENVIRONMENT=production" \
    --set-secrets "DATABASE_URL=database-url:latest"

gcloud run jobs execute agent47-migrations --region us-central1
```

### 15.2 Verify Services

1. Check backend health: `https://agent47-backend-xxxxx.run.app/health`
2. Check frontend: `https://agent47-frontend-xxxxx.run.app`
3. Test image generation
4. Test admin panel
5. Test team chat

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Update `BACKEND_CORS_ORIGINS` with frontend URL
   - Check Cloud Run CORS settings

2. **Database Connection Issues**
   - Verify Cloud SQL connection name
   - Check firewall rules
   - Verify credentials in Secret Manager

3. **Secret Access Issues**
   - Verify service account has `secretAccessor` role
   - Check secret names match exactly

4. **Image Generation Fails**
   - Verify Gemini API key in Secret Manager
   - Check API quotas and limits
   - Review logs: `gcloud logging read "resource.type=cloud_run_revision"`

### View Logs

```bash
# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent47-backend" --limit 50

# Frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent47-frontend" --limit 50
```

## Cost Estimation

**Monthly Estimate (Low Traffic):**
- Cloud Run: ~$20-50 (depending on traffic)
- Cloud SQL: ~$10-30 (db-f1-micro)
- Memorystore: ~$30-50 (1GB)
- Cloud Storage: ~$1-5
- **Total: ~$60-135/month**

**Scaling:**
- Cloud Run auto-scales based on traffic
- Consider Cloud SQL read replicas for high traffic
- Use Cloud CDN for static assets

## Next Steps

1. Set up monitoring alerts
2. Configure backup strategy
3. Set up staging environment
4. Implement CI/CD pipeline
5. Set up domain and SSL
6. Configure rate limiting
7. Set up error tracking (Sentry, etc.)

## Support

For issues:
1. Check Cloud Run logs
2. Check Secret Manager
3. Verify environment variables
4. Review Cloud SQL connection
5. Check IAM permissions

---

**Deployment Complete! 🚀**

Your Agent47 platform should now be running on Google Cloud Platform.

