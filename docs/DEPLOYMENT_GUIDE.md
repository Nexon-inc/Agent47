# Zero-Downtime Deployment Guide

This guide explains how the Agent47 platform ensures zero-downtime deployments using Kubernetes rolling updates, health checks, and automatic rollback.

## Overview

The deployment system is designed to ensure your server **never stops**, even during updates. This is achieved through:

1. **Kubernetes Rolling Updates** - Updates pods one at a time
2. **Health Probes** - Ensures new pods are healthy before removing old ones
3. **Multiple Replicas** - Always maintains at least 2 running pods
4. **Automatic Rollback** - Reverts to previous version if deployment fails
5. **Image Versioning** - Uses commit SHA for traceability

## How It Works

### 1. Rolling Update Strategy

All deployments use `RollingUpdate` with:
- `maxSurge: 1` - Creates one new pod before removing old one
- `maxUnavailable: 0` - Ensures at least the minimum number of pods are always running

**Example:**
- You have 3 backend pods running
- During update: 4 pods run (3 old + 1 new)
- Once new pod is healthy: 3 pods run (2 old + 1 new)
- Process continues until all pods are updated
- **Result: Always at least 3 pods serving traffic = Zero downtime**

### 2. Health Checks

Every deployment has:
- **Readiness Probe** - Checks if pod can accept traffic (every 5 seconds)
- **Liveness Probe** - Checks if pod is still alive (every 10 seconds)

If a new pod fails health checks, it's not added to the service, and the old pod continues serving traffic.

### 3. Automatic Rollback

If deployment fails:
- Kubernetes automatically rolls back to previous version
- Old pods continue serving traffic
- No downtime experienced

## Deployment Methods

### Method 1: Automatic CI/CD (Recommended)

**Staging Environment:**
- Triggered on push to `develop` branch
- Automatically builds, tests, and deploys
- Runs smoke tests after deployment

**Production Environment:**
- Triggered on push to `main` branch
- Requires manual approval (GitHub environment protection)
- Full health checks and verification
- Automatic rollback on failure

### Method 2: Manual Deployment Script

Use the zero-downtime deployment script:

```bash
# Deploy backend only
./infrastructure/scripts/zero-downtime-deploy.sh backend gcr.io/PROJECT_ID/agent47-backend:IMAGE_TAG

# Deploy frontend only
./infrastructure/scripts/zero-downtime-deploy.sh frontend gcr.io/PROJECT_ID/agent47-frontend:IMAGE_TAG

# Deploy all agents
./infrastructure/scripts/zero-downtime-deploy.sh agents gcr.io/PROJECT_ID

# Deploy everything
./infrastructure/scripts/zero-downtime-deploy.sh all gcr.io/PROJECT_ID
```

### Method 3: Manual kubectl Commands

```bash
# Update backend image
kubectl set image deployment/backend \
  backend=gcr.io/PROJECT_ID/agent47-backend:IMAGE_TAG \
  -n agent47 --record

# Watch rollout status
kubectl rollout status deployment/backend -n agent47

# Check pod health
kubectl get pods -n agent47 -l app=backend

# Rollback if needed
kubectl rollout undo deployment/backend -n agent47
```

## Required GitHub Secrets

For CI/CD to work, you need to set these secrets in GitHub:

### Staging Environment
- `GCP_SA_KEY_STAGING` - GCP service account key (JSON)
- `GCP_PROJECT_ID_STAGING` - GCP project ID
- `GKE_CLUSTER_NAME_STAGING` - GKE cluster name
- `GKE_REGION_STAGING` - GKE region

### Production Environment
- `GCP_SA_KEY_PROD` - GCP service account key (JSON)
- `GCP_PROJECT_ID_PROD` - GCP project ID
- `GKE_CLUSTER_NAME_PROD` - GKE cluster name
- `GKE_REGION_PROD` - GKE region

### How to Get Service Account Key

1. Go to GCP Console → IAM & Admin → Service Accounts
2. Create or select service account
3. Grant roles:
   - `Kubernetes Engine Developer`
   - `Storage Admin` (for GCR)
   - `Service Account User`
4. Create JSON key and download
5. Add to GitHub Secrets

## Deployment Process Flow

```
1. Code Push → GitHub Actions Triggered
2. Run Tests → Backend & Frontend tests
3. Security Scan → Vulnerability scanning
4. Build Images → Docker images with commit SHA tag
5. Push to GCR → Google Container Registry
6. Update Deployment → kubectl set image (triggers rolling update)
7. Wait for Rollout → kubectl rollout status
8. Health Checks → Verify pods are healthy
9. Smoke Tests → Test critical endpoints
10. Success/ Rollback → Notify or rollback on failure
```

## Monitoring Deployments

### Check Deployment Status

```bash
# View all deployments
kubectl get deployments -n agent47

# View deployment history
kubectl rollout history deployment/backend -n agent47

# View specific revision
kubectl rollout history deployment/backend -n agent47 --revision=2

# View pod status
kubectl get pods -n agent47 -l app=backend

# View pod logs
kubectl logs -f deployment/backend -n agent47
```

### Check Health

```bash
# Check if all pods are ready
kubectl get pods -n agent47 --field-selector=status.phase!=Running

# Check service endpoints
kubectl get endpoints -n agent47

# Test health endpoint
kubectl exec -n agent47 deployment/backend -- curl http://localhost:8000/health
```

## Troubleshooting

### Deployment Stuck

If deployment is stuck:

```bash
# Check rollout status
kubectl rollout status deployment/backend -n agent47

# Check pod events
kubectl describe pod POD_NAME -n agent47

# Check logs
kubectl logs POD_NAME -n agent47

# Force rollback
kubectl rollout undo deployment/backend -n agent47
```

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n agent47

# Check events
kubectl get events -n agent47 --sort-by='.lastTimestamp'

# Check resource limits
kubectl describe pod POD_NAME -n agent47 | grep -A 5 "Limits"
```

### Health Checks Failing

```bash
# Check probe configuration
kubectl describe deployment/backend -n agent47 | grep -A 10 "Liveness\|Readiness"

# Test health endpoint manually
kubectl exec -n agent47 deployment/backend -- curl -v http://localhost:8000/health

# Check if port is correct
kubectl get deployment/backend -n agent47 -o yaml | grep -A 5 "ports"
```

## Best Practices

1. **Always use image tags** - Never use `:latest` in production
2. **Test in staging first** - Deploy to staging before production
3. **Monitor during deployment** - Watch pod status during rollout
4. **Set up alerts** - Get notified of deployment failures
5. **Keep deployment history** - Use `--record` flag for kubectl commands
6. **Regular backups** - Backup database before major deployments
7. **Gradual rollouts** - Consider canary deployments for major changes

## Configuration Files

- **CI/CD**: `.github/workflows/ci.yml`
- **Deployment Script**: `infrastructure/scripts/zero-downtime-deploy.sh`
- **Kubernetes Manifests**: `infrastructure/kubernetes/`
- **Terraform**: `infrastructure/terraform/gcp/`

## Support

If you encounter issues:
1. Check deployment logs in GitHub Actions
2. Check Kubernetes pod logs
3. Review this guide's troubleshooting section
4. Check GCP Console for cluster status

---

**Remember**: With this setup, your server will **never stop** during updates. The rolling update strategy ensures at least the minimum number of pods are always running and serving traffic.

