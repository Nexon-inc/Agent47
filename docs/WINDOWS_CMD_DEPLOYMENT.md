# Windows CMD Deployment Guide for Agent47

This is a Windows Command Prompt (CMD) specific version of the deployment guide.

## Quick Start (Windows CMD)

```cmd
REM 1. Set your project ID (replace with your actual project ID)
set PROJECT_ID=agent47-backend
gcloud config set project %PROJECT_ID%

REM 2. Enable required APIs (these are NOT set up yet - only Gemini API is enabled)
gcloud services enable run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage-component.googleapis.com --project=%PROJECT_ID%

REM 3. Continue with Step 1 below for full setup
```

## Step 1: Initial Setup

### 1.1 Use Your Existing GCP Project

```cmd
REM Login to GCP
gcloud auth login

REM List your projects to find the ID
gcloud projects list

REM Set your project ID (replace with your actual project ID)
REM You can get it from: gcloud projects list
set PROJECT_ID=agent47-backend

REM Set as active project
gcloud config set project %PROJECT_ID%

REM Verify you're using the correct project
gcloud config get-value project
```

### 1.2 Enable Required APIs

```cmd
REM Get your project ID first (if not already set)
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Enable Cloud Run API (required for deploying services)
gcloud services enable run.googleapis.com --project=%PROJECT_ID%

REM Enable Secret Manager API (required for storing secrets)
gcloud services enable secretmanager.googleapis.com --project=%PROJECT_ID%

REM Enable Cloud Storage API (required for file storage)
gcloud services enable storage-component.googleapis.com --project=%PROJECT_ID%

REM Enable Artifact Registry API (required for Docker images)
gcloud services enable artifactregistry.googleapis.com --project=%PROJECT_ID%

REM Enable Cloud Build API (required for building Docker images)
gcloud services enable cloudbuild.googleapis.com --project=%PROJECT_ID%

REM Verify APIs are enabled
gcloud services list --enabled --project=%PROJECT_ID%
```

### 1.3 Set Up Authentication

```cmd
REM Get your project ID first (if not already set)
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Create service account for Cloud Run (if it doesn't exist)
gcloud iam service-accounts create agent47-run --display-name="Agent47 Cloud Run Service Account" --project=%PROJECT_ID% 2>nul
if errorlevel 1 (
    echo Service account 'agent47-run' already exists, skipping creation.
) else (
    echo Creating service account...
)

REM Grant necessary permissions
echo Granting permissions to service account...

REM Grant Secret Manager access (for reading API keys and secrets)
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:agent47-run@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

REM Grant Storage access (for file uploads/downloads)
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:agent47-run@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"

REM Grant Cloud Run Invoker (for service-to-service communication)
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:agent47-run@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/run.invoker"

echo Service account setup complete!
```

## Step 5: Store Secrets

**Important**: Replace all placeholder values with your actual credentials from your `.env` file.

```cmd
REM Get your project ID first (if not already set)
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Store Supabase URL (replace with your actual Supabase URL from .env)
echo https://your-project.supabase.co | gcloud secrets create supabase-url --data-file=- --project=%PROJECT_ID%

REM Store Supabase Anon Key (replace with your actual key from .env)
echo your-anon-key | gcloud secrets create supabase-anon-key --data-file=- --project=%PROJECT_ID%

REM Store Supabase Service Role Key (replace with your actual key from .env)
echo your-service-role-key | gcloud secrets create supabase-service-key --data-file=- --project=%PROJECT_ID%

REM Store JWT Secret (replace with a strong random secret from .env)
echo your-jwt-secret-key | gcloud secrets create jwt-secret --data-file=- --project=%PROJECT_ID%

REM Store Google Gemini API Key (get this from your .env file)
echo your-gemini-api-key | gcloud secrets create gemini-api-key --data-file=- --project=%PROJECT_ID%

REM Store other API keys as needed (replace with your actual keys from .env)
echo your-groq-api-key | gcloud secrets create groq-api-key --data-file=- --project=%PROJECT_ID%

echo your-openai-api-key | gcloud secrets create openai-api-key --data-file=- --project=%PROJECT_ID%

REM Verify secrets were created
gcloud secrets list --project=%PROJECT_ID%
```

**Note for Windows**: If you have special characters or spaces in your secrets, create a temporary file instead:

```cmd
REM Create a temporary file with your secret
echo your-secret-value > temp_secret.txt

REM Create the secret from file
gcloud secrets create secret-name --data-file=temp_secret.txt --project=%PROJECT_ID%

REM Delete the temporary file
del temp_secret.txt
```

## Step 6: Build and Deploy Backend

### 6.1 Create Artifact Registry

```cmd
REM Get your project ID first (if not already set)
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Create repository (if it doesn't exist)
gcloud artifacts repositories create agent47-repo --repository-format=docker --location=us-central1 --description="Agent47 Docker images" --project=%PROJECT_ID% 2>nul
if errorlevel 1 (
    echo Repository 'agent47-repo' already exists, skipping creation.
) else (
    echo Creating Artifact Registry repository...
)
```

### 6.2 Build Docker Image

```cmd
REM Get your project ID first (if not already set)
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Navigate to project root (where backend folder is located)
cd C:\Users\John Kyalo\Desktop\Agent47

REM Build and push image using Cloud Build (recommended)
REM This will build the Docker image in the cloud
gcloud builds submit --tag us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/backend:latest ./backend --project=%PROJECT_ID%
```

### 6.3 Deploy to Cloud Run

```cmd
REM Get your project ID first (if not already set)
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Deploy backend
REM Replace secret names with the actual names you created in Step 5
gcloud run deploy agent47-backend --image us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/backend:latest --platform managed --region us-central1 --allow-unauthenticated --service-account agent47-run@%PROJECT_ID%.iam.gserviceaccount.com --set-env-vars "ENVIRONMENT=production,DEBUG=false" --set-secrets "SUPABASE_URL=supabase-url:latest,SUPABASE_ANON_KEY=supabase-anon-key:latest,SUPABASE_SERVICE_KEY=supabase-service-key:latest,JWT_SECRET=jwt-secret:latest,GEMINI_API_KEY=gemini-api-key:latest" --memory 2Gi --cpu 2 --timeout 300 --max-instances 10 --min-instances 0 --project=%PROJECT_ID%

REM Get backend URL
for /f "tokens=*" %%i in ('gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)" --project=%PROJECT_ID%') do set BACKEND_URL=%%i
echo Backend URL: %BACKEND_URL%
```

## Step 7: Deploy Frontend

```cmd
REM Get your project ID and backend URL first
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i
for /f "tokens=*" %%i in ('gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)" --project=%PROJECT_ID%') do set BACKEND_URL=%%i

REM Navigate to project root
cd C:\Users\John Kyalo\Desktop\Agent47

REM Build and push frontend image using Cloud Build
REM Replace SUPABASE_URL and SUPABASE_ANON_KEY with your actual values
gcloud builds submit --tag us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/frontend:latest ./frontend --project=%PROJECT_ID%

REM Deploy frontend
REM Replace SUPABASE_URL and SUPABASE_ANON_KEY with your actual values from Step 5
gcloud run deploy agent47-frontend --image us-central1-docker.pkg.dev/%PROJECT_ID%/agent47-repo/frontend:latest --platform managed --region us-central1 --allow-unauthenticated --set-env-vars "NEXT_PUBLIC_API_URL=%BACKEND_URL%,NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co,NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key" --memory 1Gi --cpu 1 --timeout 300 --max-instances 5 --min-instances 0 --project=%PROJECT_ID%

REM Get frontend URL
for /f "tokens=*" %%i in ('gcloud run services describe agent47-frontend --region us-central1 --format="value(status.url)" --project=%PROJECT_ID%') do set FRONTEND_URL=%%i
echo Frontend URL: %FRONTEND_URL%
```

## Windows-Specific Notes

1. **Variable Syntax**: Use `%VARIABLE%` instead of `$VARIABLE`
2. **Setting Variables**: Use `set VAR=value` instead of `export VAR=value`
3. **Command Substitution**: Use `for /f` loops instead of backticks
4. **Line Continuation**: Use `^` for multi-line commands (though gcloud commands usually work on one line)
5. **Error Checking**: Use `if errorlevel 1` instead of `if ! command`

## Common Windows CMD Commands

```cmd
REM Set project ID
set PROJECT_ID=agent47-backend

REM Get project ID from gcloud
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Get service URL
for /f "tokens=*" %%i in ('gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)"') do set BACKEND_URL=%%i

REM Check if command succeeded
if errorlevel 1 (
    echo Command failed
) else (
    echo Command succeeded
)
```

For the complete deployment guide with all steps, see `docs/GOOGLE_CLOUD_DEPLOYMENT.md` (which now includes both Windows and Linux/Mac versions).

