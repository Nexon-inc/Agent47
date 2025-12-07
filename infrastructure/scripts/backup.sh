#!/bin/bash

# Agent47 Backup Script
# This script creates backups of the Agent47 platform data

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
BACKUP_DIR="${BACKUP_DIR:-/backups/agent47}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS="${RETENTION_DAYS:-7}"

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
    local tools=("kubectl" "pg_dump" "redis-cli")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check if backup directory exists
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
    
    # Check if kubeconfig is configured
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes cluster is not accessible. Please configure kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

backup_database() {
    log_info "Backing up PostgreSQL database..."
    
    local backup_file="$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
    
    # Get database connection details
    local db_host=$(kubectl get service postgres -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    local db_port=$(kubectl get service postgres -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    local db_name=$(kubectl get configmap agent47-config -n $NAMESPACE -o jsonpath='{.data.DB_POSTGRES_DB}')
    local db_user=$(kubectl get configmap agent47-config -n $NAMESPACE -o jsonpath='{.data.DB_POSTGRES_USER}')
    local db_password=$(kubectl get secret agent47-secrets -n $NAMESPACE -o jsonpath='{.data.DB_POSTGRES_PASSWORD}' | base64 -d)
    
    # Set password environment variable
    export PGPASSWORD="$db_password"
    
    # Create database backup
    if pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" --no-password > "$backup_file"; then
        log_success "Database backup created: $backup_file"
        
        # Compress backup
        gzip "$backup_file"
        log_success "Database backup compressed: $backup_file.gz"
    else
        log_error "Database backup failed"
        exit 1
    fi
    
    # Clean up environment variable
    unset PGPASSWORD
}

backup_redis() {
    log_info "Backing up Redis data..."
    
    local backup_file="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"
    
    # Get Redis connection details
    local redis_host=$(kubectl get service redis -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    local redis_port=$(kubectl get service redis -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')
    
    # Create Redis backup using BGSAVE
    if redis-cli -h "$redis_host" -p "$redis_port" BGSAVE; then
        log_success "Redis backup initiated"
        
        # Wait for backup to complete
        while [ "$(redis-cli -h "$redis_host" -p "$redis_port" LASTSAVE)" = "$(redis-cli -h "$redis_host" -p "$redis_port" LASTSAVE)" ]; do
            sleep 1
        done
        
        # Copy backup file from Redis pod
        local redis_pod=$(kubectl get pods -n $NAMESPACE -l app=redis -o jsonpath='{.items[0].metadata.name}')
        kubectl cp "$NAMESPACE/$redis_pod:/data/dump.rdb" "$backup_file"
        
        # Compress backup
        gzip "$backup_file"
        log_success "Redis backup created: $backup_file.gz"
    else
        log_error "Redis backup failed"
        exit 1
    fi
}

backup_chromadb() {
    log_info "Backing up ChromaDB data..."
    
    local backup_file="$BACKUP_DIR/chromadb_backup_$TIMESTAMP.tar.gz"
    
    # Get ChromaDB pod
    local chromadb_pod=$(kubectl get pods -n $NAMESPACE -l app=chromadb -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$chromadb_pod" ]; then
        # Create backup of ChromaDB data directory
        kubectl exec -n $NAMESPACE "$chromadb_pod" -- tar -czf /tmp/chromadb_backup.tar.gz /chroma
        kubectl cp "$NAMESPACE/$chromadb_pod:/tmp/chromadb_backup.tar.gz" "$backup_file"
        
        log_success "ChromaDB backup created: $backup_file"
    else
        log_warning "ChromaDB pod not found, skipping backup"
    fi
}

backup_kafka() {
    log_info "Backing up Kafka data..."
    
    local backup_file="$BACKUP_DIR/kafka_backup_$TIMESTAMP.tar.gz"
    
    # Get Kafka pod
    local kafka_pod=$(kubectl get pods -n $NAMESPACE -l app=kafka -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$kafka_pod" ]; then
        # Create backup of Kafka data directory
        kubectl exec -n $NAMESPACE "$kafka_pod" -- tar -czf /tmp/kafka_backup.tar.gz /var/lib/kafka/data
        kubectl cp "$NAMESPACE/$kafka_pod:/tmp/kafka_backup.tar.gz" "$backup_file"
        
        log_success "Kafka backup created: $backup_file"
    else
        log_warning "Kafka pod not found, skipping backup"
    fi
}

backup_kubernetes_resources() {
    log_info "Backing up Kubernetes resources..."
    
    local backup_file="$BACKUP_DIR/kubernetes_resources_$TIMESTAMP.yaml"
    
    # Backup all resources in the namespace
    kubectl get all -n $NAMESPACE -o yaml > "$backup_file"
    
    # Backup configmaps
    kubectl get configmaps -n $NAMESPACE -o yaml >> "$backup_file"
    
    # Backup secrets (without sensitive data)
    kubectl get secrets -n $NAMESPACE -o yaml | sed 's/data:.*/data: [REDACTED]/' >> "$backup_file"
    
    # Compress backup
    gzip "$backup_file"
    log_success "Kubernetes resources backup created: $backup_file.gz"
}

backup_application_data() {
    log_info "Backing up application data..."
    
    local backup_file="$BACKUP_DIR/application_data_$TIMESTAMP.tar.gz"
    
    # Create temporary directory for application data
    local temp_dir=$(mktemp -d)
    
    # Backup logs from all pods
    local pods=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')
    for pod in $pods; do
        log_info "Backing up logs from pod: $pod"
        kubectl logs "$pod" -n $NAMESPACE > "$temp_dir/${pod}_logs.txt" 2>/dev/null || true
    done
    
    # Backup configuration files
    kubectl get configmap agent47-config -n $NAMESPACE -o yaml > "$temp_dir/configmap.yaml"
    
    # Create tar archive
    tar -czf "$backup_file" -C "$temp_dir" .
    
    # Clean up temporary directory
    rm -rf "$temp_dir"
    
    log_success "Application data backup created: $backup_file"
}

cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    local deleted_count=0
    
    # Find and delete old backup files
    while IFS= read -r -d '' file; do
        rm "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [ $deleted_count -gt 0 ]; then
        log_success "Cleaned up $deleted_count old backup files"
    else
        log_info "No old backup files to clean up"
    fi
}

create_backup_manifest() {
    log_info "Creating backup manifest..."
    
    local manifest_file="$BACKUP_DIR/backup_manifest_$TIMESTAMP.json"
    
    cat > "$manifest_file" << EOF
{
    "backup_timestamp": "$TIMESTAMP",
    "backup_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "project_name": "$PROJECT_NAME",
    "namespace": "$NAMESPACE",
    "backup_directory": "$BACKUP_DIR",
    "retention_days": $RETENTION_DAYS,
    "backup_files": [
        $(find "$BACKUP_DIR" -name "*_$TIMESTAMP*" -type f -printf '"%p",\n' | sed '$s/,$//')
    ],
    "backup_size": "$(du -sh "$BACKUP_DIR" | cut -f1)",
    "backup_status": "completed"
}
EOF
    
    log_success "Backup manifest created: $manifest_file"
}

verify_backups() {
    log_info "Verifying backup integrity..."
    
    local verification_failed=false
    
    # Check if backup files exist and are not empty
    for file in "$BACKUP_DIR"/*_$TIMESTAMP*; do
        if [ -f "$file" ]; then
            if [ -s "$file" ]; then
                log_success "Backup file verified: $(basename "$file")"
            else
                log_error "Backup file is empty: $(basename "$file")"
                verification_failed=true
            fi
        fi
    done
    
    if [ "$verification_failed" = true ]; then
        log_error "Backup verification failed"
        exit 1
    else
        log_success "All backup files verified successfully"
    fi
}

show_backup_summary() {
    log_info "Backup Summary:"
    echo "=================="
    echo "Backup Directory: $BACKUP_DIR"
    echo "Backup Timestamp: $TIMESTAMP"
    echo "Retention Days: $RETENTION_DAYS"
    echo ""
    
    log_info "Backup Files:"
    ls -lh "$BACKUP_DIR"/*_$TIMESTAMP* 2>/dev/null || echo "No backup files found"
    echo ""
    
    log_info "Total Backup Size:"
    du -sh "$BACKUP_DIR"
    echo ""
    
    log_success "Backup completed successfully!"
}

# Main backup flow
main() {
    log_info "Starting Agent47 backup..."
    log_info "Backup Directory: $BACKUP_DIR"
    log_info "Retention Days: $RETENTION_DAYS"
    
    check_prerequisites
    backup_database
    backup_redis
    backup_chromadb
    backup_kafka
    backup_kubernetes_resources
    backup_application_data
    cleanup_old_backups
    create_backup_manifest
    verify_backups
    show_backup_summary
}

# Handle script arguments
case "${1:-backup}" in
    "backup")
        main
        ;;
    "database")
        check_prerequisites
        backup_database
        ;;
    "redis")
        check_prerequisites
        backup_redis
        ;;
    "chromadb")
        check_prerequisites
        backup_chromadb
        ;;
    "kafka")
        check_prerequisites
        backup_kafka
        ;;
    "kubernetes")
        check_prerequisites
        backup_kubernetes_resources
        ;;
    "application")
        check_prerequisites
        backup_application_data
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "verify")
        verify_backups
        ;;
    *)
        echo "Usage: $0 {backup|database|redis|chromadb|kafka|kubernetes|application|cleanup|verify}"
        echo ""
        echo "Commands:"
        echo "  backup      - Full backup (default)"
        echo "  database    - Backup PostgreSQL database only"
        echo "  redis       - Backup Redis data only"
        echo "  chromadb    - Backup ChromaDB data only"
        echo "  kafka       - Backup Kafka data only"
        echo "  kubernetes  - Backup Kubernetes resources only"
        echo "  application - Backup application data only"
        echo "  cleanup     - Clean up old backups"
        echo "  verify      - Verify backup integrity"
        echo ""
        echo "Environment Variables:"
        echo "  BACKUP_DIR     - Backup directory (default: /backups/agent47)"
        echo "  RETENTION_DAYS - Backup retention in days (default: 7)"
        exit 1
        ;;
esac
