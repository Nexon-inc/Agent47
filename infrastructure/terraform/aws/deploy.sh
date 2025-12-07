#!/bin/bash

# Agent47 AWS Deployment Script
# This script deploys the Agent47 infrastructure to AWS using Terraform

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
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "AWS credentials are configured"
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
    AWS_REGION=$(terraform output -raw region)
    
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    print_success "kubectl configured for cluster: $CLUSTER_NAME"
}

# Deploy Agent47 to Kubernetes
deploy_agent47() {
    print_status "Deploying Agent47 to Kubernetes..."
    
    # Create namespace
    kubectl create namespace agent47 --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    kubectl apply -f ../../kubernetes/ -n agent47
    
    print_success "Agent47 deployed to Kubernetes"
}

# Show deployment information
show_deployment_info() {
    print_status "Deployment Information:"
    echo ""
    echo "Cluster Name: $(terraform output -raw cluster_name)"
    echo "Cluster Endpoint: $(terraform output -raw cluster_endpoint)"
    echo "Load Balancer DNS: $(terraform output -raw load_balancer_dns)"
    echo "Database Endpoint: $(terraform output -raw database_endpoint)"
    echo "Redis Endpoint: $(terraform output -raw redis_endpoint)"
    echo "S3 Bucket: $(terraform output -raw storage_bucket_name)"
    echo ""
    echo "Application URLs:"
    echo "Application: $(terraform output -raw application_url)"
    echo "API: $(terraform output -raw api_url)"
    echo ""
    echo "Estimated Monthly Cost: $(terraform output -raw estimated_monthly_cost)"
    echo ""
    print_warning "Remember to:"
    echo "1. Update your DNS records to point to the load balancer"
    echo "2. Configure SSL certificates for your domain"
    echo "3. Update environment variables in Kubernetes secrets"
    echo "4. Monitor the deployment using kubectl get pods -n agent47"
}

# Main deployment function
main() {
    print_status "Starting Agent47 AWS deployment..."
    
    # Check if terraform.tfvars exists
    if [ ! -f "terraform.tfvars" ]; then
        print_error "terraform.tfvars file not found. Please copy terraform.tfvars.example to terraform.tfvars and update the values."
        exit 1
    fi
    
    check_prerequisites
    check_aws_credentials
    init_terraform
    plan_terraform
    
    # Ask for confirmation
    echo ""
    print_warning "This will create AWS resources that may incur costs. Do you want to continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    apply_terraform
    configure_kubectl
    deploy_agent47
    show_deployment_info
    
    print_success "Agent47 deployment completed successfully!"
}

# Run main function
main "$@"
