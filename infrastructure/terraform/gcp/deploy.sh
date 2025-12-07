#!/bin/bash

# Agent47 GCP Deployment Script
# This script deploys the Agent47 infrastructure to GCP using Terraform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install gcloud CLI first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Check GCP credentials and project
check_gcp_credentials() {
    print_status "Checking GCP credentials..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "No active GCP credentials found. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    if [ -z "$GCP_PROJECT_ID" ] && [ ! -f "terraform.tfvars" ]; then
        print_error "GCP_PROJECT_ID environment variable not set and terraform.tfvars not found."
        print_error "Please set GCP_PROJECT_ID or create terraform.tfvars file."
        exit 1
    fi
    
    print_success "GCP credentials are configured"
}

# Check Supabase configuration
check_supabase_config() {
    print_status "Checking Supabase configuration..."
    
    if [ ! -f "terraform.tfvars" ]; then
        print_error "terraform.tfvars file not found. Please copy terraform.tfvars.example and update the values."
        exit 1
    fi
    
    # Check if Supabase variables are set
    if ! grep -q "supabase_project_id" terraform.tfvars || ! grep -q "supabase_api_url" terraform.tfvars; then
        print_error "Supabase configuration missing in terraform.tfvars."
        print_error "Please add your Supabase project details to terraform.tfvars."
        exit 1
    fi
    
    print_success "Supabase configuration found"
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    terraform init
    print_success "Terraform initialized"
}

# Plan Terraform deployment
plan_terraform() {
    print_status "Planning Terraform deployment..."
    terraform plan -out=tfplan
    print_success "Terraform plan created"
}

# Apply Terraform deployment
apply_terraform() {
    print_status "Applying Terraform deployment..."
    terraform apply tfplan
    print_success "Terraform deployment completed"
}

# Configure kubectl
configure_kubectl() {
    print_status "Configuring kubectl..."
    
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    GCP_REGION=$(terraform output -raw region)
    GCP_PROJECT_ID=$(terraform output -raw project_id)
    
    gcloud container clusters get-credentials $CLUSTER_NAME --region $GCP_REGION --project $GCP_PROJECT_ID
    print_success "kubectl configured for cluster: $CLUSTER_NAME"
}

# Create Kubernetes namespace and secrets
setup_kubernetes() {
    print_status "Setting up Kubernetes..."
    
    # Create namespace
    kubectl create namespace agent47 --dry-run=client -o yaml | kubectl apply -f -
    
    # Create Supabase secrets
    SUPABASE_API_URL=$(terraform output -raw supabase_api_url)
    SUPABASE_ANON_KEY=$(grep "supabase_anon_key" terraform.tfvars | cut -d'"' -f2)
    SUPABASE_SERVICE_ROLE_KEY=$(grep "supabase_service_role_key" terraform.tfvars | cut -d'"' -f2)
    
    kubectl create secret generic supabase-credentials \
        --from-literal=supabase_api_url="$SUPABASE_API_URL" \
        --from-literal=supabase_anon_key="$SUPABASE_ANON_KEY" \
        --from-literal=supabase_service_role_key="$SUPABASE_SERVICE_ROLE_KEY" \
        --namespace agent47 \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Kubernetes setup completed"
}

# Deploy Agent47 to Kubernetes
deploy_agent47() {
    print_status "Deploying Agent47 to Kubernetes..."
    
    # Apply Kubernetes manifests
    kubectl apply -f ../../kubernetes/ -n agent47
    
    print_success "Agent47 deployed to Kubernetes"
}

# Show deployment information
show_deployment_info() {
    print_status "Deployment Information:"
    echo ""
    echo "GCP Project: $(terraform output -raw project_id)"
    echo "Cluster Name: $(terraform output -raw cluster_name)"
    echo "Cluster Endpoint: $(terraform output -raw cluster_endpoint)"
    echo "Load Balancer IP: $(terraform output -raw load_balancer_ip)"
    echo "Storage Bucket: $(terraform output -raw storage_bucket_name)"
    echo ""
    echo "Supabase Integration:"
    echo "Supabase Project ID: $(terraform output -raw supabase_project_id)"
    echo "Supabase API URL: $(terraform output -raw supabase_api_url)"
    echo "Supabase Dashboard: $(terraform output -raw supabase_dashboard_url)"
    echo ""
    echo "Application URLs:"
    echo "Application: $(terraform output -raw application_url)"
    echo "API: $(terraform output -raw api_url)"
    echo ""
    echo "Monitoring:"
    echo "GCP Monitoring: $(terraform output -raw monitoring_dashboard_url)"
    echo "GCP Logging: $(terraform output -raw logging_url)"
    echo ""
    echo "Estimated Monthly Cost: $(terraform output -raw estimated_monthly_cost)"
    echo ""
    print_warning "Next Steps:"
    echo "1. Update your DNS records to point to the load balancer IP"
    echo "2. Configure SSL certificates for your domain"
    echo "3. Update environment variables in Kubernetes secrets"
    echo "4. Monitor the deployment using kubectl get pods -n agent47"
    echo "5. Access Supabase dashboard to configure your database"
}

# Main deployment function
main() {
    print_status "Starting Agent47 GCP deployment..."
    
    check_prerequisites
    check_gcp_credentials
    check_supabase_config
    init_terraform
    plan_terraform
    
    # Ask for confirmation
    echo ""
    print_warning "This will create GCP resources that may incur costs. Do you want to continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    apply_terraform
    configure_kubectl
    setup_kubernetes
    deploy_agent47
    show_deployment_info
    
    print_success "Agent47 GCP deployment completed successfully!"
}

# Run main function
main "$@"
