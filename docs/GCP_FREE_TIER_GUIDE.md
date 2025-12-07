# Google Cloud Free Tier Guide

## 🎁 GCP Free Tier - What You Get

### Free Credits
- **$300 credit** for 90 days (new accounts)
- **No credit card required** for some services
- **Always Free tier** (permanent free resources)

### Do You Need a Domain?

**Answer: NO** - You don't need a domain to:
- ✅ Get free credits
- ✅ Create GCP account
- ✅ Deploy your application
- ✅ Use GCP services

**You WILL need a domain for:**
- SSL certificates (HTTPS)
- Custom branding
- Production deployment
- OAuth callbacks (some services)

## 🚀 Getting Started with GCP Free Tier

### Step 1: Create GCP Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Get Started for Free"
3. Sign in with your Google account
4. **No credit card required** for free tier signup
5. Accept terms and conditions

### Step 2: Activate Free Trial

1. You'll get **$300 credit** for 90 days
2. This is enough to test your entire platform
3. After 90 days, you can use "Always Free" tier

### Step 3: Create Project

1. Click "Select a project" → "New Project"
2. Name it: `agent47-staging` (or your choice)
3. Click "Create"
4. Select the project

### Step 4: Enable Required APIs

```bash
# Install gcloud CLI first, then:
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

Or enable via Console:
1. Go to "APIs & Services" → "Library"
2. Search and enable:
   - Kubernetes Engine API
   - Compute Engine API
   - Cloud Storage API
   - Secret Manager API
   - Cloud Monitoring API
   - Cloud Logging API

## 💰 Free Tier Limits

### Always Free (Permanent)

**Compute Engine:**
- 1 f1-micro instance per month (US regions)
- 30 GB-month standard persistent disk

**Cloud Storage:**
- 5 GB standard storage
- 5,000 Class A operations
- 50,000 Class B operations

**Cloud Run:**
- 2 million requests per month
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds

**Cloud Functions:**
- 2 million invocations per month
- 400,000 GB-seconds memory
- 200,000 GHz-seconds compute

### Free Trial ($300 Credit)

- Valid for 90 days
- Can use any GCP service
- Perfect for testing your platform
- No restrictions on service types

## 🏗️ Recommended Setup for Agent47

### Option 1: Cloud Run (Easiest - Recommended)

**Pros:**
- Serverless (pay per request)
- Auto-scaling
- No infrastructure management
- Free tier: 2M requests/month

**Cost:** ~$0-10/month (within free tier)

### Option 2: GKE (Kubernetes) - What You Have

**Pros:**
- Full control
- Production-ready
- Auto-scaling
- Zero-downtime deployments

**Cost:** ~$25-50/month (1 small cluster)

**Free Tier:**
- Use preemptible/spot instances
- Use e2-micro nodes
- Single zone deployment

### Option 3: Compute Engine VM

**Pros:**
- Simple setup
- Full control
- Cheapest option

**Cost:** ~$5-10/month (f1-micro instance)

**Free Tier:**
- 1 f1-micro instance free per month
- 30 GB disk free

## 📝 Setup Checklist

### Before Deployment

- [ ] Create GCP account
- [ ] Activate free trial ($300 credit)
- [ ] Create project
- [ ] Enable required APIs
- [ ] Create service account
- [ ] Download service account JSON key
- [ ] Set up billing (required even for free tier)

### For Deployment

- [ ] Set up GitHub Secrets
- [ ] Configure Terraform variables
- [ ] Deploy infrastructure
- [ ] Create Kubernetes secrets
- [ ] Deploy application
- [ ] Test deployment

## 🔐 Billing Account Setup

**Important:** Even free tier requires a billing account, but:
- You won't be charged if you stay within free tier
- $300 credit covers first 90 days
- You can set up billing alerts
- You can disable billing after testing

### Setting Up Billing

1. Go to "Billing" in GCP Console
2. Click "Link a billing account"
3. Add payment method (won't be charged if within free tier)
4. Set up billing alerts:
   - Alert at $10
   - Alert at $50
   - Alert at $100

## 🌐 Domain Requirements

### For Free Credits: **NOT REQUIRED**

You can:
- Use GCP's default hostnames
- Use IP addresses
- Use Cloud Run URLs (e.g., `agent47-xxxxx.run.app`)
- Use GKE load balancer IPs

### When You'll Need a Domain

1. **Production Deployment**
   - Custom domain (e.g., `agent47.com`)
   - SSL certificates
   - Professional branding

2. **OAuth Callbacks**
   - Some services require verified domains
   - Facebook, LinkedIn, etc.

3. **Email Services**
   - Better deliverability with custom domain
   - Professional email addresses

### Getting a Domain (If Needed)

**Free Options:**
- Freenom (.tk, .ml, .ga domains - limited)
- No-IP (dynamic DNS)

**Paid Options (Recommended):**
- Namecheap: $10-15/year
- Google Domains: $12/year
- Cloudflare: $8-10/year

**For Testing:** You can use GCP's default URLs and add a domain later.

## 💡 Cost Optimization Tips

### 1. Use Preemptible Instances
- 80% cheaper than regular instances
- Good for non-critical workloads
- Can be interrupted (but auto-restarts)

### 2. Use Small Instance Types
- e2-micro or f1-micro for testing
- Scale up only when needed

### 3. Use Single Zone
- Multi-zone costs more
- Single zone is fine for testing

### 4. Monitor Usage
- Set up billing alerts
- Check usage regularly
- Use GCP Cost Management tools

### 5. Clean Up Resources
- Delete unused resources
- Stop VMs when not in use
- Delete old images and snapshots

## 📊 Estimated Monthly Costs

### Development/Testing (Free Tier)
- **Cost:** $0-5/month
- Uses free tier resources
- Perfect for testing

### Small Production (Minimal)
- **Cost:** $25-50/month
- 1 small GKE cluster
- 2-3 small nodes
- Basic monitoring

### Medium Production
- **Cost:** $100-200/month
- 1 medium GKE cluster
- 3-5 nodes
- Full monitoring
- Load balancer

## 🚨 Important Notes

1. **Free Trial Expires After 90 Days**
   - Switch to "Always Free" tier
   - Or upgrade to paid account

2. **Billing Account Required**
   - Even for free tier
   - Won't be charged if within limits
   - Set up alerts to monitor

3. **No Domain Needed Initially**
   - Can use GCP default URLs
   - Add domain later for production

4. **Monitor Usage**
   - Check billing dashboard regularly
   - Set up alerts
   - Review costs weekly

## ✅ Quick Start Commands

```bash
# Install gcloud CLI
# Windows: Download from https://cloud.google.com/sdk/docs/install
# Mac: brew install google-cloud-sdk
# Linux: See GCP docs

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com

# Check free tier usage
gcloud billing accounts list
```

## 📚 Resources

- [GCP Free Tier](https://cloud.google.com/free)
- [Always Free Tier](https://cloud.google.com/free/docs/free-cloud-features)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)
- [Billing Alerts](https://cloud.google.com/billing/docs/how-to/budgets)

---

**Bottom Line**: You can start using GCP **right now** without a domain. The $300 free credit is enough to test your entire platform. Add a domain later when you're ready for production!

