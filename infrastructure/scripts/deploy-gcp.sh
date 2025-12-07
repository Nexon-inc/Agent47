#!/bin/bash

# Agent47 GCP Deployment Script
# This script automates the complete deployment of Agent47 to GCP

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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform/gcp"
SUPABASE_DIR="$PROJECT_ROOT/infrastructure/supabase"
KUBERNETES_DIR="$PROJECT_ROOT/infrastructure/kubernetes"

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("terraform")
    fi
    
    if ! command -v gcloud &> /dev/null; then
        missing_tools+=("gcloud")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v supabase &> /dev/null; then
        missing_tools+=("supabase")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_status "Please install the missing tools and try again."
        print_status "Installation guides:"
        print_status "  Terraform: https://www.terraform.io/downloads.html"
        print_status "  gcloud: https://cloud.google.com/sdk/docs/install"
        print_status "  kubectl: https://kubernetes.io/docs/tasks/tools/"
        print_status "  Supabase: https://supabase.com/docs/guides/cli/getting-started"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Check GCP authentication
check_gcp_auth() {
    print_status "Checking GCP authentication..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "No active GCP credentials found."
        print_status "Please run: gcloud auth login"
        exit 1
    fi
    
    local current_project=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$current_project" ]; then
        print_error "No GCP project set."
        print_status "Please run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    print_success "GCP authentication verified (Project: $current_project)"
}

# Check Supabase configuration
check_supabase_config() {
    print_status "Checking Supabase configuration..."
    
    if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
        print_error "terraform.tfvars file not found in $TERRAFORM_DIR"
        print_status "Please copy terraform.tfvars.example and update the values."
        exit 1
    fi
    
    # Check if Supabase variables are set
    if ! grep -q "supabase_project_id" "$TERRAFORM_DIR/terraform.tfvars" || ! grep -q "supabase_api_url" "$TERRAFORM_DIR/terraform.tfvars"; then
        print_error "Supabase configuration missing in terraform.tfvars."
        print_status "Please add your Supabase project details to terraform.tfvars."
        exit 1
    fi
    
    print_success "Supabase configuration found"
}

# Set up Supabase
setup_supabase() {
    print_status "Setting up Supabase..."
    
    cd "$SUPABASE_DIR"
    
    if [ ! -f "setup-supabase.sh" ]; then
        print_error "Supabase setup script not found"
        exit 1
    fi
    
    chmod +x setup-supabase.sh
    
    # Check if this is a new Supabase project
    if ! supabase projects list | grep -q "agent47"; then
        print_warning "Supabase project not found. Setting up cloud project..."
        ./setup-supabase.sh cloud
    else
        print_success "Supabase project already exists"
    fi
    
    cd "$PROJECT_ROOT"
}

# Deploy GCP infrastructure
deploy_infrastructure() {
    print_status "Deploying GCP infrastructure..."
    
    cd "$TERRAFORM_DIR"
    
    if [ ! -f "deploy.sh" ]; then
        print_error "GCP deployment script not found"
        exit 1
    fi
    
    chmod +x deploy.sh
    ./deploy.sh
    
    cd "$PROJECT_ROOT"
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get GCP project ID and region
    local project_id=$(gcloud config get-value project)
    local region=$(grep "gcp_region" "$TERRAFORM_DIR/terraform.tfvars" | cut -d'"' -f2)
    
    # Configure Docker for GCR
    gcloud auth configure-docker
    
    # Build and push backend image
    print_status "Building backend image..."
    docker build -t "gcr.io/$project_id/agent47-backend:latest" "$PROJECT_ROOT/backend"
    docker push "gcr.io/$project_id/agent47-backend:latest"
    
    # Build and push frontend image
    print_status "Building frontend image..."
    docker build -t "gcr.io/$project_id/agent47-frontend:latest" "$PROJECT_ROOT/frontend"
    docker push "gcr.io/$project_id/agent47-frontend:latest"
    
    # Build and push agent images
    local agents=("aria" "clara" "eric" "jackie" "joe" "purity" "shakes")
    for agent in "${agents[@]}"; do
        print_status "Building $agent agent image..."
        docker build -t "gcr.io/$project_id/agent47-$agent-agent:latest" "$PROJECT_ROOT/backend/agents/$agent"
        docker push "gcr.io/$project_id/agent47-$agent-agent:latest"
    done
    
    # Build and push grok-llm image
    print_status "Building Grok LLM image..."
    docker build -t "gcr.io/$project_id/agent47-grok-llm:latest" "$PROJECT_ROOT/infrastructure/grok-llm"
    docker push "gcr.io/$project_id/agent47-grok-llm:latest"
    
    print_success "All Docker images built and pushed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Get cluster info
    local cluster_name=$(cd "$TERRAFORM_DIR" && terraform output -raw cluster_name)
    local region=$(cd "$TERRAFORM_DIR" && terraform output -raw region)
    local project_id=$(cd "$TERRAFORM_DIR" && terraform output -raw project_id)
    
    # Configure kubectl
    gcloud container clusters get-credentials "$cluster_name" --region "$region" --project "$project_id"
    
    # Create namespace
    kubectl create namespace agent47 --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Supabase secrets
    kubectl apply -f "$KUBERNETES_DIR/supabase-secrets.yaml"
    
    # Apply backend deployment
    kubectl apply -f "$KUBERNETES_DIR/backend-supabase.yaml"
    
    # Apply agent deployments
    kubectl apply -f "$KUBERNETES_DIR/agents-supabase.yaml"
    
    # Apply other services
    kubectl apply -f "$KUBERNETES_DIR/chromadb.yaml"
    kubectl apply -f "$KUBERNETES_DIR/kafka.yaml"
    kubectl apply -f "$KUBERNETES_DIR/grok-llm.yaml"
    kubectl apply -f "$KUBERNETES_DIR/frontend.yaml"
    
    # Apply monitoring
    kubectl apply -f "$KUBERNETES_DIR/monitoring/"
    
    print_success "Kubernetes deployment completed"
}

# Wait for deployment to be ready
wait_for_deployment() {
    print_status "Waiting for deployment to be ready..."
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=backend -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=frontend -n agent47 --timeout=300s
    
    # Wait for services to be ready
    kubectl wait --for=condition=ready pod -l app=aria-agent -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=clara-agent -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=eric-agent -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=jackie-agent -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=joe-agent -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=purity-agent -n agent47 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=shakes-agent -n agent47 --timeout=300s
    
    print_success "All services are ready"
}

# Show deployment information
show_deployment_info() {
    print_status "Deployment Information:"
    echo ""
    
    # Get deployment info
    local load_balancer_ip=$(cd "$TERRAFORM_DIR" && terraform output -raw load_balancer_ip)
    local cluster_name=$(cd "$TERRAFORM_DIR" && terraform output -raw cluster_name)
    local project_id=$(cd "$TERRAFORM_DIR" && terraform output -raw project_id)
    local supabase_url=$(cd "$TERRAFORM_DIR" && terraform output -raw supabase_api_url)
    
    echo "GCP Project: $project_id"
    echo "Cluster Name: $cluster_name"
    echo "Load Balancer IP: $load_balancer_ip"
    echo "Supabase URL: $supabase_url"
    echo ""
    
    echo "Application URLs:"
    echo "  Frontend: https://$load_balancer_ip"
    echo "  API: https://api.$load_balancer_ip"
    echo "  API Docs: https://api.$load_balancer_ip/docs"
    echo ""
    
    echo "Monitoring:"
    echo "  GCP Monitoring: https://console.cloud.google.com/monitoring?project=$project_id"
    echo "  GCP Logging: https://console.cloud.google.com/logs?project=$project_id"
    echo "  Supabase Dashboard: https://supabase.com/dashboard/project/$(grep "supabase_project_id" "$TERRAFORM_DIR/terraform.tfvars" | cut -d'"' -f2)"
    echo ""
    
    echo "Kubernetes Commands:"
    echo "  View pods: kubectl get pods -n agent47"
    echo "  View services: kubectl get services -n agent47"
    echo "  View logs: kubectl logs -f deployment/backend -n agent47"
    echo ""
    
    print_warning "Next Steps:"
    echo "1. Update your DNS records to point to the load balancer IP: $load_balancer_ip"
    echo "2. Wait for SSL certificates to be provisioned (can take up to 1 hour)"
    echo "3. Test your application endpoints"
    echo "4. Monitor the deployment using the provided URLs"
}

# Main deployment function
main() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║    █████╗  ██████╗ ███████╗███╗   ██╗████████╗ ██████╗      ║"
    echo "║   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗     ║"
    echo "║   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║   ██║     ║"
    echo "║   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║     ║"
    echo "║   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ╚██████╔╝     ║"
    echo "║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝      ║"
    echo "║                                                              ║"
    echo "║              GCP + Supabase Deployment                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_prerequisites
    check_gcp_auth
    check_supabase_config
    
    # Ask for confirmation
    echo ""
    print_warning "This will deploy Agent47 to GCP with Supabase integration."
    print_warning "This may incur costs. Do you want to continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    setup_supabase
    deploy_infrastructure
    build_and_push_images
    deploy_kubernetes
    wait_for_deployment
    show_deployment_info
    
    print_success "Agent47 GCP deployment completed successfully!"
}

# Run main function
main "$@"
