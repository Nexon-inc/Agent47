#!/bin/bash

# Zero-Downtime Deployment Script for Agent47
# This script ensures zero-downtime deployments with health checks and automatic rollback

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="agent47"
TIMEOUT=600  # 10 minutes timeout for deployments
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10

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

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_success "kubectl is configured correctly"
}

# Function to wait for deployment to be ready
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    
    print_status "Waiting for deployment $deployment to be ready..."
    
    if kubectl rollout status deployment/$deployment -n $namespace --timeout=${TIMEOUT}s; then
        print_success "Deployment $deployment is ready"
        return 0
    else
        print_error "Deployment $deployment failed to become ready"
        return 1
    fi
}

# Function to check pod health
check_pod_health() {
    local deployment=$1
    local namespace=$2
    local retries=$3
    local interval=$4
    
    print_status "Checking health of $deployment pods..."
    
    for i in $(seq 1 $retries); do
        # Get pods for this deployment
        local pods=$(kubectl get pods -n $namespace -l app=$deployment -o jsonpath='{.items[*].metadata.name}')
        
        if [ -z "$pods" ]; then
            print_warning "No pods found for $deployment, waiting..."
            sleep $interval
            continue
        fi
        
        # Check if all pods are ready
        local ready_pods=$(kubectl get pods -n $namespace -l app=$deployment -o jsonpath='{.items[?(@.status.conditions[?(@.type=="Ready")].status=="True")].metadata.name}' | wc -w)
        local total_pods=$(echo $pods | wc -w)
        
        if [ "$ready_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
            print_success "All $total_pods pods for $deployment are ready"
            return 0
        fi
        
        print_status "Waiting for pods to be ready ($ready_pods/$total_pods)... (attempt $i/$retries)"
        sleep $interval
    done
    
    print_error "Pods for $deployment did not become healthy within timeout"
    return 1
}

# Function to perform health check on service
check_service_health() {
    local service=$1
    local namespace=$2
    local port=$3
    local path=${4:-/health}
    
    print_status "Checking health of service $service..."
    
    # Get service endpoint
    local endpoint=$(kubectl get service $service -n $namespace -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || \
                     kubectl get service $service -n $namespace -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
    
    if [ -z "$endpoint" ]; then
        print_warning "Could not determine endpoint for service $service, skipping health check"
        return 0
    fi
    
    # Try to curl the health endpoint
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if kubectl run health-check-$RANDOM --rm -i --restart=Never --image=curlimages/curl:latest \
           -- curl -f -s http://$endpoint:$port$path > /dev/null 2>&1; then
            print_success "Service $service is healthy"
            return 0
        fi
        
        print_status "Health check attempt $i/$HEALTH_CHECK_RETRIES failed, retrying..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    print_error "Service $service health check failed after $HEALTH_CHECK_RETRIES attempts"
    return 1
}

# Function to rollback deployment
rollback_deployment() {
    local deployment=$1
    local namespace=$2
    
    print_warning "Rolling back deployment $deployment..."
    
    if kubectl rollout undo deployment/$deployment -n $namespace; then
        print_success "Rollback initiated for $deployment"
        
        # Wait for rollback to complete
        if wait_for_deployment $deployment $namespace; then
            print_success "Rollback completed successfully for $deployment"
            return 0
        else
            print_error "Rollback failed for $deployment"
            return 1
        fi
    else
        print_error "Failed to initiate rollback for $deployment"
        return 1
    fi
}

# Function to deploy a single service
deploy_service() {
    local deployment=$1
    local namespace=$2
    local image=$3
    local container_name=${4:-$deployment}
    
    print_status "Deploying $deployment with image $image..."
    
    # Update deployment image
    if kubectl set image deployment/$deployment $container_name=$image -n $namespace --record; then
        print_success "Image updated for $deployment"
    else
        print_error "Failed to update image for $deployment"
        return 1
    fi
    
    # Wait for deployment to be ready
    if ! wait_for_deployment $deployment $namespace; then
        print_error "Deployment $deployment failed"
        rollback_deployment $deployment $namespace
        return 1
    fi
    
    # Check pod health
    if ! check_pod_health $deployment $namespace $HEALTH_CHECK_RETRIES $HEALTH_CHECK_INTERVAL; then
        print_error "Pods for $deployment are not healthy"
        rollback_deployment $deployment $namespace
        return 1
    fi
    
    print_success "Deployment $deployment completed successfully"
    return 0
}

# Function to deploy backend
deploy_backend() {
    local image=$1
    print_status "=== Deploying Backend ==="
    deploy_service "backend" $NAMESPACE $image "backend"
}

# Function to deploy frontend
deploy_frontend() {
    local image=$1
    print_status "=== Deploying Frontend ==="
    deploy_service "agent47-frontend" $NAMESPACE $image "frontend"
}

# Function to deploy agents
deploy_agents() {
    local image_prefix=$1
    local agents=("aria" "clara" "eric" "jackie" "joe" "purity" "shakes")
    
    print_status "=== Deploying Agents ==="
    
    for agent in "${agents[@]}"; do
        local image="$image_prefix/agent47-$agent-agent"
        local deployment="$agent-agent"
        
        print_status "Deploying $agent agent..."
        if ! deploy_service $deployment $NAMESPACE $image "$agent-agent"; then
            print_error "Failed to deploy $agent agent"
            # Continue with other agents even if one fails
        fi
    done
}

# Main deployment function
main() {
    local component=$1
    local image=$2
    
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║         Agent47 Zero-Downtime Deployment Script              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_kubectl
    
    case $component in
        backend)
            deploy_backend $image
            ;;
        frontend)
            deploy_frontend $image
            ;;
        agents)
            deploy_agents $image
            ;;
        all)
            deploy_backend "$image/agent47-backend"
            deploy_frontend "$image/agent47-frontend"
            deploy_agents $image
            ;;
        *)
            print_error "Unknown component: $component"
            echo "Usage: $0 {backend|frontend|agents|all} <image>"
            exit 1
            ;;
    esac
    
    print_success "All deployments completed successfully!"
}

# Run main function
main "$@"

