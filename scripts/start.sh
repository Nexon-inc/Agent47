#!/bin/bash

# Agent47 Startup Script
# This script starts the entire Agent47 platform

set -e

echo "🚀 Starting Agent47 Multi-Agent AI Platform..."

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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f env.example ]; then
            cp env.example .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your actual configuration values"
        else
            print_error "env.example file not found. Cannot create .env file."
            exit 1
        fi
    else
        print_success ".env file found"
    fi
}

# Verify environment configuration
verify_env() {
    print_status "Verifying environment configuration..."
    
    if [ -f backend/verify_env_setup.py ]; then
        cd backend
        python3 verify_env_setup.py
        local exit_code=$?
        cd ..
        
        if [ $exit_code -ne 0 ]; then
            print_error "Environment verification failed. Please fix the issues and try again."
            print_warning "You can run 'python3 backend/verify_env_setup.py' to see detailed issues."
            exit 1
        fi
        print_success "Environment verification passed"
    else
        print_warning "Environment verification script not found, skipping verification"
    fi
}

# Check if required services are available
check_services() {
    print_status "Checking required services..."
    
    # Check if ports are available
    local ports=(5432 6379 9092 8000 3000)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port is already in use. This might cause conflicts."
        fi
    done
}

# Start services with Docker Compose
start_services() {
    print_status "Starting services with Docker Compose..."
    
    # Pull latest images
    print_status "Pulling latest Docker images..."
    docker-compose pull
    
    # Build custom images
    print_status "Building custom Docker images..."
    docker-compose build
    
    # Start services
    print_status "Starting all services..."
    docker-compose up -d
    
    print_success "All services started successfully!"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U agent47 -d agent47_db; do sleep 2; done'
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    timeout 30 bash -c 'until docker-compose exec -T redis redis-cli ping; do sleep 2; done'
    print_success "Redis is ready"
    
    # Wait for Kafka
    print_status "Waiting for Kafka..."
    timeout 60 bash -c 'until docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list; do sleep 5; done'
    print_success "Kafka is ready"
    
    # Wait for ChromaDB
    print_status "Waiting for ChromaDB..."
    timeout 30 bash -c 'until curl -f http://localhost:8009/api/v1/heartbeat; do sleep 2; done'
    print_success "ChromaDB is ready"
    
    # Wait for Backend
    print_status "Waiting for Backend API..."
    timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
    print_success "Backend API is ready"
    
    # Wait for Frontend
    print_status "Waiting for Frontend..."
    timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 5; done'
    print_success "Frontend is ready"
}

# Show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo ""
    print_success "🎉 Agent47 Platform is now running!"
    echo ""
    echo "📱 Access Points:"
    echo "  • Frontend:     http://localhost:3000"
    echo "  • Backend API:  http://localhost:8000"
    echo "  • API Docs:     http://localhost:8000/docs"
    echo "  • Grafana:      http://localhost:3001 (admin/admin)"
    echo "  • Prometheus:   http://localhost:9090"
    echo ""
    echo "🔧 Management Commands:"
    echo "  • View logs:    docker-compose logs -f [service]"
    echo "  • Stop all:     docker-compose down"
    echo "  • Restart:      docker-compose restart [service]"
    echo "  • Scale:        docker-compose up -d --scale backend=3"
    echo ""
}

# Main execution
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
    echo "║              Multi-Agent AI Platform                         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_docker
    check_env
    verify_env
    check_services
    start_services
    wait_for_services
    show_status
}

# Handle script interruption
trap 'print_error "Startup interrupted. Use docker-compose down to stop services."; exit 1' INT

# Run main function
main "$@"
