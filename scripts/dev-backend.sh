#!/bin/bash

# Agent47 Backend Development Script
# This script starts the backend server for local development

set -e

echo "🚀 Starting Agent47 Backend for Development..."

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

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    print_error "Please run this script from the Agent47 root directory"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    print_status "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source backend/venv/bin/activate
print_success "Virtual environment activated"

# Install/update dependencies
print_status "Installing dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..
print_success "Dependencies installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f "env.example" ]; then
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

# Check if required services are running
print_status "Checking required services..."

# Check PostgreSQL
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    print_warning "PostgreSQL is not running on localhost:5432"
    print_status "You can start it with: docker-compose up -d postgres"
fi

# Check Redis
if ! redis-cli -h localhost -p 6379 ping &> /dev/null; then
    print_warning "Redis is not running on localhost:6379"
    print_status "You can start it with: docker-compose up -d redis"
fi

# Check Kafka
if ! nc -z localhost 9092 &> /dev/null; then
    print_warning "Kafka is not running on localhost:9092"
    print_status "You can start it with: docker-compose up -d kafka"
fi

# Start the backend server
print_status "Starting Agent47 Backend server..."
print_status "Backend will be available at: http://localhost:8000"
print_status "API documentation at: http://localhost:8000/docs"
print_status "Press Ctrl+C to stop the server"
echo ""

cd backend
python main.py
