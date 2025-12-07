#!/bin/bash

# Agent47 Health Check Script
# This script performs comprehensive health checks on the Agent47 platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="agent47"
NAMESPACE="agent47"
TIMEOUT="${TIMEOUT:-30}"
VERBOSE="${VERBOSE:-false}"

# Health check results
declare -A HEALTH_STATUS
declare -A HEALTH_MESSAGES

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

log_verbose() {
    if [ "$VERBOSE" = "true" ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("kubectl" "curl" "jq")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check if kubeconfig is configured
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes cluster is not accessible. Please configure kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

check_kubernetes_cluster() {
    log_info "Checking Kubernetes cluster health..."
    
    # Check cluster connectivity
    if kubectl cluster-info &> /dev/null; then
        HEALTH_STATUS["kubernetes_cluster"]="healthy"
        HEALTH_MESSAGES["kubernetes_cluster"]="Kubernetes cluster is accessible"
        log_success "Kubernetes cluster is healthy"
    else
        HEALTH_STATUS["kubernetes_cluster"]="unhealthy"
        HEALTH_MESSAGES["kubernetes_cluster"]="Kubernetes cluster is not accessible"
        log_error "Kubernetes cluster is not accessible"
    fi
    
    # Check node status
    local unhealthy_nodes=$(kubectl get nodes --no-headers | grep -v "Ready" | wc -l)
    if [ "$unhealthy_nodes" -eq 0 ]; then
        HEALTH_STATUS["kubernetes_nodes"]="healthy"
        HEALTH_MESSAGES["kubernetes_nodes"]="All nodes are ready"
        log_success "All Kubernetes nodes are ready"
    else
        HEALTH_STATUS["kubernetes_nodes"]="unhealthy"
        HEALTH_MESSAGES["kubernetes_nodes"]="$unhealthy_nodes nodes are not ready"
        log_warning "$unhealthy_nodes Kubernetes nodes are not ready"
    fi
}

check_namespace() {
    log_info "Checking namespace health..."
    
    # Check if namespace exists
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        HEALTH_STATUS["namespace"]="healthy"
        HEALTH_MESSAGES["namespace"]="Namespace $NAMESPACE exists"
        log_success "Namespace $NAMESPACE exists"
    else
        HEALTH_STATUS["namespace"]="unhealthy"
        HEALTH_MESSAGES["namespace"]="Namespace $NAMESPACE does not exist"
        log_error "Namespace $NAMESPACE does not exist"
        return 1
    fi
}

check_pods() {
    log_info "Checking pod health..."
    
    # Get all pods in the namespace
    local pods=$(kubectl get pods -n "$NAMESPACE" --no-headers -o custom-columns=":metadata.name")
    local total_pods=0
    local running_pods=0
    local failed_pods=0
    
    for pod in $pods; do
        ((total_pods++))
        local pod_status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        
        case "$pod_status" in
            "Running")
                ((running_pods++))
                log_verbose "Pod $pod is running"
                ;;
            "Failed"|"CrashLoopBackOff"|"Error")
                ((failed_pods++))
                log_warning "Pod $pod is in $pod_status state"
                ;;
            *)
                log_verbose "Pod $pod is in $pod_status state"
                ;;
        esac
    done
    
    if [ "$failed_pods" -eq 0 ] && [ "$running_pods" -gt 0 ]; then
        HEALTH_STATUS["pods"]="healthy"
        HEALTH_MESSAGES["pods"]="$running_pods/$total_pods pods are running"
        log_success "$running_pods/$total_pods pods are running"
    else
        HEALTH_STATUS["pods"]="unhealthy"
        HEALTH_MESSAGES["pods"]="$failed_pods/$total_pods pods have failed"
        log_error "$failed_pods/$total_pods pods have failed"
    fi
}

check_services() {
    log_info "Checking service health..."
    
    # Get all services in the namespace
    local services=$(kubectl get services -n "$NAMESPACE" --no-headers -o custom-columns=":metadata.name")
    local total_services=0
    local healthy_services=0
    
    for service in $services; do
        ((total_services++))
        local service_type=$(kubectl get service "$service" -n "$NAMESPACE" -o jsonpath='{.spec.type}')
        
        if [ "$service_type" = "ClusterIP" ]; then
            # Check if service has endpoints
            local endpoints=$(kubectl get endpoints "$service" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null || echo "")
            if [ -n "$endpoints" ]; then
                ((healthy_services++))
                log_verbose "Service $service has endpoints"
            else
                log_warning "Service $service has no endpoints"
            fi
        else
            ((healthy_services++))
            log_verbose "Service $service is of type $service_type"
        fi
    done
    
    if [ "$healthy_services" -eq "$total_services" ]; then
        HEALTH_STATUS["services"]="healthy"
        HEALTH_MESSAGES["services"]="$healthy_services/$total_services services are healthy"
        log_success "$healthy_services/$total_services services are healthy"
    else
        HEALTH_STATUS["services"]="unhealthy"
        HEALTH_MESSAGES["services"]="$((total_services - healthy_services))/$total_services services have issues"
        log_warning "$((total_services - healthy_services))/$total_services services have issues"
    fi
}

check_deployments() {
    log_info "Checking deployment health..."
    
    # Get all deployments in the namespace
    local deployments=$(kubectl get deployments -n "$NAMESPACE" --no-headers -o custom-columns=":metadata.name")
    local total_deployments=0
    local healthy_deployments=0
    
    for deployment in $deployments; do
        ((total_deployments++))
        local ready_replicas=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired_replicas=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
        
        if [ "$ready_replicas" = "$desired_replicas" ] && [ "$ready_replicas" -gt 0 ]; then
            ((healthy_deployments++))
            log_verbose "Deployment $deployment is healthy ($ready_replicas/$desired_replicas)"
        else
            log_warning "Deployment $deployment is unhealthy ($ready_replicas/$desired_replicas)"
        fi
    done
    
    if [ "$healthy_deployments" -eq "$total_deployments" ]; then
        HEALTH_STATUS["deployments"]="healthy"
        HEALTH_MESSAGES["deployments"]="$healthy_deployments/$total_deployments deployments are healthy"
        log_success "$healthy_deployments/$total_deployments deployments are healthy"
    else
        HEALTH_STATUS["deployments"]="unhealthy"
        HEALTH_MESSAGES["deployments"]="$((total_deployments - healthy_deployments))/$total_deployments deployments have issues"
        log_warning "$((total_deployments - healthy_deployments))/$total_deployments deployments have issues"
    fi
}

check_application_endpoints() {
    log_info "Checking application endpoints..."
    
    # List of services to check
    local services=(
        "agent47-backend:8000:/health"
        "agent47-frontend:3000:/"
        "agent47-aria:8001:/health"
        "agent47-clara:8002:/health"
        "agent47-eric:8003:/health"
        "agent47-jackie:8004:/health"
        "agent47-joe:8005:/health"
        "agent47-purity:8006:/health"
        "agent47-shakes:8007:/health"
        "grok-llm:8001:/health"
    )
    
    local total_services=${#services[@]}
    local healthy_services=0
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port path <<< "$service_info"
        
        # Port forward to service
        kubectl port-forward "service/$service_name" "$port:$port" -n "$NAMESPACE" > /dev/null 2>&1 &
        local pf_pid=$!
        
        # Wait for port forward to be ready
        sleep 2
        
        # Check endpoint
        if curl -f -s "http://localhost:$port$path" > /dev/null 2>&1; then
            ((healthy_services++))
            log_verbose "Service $service_name is responding"
        else
            log_warning "Service $service_name is not responding"
        fi
        
        # Clean up port forward
        kill $pf_pid 2>/dev/null || true
    done
    
    if [ "$healthy_services" -eq "$total_services" ]; then
        HEALTH_STATUS["endpoints"]="healthy"
        HEALTH_MESSAGES["endpoints"]="$healthy_services/$total_services endpoints are responding"
        log_success "$healthy_services/$total_services endpoints are responding"
    else
        HEALTH_STATUS["endpoints"]="unhealthy"
        HEALTH_MESSAGES["endpoints"]="$((total_services - healthy_services))/$total_services endpoints are not responding"
        log_warning "$((total_services - healthy_services))/$total_services endpoints are not responding"
    fi
}

check_database_connectivity() {
    log_info "Checking database connectivity..."
    
    # Check PostgreSQL
    local postgres_pod=$(kubectl get pods -n "$NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$postgres_pod" ]; then
        if kubectl exec "$postgres_pod" -n "$NAMESPACE" -- pg_isready -U agent47 -d agent47_db > /dev/null 2>&1; then
            HEALTH_STATUS["postgres"]="healthy"
            HEALTH_MESSAGES["postgres"]="PostgreSQL is accessible"
            log_success "PostgreSQL is accessible"
        else
            HEALTH_STATUS["postgres"]="unhealthy"
            HEALTH_MESSAGES["postgres"]="PostgreSQL is not accessible"
            log_error "PostgreSQL is not accessible"
        fi
    else
        HEALTH_STATUS["postgres"]="unhealthy"
        HEALTH_MESSAGES["postgres"]="PostgreSQL pod not found"
        log_error "PostgreSQL pod not found"
    fi
    
    # Check Redis
    local redis_pod=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$redis_pod" ]; then
        if kubectl exec "$redis_pod" -n "$NAMESPACE" -- redis-cli ping > /dev/null 2>&1; then
            HEALTH_STATUS["redis"]="healthy"
            HEALTH_MESSAGES["redis"]="Redis is accessible"
            log_success "Redis is accessible"
        else
            HEALTH_STATUS["redis"]="unhealthy"
            HEALTH_MESSAGES["redis"]="Redis is not accessible"
            log_error "Redis is not accessible"
        fi
    else
        HEALTH_STATUS["redis"]="unhealthy"
        HEALTH_MESSAGES["redis"]="Redis pod not found"
        log_error "Redis pod not found"
    fi
}

check_monitoring() {
    log_info "Checking monitoring stack..."
    
    # Check Prometheus
    local prometheus_pod=$(kubectl get pods -n "$NAMESPACE" -l app=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$prometheus_pod" ]; then
        if kubectl exec "$prometheus_pod" -n "$NAMESPACE" -- wget -q --spider http://localhost:9090/-/healthy > /dev/null 2>&1; then
            HEALTH_STATUS["prometheus"]="healthy"
            HEALTH_MESSAGES["prometheus"]="Prometheus is running"
            log_success "Prometheus is running"
        else
            HEALTH_STATUS["prometheus"]="unhealthy"
            HEALTH_MESSAGES["prometheus"]="Prometheus is not responding"
            log_warning "Prometheus is not responding"
        fi
    else
        HEALTH_STATUS["prometheus"]="unhealthy"
        HEALTH_MESSAGES["prometheus"]="Prometheus pod not found"
        log_warning "Prometheus pod not found"
    fi
    
    # Check Grafana
    local grafana_pod=$(kubectl get pods -n "$NAMESPACE" -l app=grafana -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$grafana_pod" ]; then
        if kubectl exec "$grafana_pod" -n "$NAMESPACE" -- wget -q --spider http://localhost:3000/api/health > /dev/null 2>&1; then
            HEALTH_STATUS["grafana"]="healthy"
            HEALTH_MESSAGES["grafana"]="Grafana is running"
            log_success "Grafana is running"
        else
            HEALTH_STATUS["grafana"]="unhealthy"
            HEALTH_MESSAGES["grafana"]="Grafana is not responding"
            log_warning "Grafana is not responding"
        fi
    else
        HEALTH_STATUS["grafana"]="unhealthy"
        HEALTH_MESSAGES["grafana"]="Grafana pod not found"
        log_warning "Grafana pod not found"
    fi
}

check_resource_usage() {
    log_info "Checking resource usage..."
    
    # Check node resource usage
    local nodes=$(kubectl get nodes --no-headers -o custom-columns=":metadata.name")
    local total_nodes=0
    local healthy_nodes=0
    
    for node in $nodes; do
        ((total_nodes++))
        local cpu_usage=$(kubectl top node "$node" --no-headers 2>/dev/null | awk '{print $2}' | sed 's/%//' || echo "0")
        local memory_usage=$(kubectl top node "$node" --no-headers 2>/dev/null | awk '{print $4}' | sed 's/%//' || echo "0")
        
        if [ "$cpu_usage" -lt 80 ] && [ "$memory_usage" -lt 80 ]; then
            ((healthy_nodes++))
            log_verbose "Node $node: CPU $cpu_usage%, Memory $memory_usage%"
        else
            log_warning "Node $node: CPU $cpu_usage%, Memory $memory_usage%"
        fi
    done
    
    if [ "$healthy_nodes" -eq "$total_nodes" ]; then
        HEALTH_STATUS["resources"]="healthy"
        HEALTH_MESSAGES["resources"]="All nodes have healthy resource usage"
        log_success "All nodes have healthy resource usage"
    else
        HEALTH_STATUS["resources"]="unhealthy"
        HEALTH_MESSAGES["resources"]="$((total_nodes - healthy_nodes))/$total_nodes nodes have high resource usage"
        log_warning "$((total_nodes - healthy_nodes))/$total_nodes nodes have high resource usage"
    fi
}

generate_health_report() {
    log_info "Generating health report..."
    
    local report_file="/tmp/agent47_health_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "project_name": "$PROJECT_NAME",
    "namespace": "$NAMESPACE",
    "overall_status": "$(get_overall_status)",
    "checks": {
EOF
    
    local first=true
    for check in "${!HEALTH_STATUS[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        cat >> "$report_file" << EOF
        "$check": {
            "status": "${HEALTH_STATUS[$check]}",
            "message": "${HEALTH_MESSAGES[$check]}"
        }
EOF
    done
    
    cat >> "$report_file" << EOF
    }
}
EOF
    
    log_success "Health report generated: $report_file"
}

get_overall_status() {
    local unhealthy_count=0
    for status in "${HEALTH_STATUS[@]}"; do
        if [ "$status" = "unhealthy" ]; then
            ((unhealthy_count++))
        fi
    done
    
    if [ "$unhealthy_count" -eq 0 ]; then
        echo "healthy"
    elif [ "$unhealthy_count" -le 2 ]; then
        echo "degraded"
    else
        echo "unhealthy"
    fi
}

show_health_summary() {
    log_info "Health Check Summary:"
    echo "======================"
    echo "Overall Status: $(get_overall_status | tr '[:lower:]' '[:upper:]')"
    echo "Timestamp: $(date)"
    echo ""
    
    for check in "${!HEALTH_STATUS[@]}"; do
        local status="${HEALTH_STATUS[$check]}"
        local message="${HEALTH_MESSAGES[$check]}"
        
        case "$status" in
            "healthy")
                echo -e "${GREEN}✓${NC} $check: $message"
                ;;
            "unhealthy")
                echo -e "${RED}✗${NC} $check: $message"
                ;;
            *)
                echo -e "${YELLOW}?${NC} $check: $message"
                ;;
        esac
    done
    
    echo ""
    
    local overall_status=$(get_overall_status)
    case "$overall_status" in
        "healthy")
            log_success "All health checks passed!"
            ;;
        "degraded")
            log_warning "Some health checks failed, but system is operational"
            ;;
        "unhealthy")
            log_error "Multiple health checks failed, system may be unstable"
            exit 1
            ;;
    esac
}

# Main health check flow
main() {
    log_info "Starting Agent47 health check..."
    log_info "Namespace: $NAMESPACE"
    log_info "Timeout: $TIMEOUT seconds"
    
    check_prerequisites
    check_kubernetes_cluster
    check_namespace
    check_pods
    check_services
    check_deployments
    check_application_endpoints
    check_database_connectivity
    check_monitoring
    check_resource_usage
    generate_health_report
    show_health_summary
}

# Handle script arguments
case "${1:-health}" in
    "health")
        main
        ;;
    "quick")
        check_prerequisites
        check_namespace
        check_pods
        check_services
        show_health_summary
        ;;
    "detailed")
        VERBOSE=true
        main
        ;;
    "report")
        main
        ;;
    *)
        echo "Usage: $0 {health|quick|detailed|report}"
        echo ""
        echo "Commands:"
        echo "  health   - Full health check (default)"
        echo "  quick    - Quick health check"
        echo "  detailed - Detailed health check with verbose output"
        echo "  report   - Generate health report"
        echo ""
        echo "Environment Variables:"
        echo "  NAMESPACE - Kubernetes namespace (default: agent47)"
        echo "  TIMEOUT   - Health check timeout in seconds (default: 30)"
        echo "  VERBOSE   - Enable verbose output (true/false)"
        exit 1
        ;;
esac
