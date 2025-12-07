#!/bin/bash

# Agent47 Frontend Development Script
# This script starts the frontend server for local development

set -e

echo "🚀 Starting Agent47 Frontend for Development..."

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
if [ ! -f "frontend/package.json" ]; then
    print_error "Please run this script from the Agent47 root directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Node.js 18+ is required. Current version: $NODE_VERSION"
    exit 1
fi

print_success "Node.js $NODE_VERSION detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    print_status "Installing dependencies..."
    cd frontend
    npm install
    cd ..
    print_success "Dependencies installed"
else
    print_status "Dependencies already installed"
fi

# Check if .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    print_warning ".env.local file not found. Creating from template..."
    if [ -f "frontend/.env.example" ]; then
        cp frontend/.env.example frontend/.env.local
        print_success "Created .env.local file from template"
        print_warning "Please edit frontend/.env.local file with your actual configuration values"
    else
        print_warning "No .env.example found. Using default configuration"
    fi
else
    print_success ".env.local file found"
fi

# Check if backend is running
print_status "Checking backend connection..."
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "Backend is running on http://localhost:8000"
else
    print_warning "Backend is not running on http://localhost:8000"
    print_status "Make sure to start the backend server first with: ./scripts/dev-backend.sh"
fi

# Start the frontend server
print_status "Starting Agent47 Frontend server..."
print_status "Frontend will be available at: http://localhost:3000"
print_status "Press Ctrl+C to stop the server"
echo ""

cd frontend
npm run dev
