# GitHub & GCP Setup Guide - Secrets Management

## 🔐 What Happens to Your `.env` File?

**Good news**: Your `.env` file is **already protected** by `.gitignore` and will **NOT** be uploaded to GitHub. This is correct and secure!

### Files That Stay Local (Not Uploaded)

✅ **Protected by `.gitignore`:**
- `.env` - Your main environment file
- `.env.local`, `.env.production`, `.env.staging` - Environment-specific files
- `*.key`, `*.pem`, `*.crt` - SSL certificates and keys
- `credentials/` - API credentials folder
- `*.tfstate` - Terraform state files
- `*.kubeconfig` - Kubernetes config files
- `logs/`, `uploads/`, `chroma_db/` - Runtime data

### What Gets Uploaded to GitHub

✅ **Safe to upload:**
- `env.example` - Template file (no real secrets)
- All source code
- Configuration templates
- Documentation
- CI/CD workflows

## 📋 How to Handle Secrets for Deployment

You need to store your secrets in **3 places**:

### 1. GitHub Secrets (For CI/CD)

**Location**: GitHub Repository → Settings → Secrets and variables → Actions

**Required Secrets for Staging:**
```
GCP_SA_KEY_STAGING          # GCP Service Account JSON key
GCP_PROJECT_ID_STAGING      # Your GCP project ID
GKE_CLUSTER_NAME_STAGING    # Your GKE cluster name
GKE_REGION_STAGING          # e.g., us-central1
```

**Required Secrets for Production:**
```
GCP_SA_KEY_PROD             # GCP Service Account JSON key
GCP_PROJECT_ID_PROD         # Your GCP project ID
GKE_CLUSTER_NAME_PROD       # Your GKE cluster name
GKE_REGION_PROD             # e.g., us-central1
```

### 2. Kubernetes Secrets (For Runtime)

Your application needs secrets at runtime. These are stored in Kubernetes.

**Option A: Use GCP Secret Manager (Recommended)**
- Store secrets in GCP Secret Manager
- Kubernetes automatically syncs them

**Option B: Create Kubernetes Secrets Manually**
- Use `kubectl create secret` commands
- Or update `infrastructure/kubernetes/supabase-secrets.yaml`

### 3. GCP Secret Manager (Optional but Recommended)

For production, store secrets in GCP Secret Manager for better security.

## 🚀 Step-by-Step Setup Process

### Step 1: Upload Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files (gitignore will exclude .env automatically)
git add .

# Commit
git commit -m "Initial commit - Agent47 platform"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/Agent47.git
git branch -M main
git push -u origin main
```

**Verify**: Check GitHub - you should NOT see `.env` file in the repository.

### Step 2: Set Up GCP Account

#### Do You Need a Domain for GCP Free Credits?

**Answer: NO** - You don't need a domain to get GCP free credits!

**GCP Free Tier Includes:**
- $300 credit for 90 days (no domain required)
- Always Free tier (limited resources, no domain required)
- Free tier services (Compute Engine, Cloud Run, etc.)

**When You Might Need a Domain:**
- For SSL certificates (HTTPS)
- For custom domain names
- For production branding

**For Now**: You can use GCP's default URLs or IP addresses.

### Step 3: Create GCP Service Account

1. Go to [GCP Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable billing (free tier still requires billing account)
4. Go to **IAM & Admin** → **Service Accounts**
5. Click **Create Service Account**
6. Name it: `agent47-deployer`
7. Grant these roles:
   - `Kubernetes Engine Developer`
   - `Storage Admin` (for GCR)
   - `Service Account User`
8. Click **Create Key** → **JSON**
9. **Save this JSON file** - you'll need it for GitHub Secrets

### Step 4: Set Up GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

**Add these secrets:**

**For Staging:**
- Name: `GCP_SA_KEY_STAGING`
  - Value: Paste the **entire contents** of the JSON key file you downloaded
- Name: `GCP_PROJECT_ID_STAGING`
  - Value: Your GCP project ID (e.g., `agent47-staging`)
- Name: `GKE_CLUSTER_NAME_STAGING`
  - Value: Your GKE cluster name (will be created by Terraform)
- Name: `GKE_REGION_STAGING`
  - Value: `us-central1` (or your preferred region)

**For Production:**
- Name: `GCP_SA_KEY_PROD`
  - Value: Paste the **entire contents** of the JSON key file
- Name: `GCP_PROJECT_ID_PROD`
  - Value: Your GCP project ID (e.g., `agent47-prod`)
- Name: `GKE_CLUSTER_NAME_PROD`
  - Value: Your GKE cluster name
- Name: `GKE_REGION_PROD`
  - Value: `us-central1`

### Step 5: Set Up Kubernetes Secrets

After deploying infrastructure, you need to create Kubernetes secrets with your `.env` values.

**Method 1: Using kubectl (Recommended)**

```bash
# Create Supabase secrets
kubectl create secret generic supabase-credentials \
  --from-literal=supabase_anon_key='YOUR_ANON_KEY' \
  --from-literal=supabase_service_role_key='YOUR_SERVICE_ROLE_KEY' \
  --from-literal=supabase_db_url='YOUR_DB_URL' \
  -n agent47

# Create API keys secret
kubectl create secret generic api-keys \
  --from-literal=chutes-api-key='YOUR_CHUTES_KEY' \
  --from-literal=openai-api-key='YOUR_OPENAI_KEY' \
  --from-literal=groq-api-key='YOUR_GROQ_KEY' \
  -n agent47
```

**Method 2: Update YAML Files**

Edit `infrastructure/kubernetes/supabase-secrets.yaml` and encode your values:

```bash
# Encode values (base64)
echo -n "your-actual-value" | base64

# Then update the YAML file with encoded values
```

### Step 6: Deploy Infrastructure

```bash
cd infrastructure/terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

## 🔄 Migration Process: From Local `.env` to Cloud Secrets

### What You Need to Migrate

From your local `.env` file, extract these values:

1. **Supabase Credentials**
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_DB_URL`

2. **API Keys**
   - `CHUTES_API_KEY`
   - `GROQ_API_KEY`
   - `OPENAI_API_KEY`
   - Any other API keys you're using

3. **Security Keys**
   - `SECURITY_SECRET_KEY`
   - `JWT_SECRET_KEY`

4. **Third-Party Integrations**
   - Social media API keys
   - CRM API keys
   - Any other service credentials

### Migration Checklist

- [ ] Extract all values from local `.env`
- [ ] Create GCP service account
- [ ] Add GitHub Secrets for CI/CD
- [ ] Create Kubernetes Secrets for runtime
- [ ] (Optional) Set up GCP Secret Manager
- [ ] Test deployment in staging
- [ ] Verify secrets are working
- [ ] Deploy to production

## 🛡️ Security Best Practices

### ✅ DO:
- Keep `.env` file local only
- Use GitHub Secrets for CI/CD
- Use Kubernetes Secrets for runtime
- Rotate secrets regularly
- Use different secrets for staging/production
- Enable GCP Secret Manager for production

### ❌ DON'T:
- Commit `.env` to GitHub
- Hardcode secrets in code
- Share secrets in chat/email
- Use same secrets for staging and production
- Store secrets in Docker images

## 📝 Quick Reference: Where Secrets Go

| Secret Type | Where to Store | How to Access |
|------------|----------------|---------------|
| GCP Service Account | GitHub Secrets | CI/CD workflows |
| Supabase Credentials | Kubernetes Secrets | Application pods |
| API Keys | Kubernetes Secrets | Application pods |
| Database Passwords | Kubernetes Secrets | Application pods |
| SSL Certificates | Kubernetes Secrets | Ingress/Load Balancer |

## 🌐 Domain Requirements

### For GCP Free Credits: **NO DOMAIN NEEDED**

You can:
- Use GCP's default URLs
- Use IP addresses
- Use GCP's provided hostnames

### When You'll Need a Domain:

1. **SSL Certificates** - For HTTPS (can use Let's Encrypt with domain)
2. **Custom Branding** - For production
3. **Email Deliverability** - For sending emails
4. **OAuth Callbacks** - Some services require verified domains

### Getting a Domain (Optional):

- **Free Options**: Freenom, No-IP (limited)
- **Paid Options**: Namecheap ($10-15/year), Google Domains
- **Recommended**: Get a domain for production ($10-15/year is worth it)

## 🚨 Important Notes

1. **Your `.env` file stays on your computer** - It's safe and won't be uploaded
2. **GitHub Secrets** are encrypted and only accessible to CI/CD
3. **Kubernetes Secrets** are base64 encoded (not encrypted by default)
4. **GCP Secret Manager** provides encryption at rest (recommended for production)

## 📚 Next Steps

1. ✅ Upload code to GitHub (`.env` will be excluded automatically)
2. ✅ Set up GCP account (no domain needed for free credits)
3. ✅ Create service account and download JSON key
4. ✅ Add GitHub Secrets
5. ✅ Deploy infrastructure with Terraform
6. ✅ Create Kubernetes Secrets
7. ✅ Test deployment
8. ✅ (Optional) Get domain for production

## 🔍 Verify Your Setup

### Check `.gitignore` is Working:

```bash
# This should show .env is ignored
git status

# This should NOT show .env
git ls-files | grep .env
```

### Check GitHub Secrets:

1. Go to GitHub → Settings → Secrets
2. Verify all required secrets are present
3. Secrets are masked (you can't see values, only names)

### Check Kubernetes Secrets:

```bash
# List secrets
kubectl get secrets -n agent47

# Verify secret exists
kubectl get secret supabase-credentials -n agent47
```

---

**Remember**: Your `.env` file is safe and won't be uploaded. You just need to manually transfer the values to GitHub Secrets and Kubernetes Secrets for deployment.

