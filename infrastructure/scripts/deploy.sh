#!/bin/bash

# Agent47 Deployment Script
# This script deploys the entire Agent47 platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="agent47"
ENVIRONMENT="${ENVIRONMENT:-prod}"
CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}"
REGION="${REGION:-us-west-2}"
NAMESPACE="agent47"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("docker" "kubectl" "helm" "terraform")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Please create it from env.example"
        exit 1
    fi
    
    # Check if kubeconfig is configured
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes cluster is not accessible. Please configure kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t "${PROJECT_NAME}-backend:latest" -f backend/Dockerfile .
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t "${PROJECT_NAME}-frontend:latest" -f frontend/Dockerfile frontend/
    
    # Build agent images
    local agents=("aria" "clara" "eric" "jackie" "joe" "purity" "shakes")
    for agent in "${agents[@]}"; do
        log_info "Building ${agent} agent image..."
        docker build -t "${PROJECT_NAME}-${agent}:latest" -f backend/agents/${agent}/Dockerfile backend/agents/${agent}/
    done
    
    # Build Grok LLM image
    log_info "Building Grok LLM image..."
    docker build -t "${PROJECT_NAME}-grok-llm:latest" -f infrastructure/grok-llm/Dockerfile infrastructure/grok-llm/
    
    log_success "All images built successfully"
}

push_images() {
    if [ "$PUSH_IMAGES" = "true" ]; then
        log_info "Pushing images to registry..."
        
        local registry="${DOCKER_REGISTRY:-docker.io}"
        local namespace="${DOCKER_NAMESPACE:-agent47}"
        
        # Tag and push backend
        docker tag "${PROJECT_NAME}-backend:latest" "${registry}/${namespace}/${PROJECT_NAME}-backend:latest"
        docker push "${registry}/${namespace}/${PROJECT_NAME}-backend:latest"
        
        # Tag and push frontend
        docker tag "${PROJECT_NAME}-frontend:latest" "${registry}/${namespace}/${PROJECT_NAME}-frontend:latest"
        docker push "${registry}/${namespace}/${PROJECT_NAME}-frontend:latest"
        
        # Tag and push agents
        local agents=("aria" "clara" "eric" "jackie" "joe" "purity" "shakes")
        for agent in "${agents[@]}"; do
            docker tag "${PROJECT_NAME}-${agent}:latest" "${registry}/${namespace}/${PROJECT_NAME}-${agent}:latest"
            docker push "${registry}/${namespace}/${PROJECT_NAME}-${agent}:latest"
        done
        
        # Tag and push Grok LLM
        docker tag "${PROJECT_NAME}-grok-llm:latest" "${registry}/${namespace}/${PROJECT_NAME}-grok-llm:latest"
        docker push "${registry}/${namespace}/${PROJECT_NAME}-grok-llm:latest"
        
        log_success "All images pushed successfully"
    else
        log_info "Skipping image push (set PUSH_IMAGES=true to push)"
    fi
}

deploy_infrastructure() {
    if [ "$DEPLOY_INFRASTRUCTURE" = "true" ]; then
        log_info "Deploying infrastructure with Terraform..."
        
        cd infrastructure/terraform/${CLOUD_PROVIDER}
        
        # Initialize Terraform
        terraform init
        
        # Plan deployment
        terraform plan -var="environment=${ENVIRONMENT}" -var="region=${REGION}"
        
        # Apply configuration
        terraform apply -auto-approve -var="environment=${ENVIRONMENT}" -var="region=${REGION}"
        
        cd ../../..
        
        log_success "Infrastructure deployed successfully"
    else
        log_info "Skipping infrastructure deployment (set DEPLOY_INFRASTRUCTURE=true to deploy)"
    fi
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets
    log_info "Applying secrets..."
    kubectl apply -f infrastructure/kubernetes/secrets.yaml -n ${NAMESPACE}
    
    # Apply configmaps
    log_info "Applying configmaps..."
    kubectl apply -f infrastructure/kubernetes/configmap.yaml -n ${NAMESPACE}
    
    # Deploy core services
    log_info "Deploying core services..."
    kubectl apply -f infrastructure/kubernetes/postgres.yaml -n ${NAMESPACE}
    kubectl apply -f infrastructure/kubernetes/redis.yaml -n ${NAMESPACE}
    kubectl apply -f infrastructure/kubernetes/kafka.yaml -n ${NAMESPACE}
    kubectl apply -f infrastructure/kubernetes/chromadb.yaml -n ${NAMESPACE}
    
    # Wait for core services to be ready
    log_info "Waiting for core services to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=kafka -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=chromadb -n ${NAMESPACE} --timeout=300s
    
    # Deploy Grok LLM
    log_info "Deploying Grok LLM..."
    kubectl apply -f infrastructure/kubernetes/grok-llm.yaml -n ${NAMESPACE}
    
    # Deploy backend
    log_info "Deploying backend..."
    kubectl apply -f infrastructure/kubernetes/backend.yaml -n ${NAMESPACE}
    
    # Deploy agents
    log_info "Deploying agents..."
    kubectl apply -f infrastructure/kubernetes/agents/ -n ${NAMESPACE}
    
    # Deploy frontend
    log_info "Deploying frontend..."
    kubectl apply -f infrastructure/kubernetes/frontend.yaml -n ${NAMESPACE}
    
    # Deploy monitoring
    if [ "$ENABLE_MONITORING" = "true" ]; then
        log_info "Deploying monitoring stack..."
        kubectl apply -f infrastructure/kubernetes/monitoring/ -n ${NAMESPACE}
    fi
    
    log_success "Kubernetes deployment completed"
}

wait_for_deployment() {
    log_info "Waiting for all deployments to be ready..."
    
    # Wait for backend
    kubectl wait --for=condition=available deployment/agent47-backend -n ${NAMESPACE} --timeout=600s
    
    # Wait for agents
    local agents=("aria" "clara" "eric" "jackie" "joe" "purity" "shakes")
    for agent in "${agents[@]}"; do
        kubectl wait --for=condition=available deployment/agent47-${agent} -n ${NAMESPACE} --timeout=600s
    done
    
    # Wait for frontend
    kubectl wait --for=condition=available deployment/agent47-frontend -n ${NAMESPACE} --timeout=600s
    
    log_success "All deployments are ready"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Get service endpoints
    local backend_port=$(kubectl get service agent47-backend -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].port}')
    local frontend_port=$(kubectl get service agent47-frontend -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].port}')
    
    # Port forward for health checks
    kubectl port-forward service/agent47-backend ${backend_port}:${backend_port} -n ${NAMESPACE} &
    local backend_pf_pid=$!
    
    kubectl port-forward service/agent47-frontend ${frontend_port}:${frontend_port} -n ${NAMESPACE} &
    local frontend_pf_pid=$!
    
    # Wait for port forwards to be ready
    sleep 5
    
    # Health check backend
    if curl -f http://localhost:${backend_port}/health > /dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
    fi
    
    # Health check frontend
    if curl -f http://localhost:${frontend_port}/ > /dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
    fi
    
    # Clean up port forwards
    kill $backend_pf_pid $frontend_pf_pid 2>/dev/null || true
    
    log_success "Health checks completed"
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo "=========================="
    echo "Environment: ${ENVIRONMENT}"
    echo "Cloud Provider: ${CLOUD_PROVIDER}"
    echo "Region: ${REGION}"
    echo "Namespace: ${NAMESPACE}"
    echo ""
    
    log_info "Service Endpoints:"
    kubectl get services -n ${NAMESPACE}
    echo ""
    
    log_info "Pod Status:"
    kubectl get pods -n ${NAMESPACE}
    echo ""
    
    log_info "Ingress Information:"
    kubectl get ingress -n ${NAMESPACE} 2>/dev/null || echo "No ingress configured"
    echo ""
    
    log_success "Deployment completed successfully!"
    log_info "You can access the application at: https://agent47.com"
    log_info "Admin panel: https://admin.agent47.com"
    log_info "API: https://api.agent47.com"
}

# Main deployment flow
main() {
    log_info "Starting Agent47 deployment..."
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Cloud Provider: ${CLOUD_PROVIDER}"
    log_info "Region: ${REGION}"
    
    check_prerequisites
    build_images
    push_images
    deploy_infrastructure
    deploy_kubernetes
    wait_for_deployment
    run_health_checks
    show_deployment_info
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "build")
        check_prerequisites
        build_images
        ;;
    "push")
        check_prerequisites
        push_images
        ;;
    "infrastructure")
        check_prerequisites
        deploy_infrastructure
        ;;
    "kubernetes")
        check_prerequisites
        deploy_kubernetes
        ;;
    "health")
        run_health_checks
        ;;
    "status")
        show_deployment_info
        ;;
    *)
        echo "Usage: $0 {deploy|build|push|infrastructure|kubernetes|health|status}"
        echo ""
        echo "Commands:"
        echo "  deploy         - Full deployment (default)"
        echo "  build          - Build Docker images only"
        echo "  push           - Push images to registry"
        echo "  infrastructure - Deploy infrastructure with Terraform"
        echo "  kubernetes     - Deploy to Kubernetes only"
        echo "  health         - Run health checks"
        echo "  status         - Show deployment status"
        echo ""
        echo "Environment Variables:"
        echo "  ENVIRONMENT           - Environment (dev/staging/prod)"
        echo "  CLOUD_PROVIDER        - Cloud provider (aws/gcp/azure)"
        echo "  REGION               - Deployment region"
        echo "  PUSH_IMAGES          - Push images to registry (true/false)"
        echo "  DEPLOY_INFRASTRUCTURE - Deploy infrastructure (true/false)"
        echo "  ENABLE_MONITORING    - Enable monitoring stack (true/false)"
        exit 1
        ;;
esac
