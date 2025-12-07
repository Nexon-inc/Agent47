# GitHub Deployment Guide for Agent47

This guide covers deploying Agent47 to Google Cloud directly from your GitHub repository.

## Prerequisites

1. ✅ Codebase uploaded to GitHub
2. ✅ Google Cloud project "Agent47 Backend" set up
3. ✅ Gemini API enabled and billing configured
4. ✅ Secrets stored in Secret Manager (Step 5 of main deployment guide)

## Quick Start: Deploy from GitHub

### Step 1: Connect GitHub to Google Cloud Build

#### Windows CMD (Command Prompt)

```cmd
REM Set your project ID
set PROJECT_ID=agent47-backend
gcloud config set project %PROJECT_ID%

REM Connect GitHub (this opens a browser for authentication)
REM Replace YOUR_USERNAME with your GitHub username
REM Replace Agent47 with your repository name if different
gcloud builds triggers create github --name="agent47-deploy" --repo-name="Agent47" --repo-owner="YOUR_USERNAME" --branch-pattern="^main$" --build-config="infrastructure/cloudbuild.yaml" --project=%PROJECT_ID%
```

**What happens:**
1. A browser window opens for GitHub authentication
2. Authorize Google Cloud Build to access your repository
3. The trigger is created and will run on every push to `main` branch

### Step 2: Update cloudbuild.yaml Substitutions

Before the first build, update the substitutions in `infrastructure/cloudbuild.yaml` or set them in the trigger:

**Option A: Update cloudbuild.yaml file**

Edit `infrastructure/cloudbuild.yaml` and replace:
- `_SUPABASE_URL`: Your actual Supabase URL
- `_SUPABASE_ANON_KEY`: Your actual Supabase Anon Key

**Option B: Set in Trigger Configuration (Recommended)**

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click on your trigger `agent47-deploy`
3. Click **"Edit"**
4. Scroll to **"Substitution variables"**
5. Add:
   - `_SUPABASE_URL` = `https://your-project.supabase.co`
   - `_SUPABASE_ANON_KEY` = `your-anon-key`
6. Click **"Save"**

### Step 3: First Deployment

#### Option A: Automatic (via GitHub Push)

```cmd
REM Just push to main branch
git add .
git commit -m "Initial deployment"
git push origin main
```

The build will automatically start. Monitor it at:
https://console.cloud.google.com/cloud-build/builds

#### Option B: Manual Trigger

```cmd
REM Get your project ID
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Manually trigger the build
gcloud builds triggers run agent47-deploy --branch=main --project=%PROJECT_ID%
```

### Step 4: Update Frontend Backend URL

After the first backend deployment, update the frontend's `NEXT_PUBLIC_API_URL`:

```cmd
REM Get backend URL
for /f "tokens=*" %%i in ('gcloud run services describe agent47-backend --region us-central1 --format="value(status.url)"') do set BACKEND_URL=%%i

REM Update frontend with backend URL
gcloud run services update agent47-frontend --region us-central1 --update-env-vars "NEXT_PUBLIC_API_URL=%BACKEND_URL%"
```

Or update the `_BACKEND_URL` substitution in your Cloud Build trigger.

## Deployment Workflow

### Automatic Deployment (Recommended)

1. **Make changes** to your code locally
2. **Commit and push** to GitHub:
   ```cmd
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```
3. **Cloud Build automatically**:
   - Detects the push
   - Builds backend and frontend images
   - Pushes to Artifact Registry
   - Deploys to Cloud Run
4. **Your services update** automatically (usually takes 5-10 minutes)

### Manual Deployment

If you need to deploy manually without pushing to GitHub:

```cmd
REM Get your project ID
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i

REM Build from GitHub
gcloud builds submit --config=infrastructure/cloudbuild.yaml --substitutions=_SUPABASE_URL=https://your-project.supabase.co,_SUPABASE_ANON_KEY=your-anon-key --project=%PROJECT_ID% https://github.com/YOUR_USERNAME/Agent47.git
```

## Updating Secrets

If you need to update secrets (API keys, etc.):

```cmd
REM Update a secret
echo new-api-key-value | gcloud secrets versions add gemini-api-key --data-file=-

REM The next deployment will automatically use the latest version
REM Or force update by redeploying:
gcloud run services update agent47-backend --region us-central1 --update-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

## Monitoring Builds

### View Build Status

```cmd
REM List recent builds
gcloud builds list --limit=10

REM View specific build details
gcloud builds describe BUILD_ID

REM Stream build logs
gcloud builds log BUILD_ID --stream
```

### View in Console

Go to: https://console.cloud.google.com/cloud-build/builds

## Troubleshooting

### Build Fails

1. **Check build logs**:
   ```cmd
   gcloud builds list --limit=1
   gcloud builds log [BUILD_ID] --stream
   ```

2. **Common issues**:
   - Missing secrets in Secret Manager
   - Incorrect Dockerfile paths
   - Build timeout (increase in infrastructure/cloudbuild.yaml)
   - Missing environment variables

### Deployment Fails

1. **Check Cloud Run logs**:
   ```cmd
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent47-backend" --limit 50
   ```

2. **Verify secrets are accessible**:
   ```cmd
   gcloud secrets list
   gcloud run services describe agent47-backend --region us-central1
   ```

### GitHub Connection Issues

1. **Re-authenticate GitHub**:
   - Go to [Cloud Build Settings](https://console.cloud.google.com/cloud-build/settings)
   - Click **"Connect Repository"**
   - Re-authenticate with GitHub

2. **Check repository permissions**:
   - Ensure Google Cloud Build has access to your repository
   - Check GitHub repository settings > Integrations

## Best Practices

1. **Use feature branches**: Test changes in a branch before merging to `main`
2. **Monitor first deployment**: Watch the first build closely
3. **Set up alerts**: Configure Cloud Build notifications
4. **Version your secrets**: Use `:latest` or specific versions
5. **Test locally first**: Build Docker images locally before pushing

## Next Steps

After successful deployment:
1. Test your services (Step 15 of main guide)
2. Set up custom domain (Step 10)
3. Configure monitoring (Step 11)
4. Set up budget alerts (Step 13)

For complete setup instructions, see `docs/GOOGLE_CLOUD_DEPLOYMENT.md`.

