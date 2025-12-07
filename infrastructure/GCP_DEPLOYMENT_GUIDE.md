# Agent47 GCP Deployment Guide

This guide walks you through deploying Agent47 to Google Cloud Platform (GCP) with Supabase integration.

## Prerequisites

### 1. Required Tools
- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (gcloud)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/) (optional)

### 2. GCP Account Setup
1. Create a [GCP account](https://cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Kubernetes Engine API
   - Cloud SQL API
   - Cloud Storage API
   - Cloud Monitoring API
   - Cloud Logging API

### 3. Supabase Account Setup
1. Create a [Supabase account](https://supabase.com/)
2. Create a new project
3. Note down your project URL and API keys

## Step 1: Configure GCP Authentication

```bash
# Authenticate with GCP
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

## Step 2: Set Up Supabase

### Option A: Local Development
```bash
cd infrastructure/supabase
chmod +x setup-supabase.sh
./setup-supabase.sh local
```

### Option B: Cloud Production
```bash
cd infrastructure/supabase
chmod +x setup-supabase.sh
./setup-supabase.sh cloud
```

Follow the prompts to:
1. Create a Supabase project
2. Get your API keys
3. Run database migrations

## Step 3: Configure Terraform

```bash
cd infrastructure/terraform/gcp

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
nano terraform.tfvars
```

Update the following values in `terraform.tfvars`:

```hcl
# GCP Configuration
gcp_project_id = "your-gcp-project-id"
gcp_region     = "us-central1"

# Project Configuration
project_name = "agent47"
environment  = "prod"
domain_name  = "your-domain.com"

# Supabase Configuration
supabase_project_id        = "your-supabase-project-id"
supabase_api_url          = "https://your-project-id.supabase.co"
supabase_anon_key         = "your-supabase-anon-key"
supabase_service_role_key = "your-supabase-service-role-key"

# Alert Configuration
alert_email = "your-email@example.com"
```

## Step 4: Deploy Infrastructure

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

The script will:
1. Check prerequisites
2. Initialize Terraform
3. Plan the deployment
4. Apply the infrastructure
5. Configure kubectl
6. Set up Kubernetes secrets
7. Deploy Agent47

## Step 5: Configure DNS

After deployment, you'll get a load balancer IP. Update your DNS records:

```bash
# Get the load balancer IP
terraform output load_balancer_ip

# Update your DNS A record to point to this IP
# For example, if your domain is agent47.com:
# A record: agent47.com -> LOAD_BALANCER_IP
# A record: api.agent47.com -> LOAD_BALANCER_IP
```

## Step 6: Configure SSL Certificates

The Terraform configuration creates managed SSL certificates. They will be automatically provisioned once DNS is configured.

You can check the certificate status:

```bash
gcloud compute ssl-certificates list
```

## Step 7: Verify Deployment

### Check Kubernetes Pods
```bash
kubectl get pods -n agent47
```

### Check Services
```bash
kubectl get services -n agent47
```

### Check Ingress
```bash
kubectl get ingress -n agent47
```

### Test Application
```bash
# Test the API
curl https://api.your-domain.com/health

# Test the frontend
curl https://your-domain.com
```

## Step 8: Monitor Your Deployment

### GCP Monitoring
- [GCP Monitoring Dashboard](https://console.cloud.google.com/monitoring)
- [GCP Logging](https://console.cloud.google.com/logs)

### Kubernetes Monitoring
```bash
# View pod logs
kubectl logs -f deployment/backend -n agent47

# View all logs
kubectl logs -f -l app=backend -n agent47
```

### Supabase Dashboard
- [Supabase Dashboard](https://supabase.com/dashboard)
- Monitor database performance
- View real-time connections
- Check storage usage

## Scaling Your Deployment

### Horizontal Pod Autoscaling
The deployment includes HPA for automatic scaling:

```bash
# Check HPA status
kubectl get hpa -n agent47

# Manually scale if needed
kubectl scale deployment backend --replicas=5 -n agent47
```

### GKE Cluster Autoscaling
The cluster is configured with node autoscaling:

```bash
# Check node pool status
gcloud container node-pools list --cluster=agent47-prod --region=us-central1
```

## Cost Optimization

### 1. Use Preemptible Instances
```hcl
# In terraform.tfvars
enable_spot_instances = true
```

### 2. Right-size Your Instances
```hcl
# For development
node_instance_type = "e2-small"

# For production
node_instance_type = "e2-standard-2"
```

### 3. Monitor Costs
- [GCP Billing Dashboard](https://console.cloud.google.com/billing)
- Set up billing alerts
- Use [GCP Cost Management](https://cloud.google.com/cost-management)

## Troubleshooting

### Common Issues

#### 1. Terraform Apply Fails
```bash
# Check GCP quotas
gcloud compute project-info describe

# Check API enablement
gcloud services list --enabled
```

#### 2. Kubernetes Pods Not Starting
```bash
# Check pod status
kubectl describe pod POD_NAME -n agent47

# Check events
kubectl get events -n agent47 --sort-by='.lastTimestamp'
```

#### 3. SSL Certificate Not Provisioning
```bash
# Check certificate status
kubectl describe certificate -n agent47

# Check DNS propagation
nslookup your-domain.com
```

#### 4. Supabase Connection Issues
```bash
# Check secrets
kubectl get secrets -n agent47

# Test connection
kubectl exec -it deployment/backend -n agent47 -- curl -H "apikey: YOUR_ANON_KEY" https://your-project-id.supabase.co/rest/v1/
```

### Getting Help

1. Check the [GCP Documentation](https://cloud.google.com/docs)
2. Review [Supabase Documentation](https://supabase.com/docs)
3. Check [Kubernetes Documentation](https://kubernetes.io/docs/)
4. Review application logs for specific errors

## Security Best Practices

### 1. Network Security
- Use private GKE nodes
- Configure network policies
- Use VPC-native clusters

### 2. Access Control
- Use IAM roles and service accounts
- Enable workload identity
- Use RBAC in Kubernetes

### 3. Secrets Management
- Store secrets in Kubernetes secrets
- Use external secret management
- Rotate secrets regularly

### 4. Monitoring and Logging
- Enable audit logs
- Set up security monitoring
- Use Cloud Security Command Center

## Backup and Disaster Recovery

### 1. Database Backups
Supabase handles automatic backups, but you can also:
- Export data regularly
- Set up cross-region replication
- Test restore procedures

### 2. Application Backups
```bash
# Backup Kubernetes resources
kubectl get all -n agent47 -o yaml > agent47-backup.yaml

# Backup Terraform state
terraform state pull > terraform-state-backup.json
```

### 3. Disaster Recovery Plan
1. Document recovery procedures
2. Test failover scenarios
3. Maintain runbooks
4. Regular disaster recovery drills

## Maintenance

### Regular Tasks
- Update Kubernetes versions
- Update application images
- Monitor resource usage
- Review security patches
- Update dependencies

### Monitoring
- Set up alerts for critical metrics
- Monitor cost trends
- Track performance metrics
- Review access logs

## Support

For issues with this deployment:
1. Check the troubleshooting section
2. Review application logs
3. Check GCP and Supabase status pages
4. Contact support with detailed error information

---

**Estimated Monthly Cost**: $150-400/month depending on usage and instance types (GCP + Supabase)

**Deployment Time**: 15-30 minutes for infrastructure, additional time for DNS propagation and SSL certificate provisioning.
