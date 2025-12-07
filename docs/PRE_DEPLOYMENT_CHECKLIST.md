# Pre-Deployment Checklist

Use this checklist before uploading to GitHub and deploying to GCP.

## ✅ Pre-Upload Checklist

### 1. Verify `.gitignore` is Working

```bash
# Check if .env is ignored
git status

# Should NOT show .env file
git ls-files | grep .env
```

**Expected Result:** `.env` should NOT appear in the list.

### 2. Files That Should NOT Be Uploaded

Verify these are in `.gitignore`:
- ✅ `.env` and all `.env.*` files
- ✅ `credentials/` folder
- ✅ `*.key`, `*.pem` files
- ✅ `logs/` folder
- ✅ `uploads/` folder
- ✅ `chroma_db/` folder
- ✅ `*.tfstate` files
- ✅ `*.kubeconfig` files

### 3. Files That SHOULD Be Uploaded

Verify these are included:
- ✅ `env.example` (template, no real secrets)
- ✅ All source code
- ✅ Configuration files (templates)
- ✅ Documentation
- ✅ CI/CD workflows
- ✅ Infrastructure code

## 📤 Upload to GitHub

### Step 1: Initialize Git (if not done)

```bash
git init
git add .
git commit -m "Initial commit - Agent47 platform"
```

### Step 2: Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click "New repository"
3. Name it: `Agent47` (or your choice)
4. **DO NOT** initialize with README (you already have files)
5. Click "Create repository"

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/Agent47.git
git branch -M main
git push -u origin main
```

### Step 4: Verify Upload

1. Go to your GitHub repository
2. Check that `.env` is **NOT** visible
3. Verify all code files are present
4. Check that `env.example` is visible

## 🔐 Secrets Setup

### Step 1: Extract Secrets from `.env`

Run the setup script:
```bash
chmod +x scripts/setup-secrets.sh
./scripts/setup-secrets.sh
```

This will create:
- `secrets-output/kubernetes-secrets.yaml`
- `secrets-output/github-secrets-instructions.md`
- `secrets-output/kubectl-commands.sh`

### Step 2: Set Up GitHub Secrets

1. Go to GitHub → Settings → Secrets and variables → Actions
2. Add secrets from `secrets-output/github-secrets-instructions.md`
3. **Important:** Add GCP service account JSON key

### Step 3: Set Up GCP

1. Create GCP account (no domain needed)
2. Activate free trial ($300 credit)
3. Create project
4. Enable required APIs
5. Create service account
6. Download JSON key

### Step 4: Deploy Infrastructure

```bash
cd infrastructure/terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform plan
terraform apply
```

### Step 5: Create Kubernetes Secrets

After infrastructure is deployed:

```bash
# Apply secrets
kubectl apply -f secrets-output/kubernetes-secrets.yaml

# Or use commands
./secrets-output/kubectl-commands.sh
```

## 🎯 Final Verification

- [ ] Code uploaded to GitHub
- [ ] `.env` file NOT in GitHub
- [ ] GitHub Secrets configured
- [ ] GCP account created
- [ ] GCP project created
- [ ] APIs enabled
- [ ] Service account created
- [ ] Infrastructure deployed
- [ ] Kubernetes secrets created
- [ ] Application deployed
- [ ] Health checks passing

## 🚨 Security Reminders

1. **Never commit `.env`** - It's in `.gitignore` for a reason
2. **Delete secrets output files** after use
3. **Use different secrets** for staging/production
4. **Rotate secrets** regularly
5. **Monitor access** to secrets

## 📝 What Happens to Your `.env` File?

**Your `.env` file:**
- ✅ Stays on your local computer
- ✅ Will NOT be uploaded to GitHub
- ✅ Protected by `.gitignore`
- ✅ You'll manually transfer values to:
  - GitHub Secrets (for CI/CD)
  - Kubernetes Secrets (for runtime)

**This is the correct and secure approach!**

---

**Ready to deploy?** Follow the steps above, and your secrets will be secure while your code is on GitHub!

