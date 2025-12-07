#!/bin/bash

# Agent47 Secrets Setup Script
# This script helps you set up secrets for GitHub and Kubernetes

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "Please create .env file from env.example first"
    exit 1
fi

print_success ".env file found"

# Function to extract value from .env
get_env_value() {
    local key=$1
    grep "^${key}=" .env | cut -d '=' -f2- | sed 's/^"//;s/"$//' | tr -d '\n'
}

# Function to base64 encode
encode_base64() {
    echo -n "$1" | base64
}

print_info "Extracting secrets from .env file..."

# Extract Supabase credentials
SUPABASE_URL=$(get_env_value "SUPABASE_URL")
SUPABASE_ANON_KEY=$(get_env_value "SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY=$(get_env_value "SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_DB_URL=$(get_env_value "SUPABASE_DB_URL")

# Extract API keys
CHUTES_API_KEY=$(get_env_value "CHUTES_API_KEY")
GROQ_API_KEY=$(get_env_value "GROQ_API_KEY")
OPENAI_API_KEY=$(get_env_value "OPENAI_API_KEY")

# Extract security keys
SECURITY_SECRET_KEY=$(get_env_value "SECURITY_SECRET_KEY")
JWT_SECRET_KEY=$(get_env_value "JWT_SECRET_KEY" || echo "$SECURITY_SECRET_KEY")

print_success "Secrets extracted"

# Create output directory
OUTPUT_DIR="./secrets-output"
mkdir -p "$OUTPUT_DIR"

# Generate Kubernetes secrets YAML
print_info "Generating Kubernetes secrets YAML..."

cat > "$OUTPUT_DIR/kubernetes-secrets.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: supabase-credentials
  namespace: agent47
type: Opaque
data:
  supabase_anon_key: $(encode_base64 "$SUPABASE_ANON_KEY")
  supabase_service_role_key: $(encode_base64 "$SUPABASE_SERVICE_ROLE_KEY")
  supabase_db_url: $(encode_base64 "$SUPABASE_DB_URL")
---
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: agent47
type: Opaque
data:
  chutes-api-key: $(encode_base64 "$CHUTES_API_KEY")
  groq-api-key: $(encode_base64 "$GROQ_API_KEY")
  openai-api-key: $(encode_base64 "$OPENAI_API_KEY")
---
apiVersion: v1
kind: Secret
metadata:
  name: security-keys
  namespace: agent47
type: Opaque
data:
  security-secret-key: $(encode_base64 "$SECURITY_SECRET_KEY")
  jwt-secret-key: $(encode_base64 "$JWT_SECRET_KEY")
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: supabase-config
  namespace: agent47
data:
  SUPABASE_URL: "$SUPABASE_URL"
  SUPABASE_STORAGE_BUCKET: "agent47-uploads"
  SUPABASE_STORAGE_URL: "${SUPABASE_URL}/storage/v1"
  SUPABASE_REALTIME_URL: "wss://$(echo $SUPABASE_URL | sed 's|https://||')/realtime/v1"
  SUPABASE_AUTH_URL: "${SUPABASE_URL}/auth/v1"
EOF

print_success "Kubernetes secrets YAML generated: $OUTPUT_DIR/kubernetes-secrets.yaml"

# Generate GitHub Secrets instructions
print_info "Generating GitHub Secrets setup instructions..."

cat > "$OUTPUT_DIR/github-secrets-instructions.md" <<EOF
# GitHub Secrets Setup Instructions

## Required Secrets

### For Staging Environment

1. **GCP_SA_KEY_STAGING**
   - Go to GCP Console → IAM & Admin → Service Accounts
   - Create service account with roles: Kubernetes Engine Developer, Storage Admin
   - Create JSON key and paste entire contents here

2. **GCP_PROJECT_ID_STAGING**
   - Your GCP project ID (e.g., agent47-staging)

3. **GKE_CLUSTER_NAME_STAGING**
   - Your GKE cluster name (will be created by Terraform)

4. **GKE_REGION_STAGING**
   - Region (e.g., us-central1)

### For Production Environment

1. **GCP_SA_KEY_PROD**
   - Same as staging but for production project

2. **GCP_PROJECT_ID_PROD**
   - Your GCP project ID (e.g., agent47-prod)

3. **GKE_CLUSTER_NAME_PROD**
   - Your GKE cluster name

4. **GKE_REGION_PROD**
   - Region (e.g., us-central1)

## How to Add Secrets

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with the name and value above
5. Click "Add secret"

## Important Notes

- Secrets are encrypted and cannot be viewed after creation
- Only CI/CD workflows can access these secrets
- Use different secrets for staging and production
EOF

print_success "GitHub Secrets instructions generated: $OUTPUT_DIR/github-secrets-instructions.md"

# Generate kubectl commands
print_info "Generating kubectl commands..."

cat > "$OUTPUT_DIR/kubectl-commands.sh" <<EOF
#!/bin/bash
# Commands to create Kubernetes secrets manually

# Create namespace (if not exists)
kubectl create namespace agent47 --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets from YAML
kubectl apply -f kubernetes-secrets.yaml

# Or create secrets manually:
kubectl create secret generic supabase-credentials \\
  --from-literal=supabase_anon_key='$SUPABASE_ANON_KEY' \\
  --from-literal=supabase_service_role_key='$SUPABASE_SERVICE_ROLE_KEY' \\
  --from-literal=supabase_db_url='$SUPABASE_DB_URL' \\
  -n agent47

kubectl create secret generic api-keys \\
  --from-literal=chutes-api-key='$CHUTES_API_KEY' \\
  --from-literal=groq-api-key='$GROQ_API_KEY' \\
  --from-literal=openai-api-key='$OPENAI_API_KEY' \\
  -n agent47

kubectl create secret generic security-keys \\
  --from-literal=security-secret-key='$SECURITY_SECRET_KEY' \\
  --from-literal=jwt-secret-key='$JWT_SECRET_KEY' \\
  -n agent47

# Verify secrets
kubectl get secrets -n agent47
EOF

chmod +x "$OUTPUT_DIR/kubectl-commands.sh"
print_success "kubectl commands generated: $OUTPUT_DIR/kubectl-commands.sh"

# Generate summary
print_info "Generating summary..."

cat > "$OUTPUT_DIR/SECRETS_SUMMARY.md" <<EOF
# Secrets Setup Summary

## ✅ What Was Generated

1. **kubernetes-secrets.yaml** - Ready-to-use Kubernetes secrets
2. **github-secrets-instructions.md** - Instructions for GitHub Secrets
3. **kubectl-commands.sh** - Commands to create secrets manually

## 📋 Next Steps

### 1. Set Up GitHub Secrets
- Follow instructions in: \`github-secrets-instructions.md\`
- Add all required secrets to GitHub repository

### 2. Deploy Kubernetes Secrets
- After infrastructure is deployed, run:
  \`\`\`bash
  kubectl apply -f kubernetes-secrets.yaml
  \`\`\`
- Or use the commands in: \`kubectl-commands.sh\`

### 3. Verify Secrets
\`\`\`bash
kubectl get secrets -n agent47
kubectl get configmap supabase-config -n agent47
\`\`\`

## 🔒 Security Notes

- Never commit these files to git
- Keep them secure and delete after use
- Rotate secrets regularly
- Use different secrets for staging/production
EOF

print_success "Summary generated: $OUTPUT_DIR/SECRETS_SUMMARY.md"

echo ""
print_success "✅ Secrets extraction complete!"
echo ""
print_info "Generated files are in: $OUTPUT_DIR/"
print_info "Review the files and follow the instructions"
echo ""
print_warning "IMPORTANT: These files contain sensitive data!"
print_warning "Do NOT commit them to git. Delete after use."

