#!/bin/bash

# Agent47 Frontend Setup Script
# This script sets up the frontend for local development

set -e

echo "🎨 Setting up Agent47 Frontend..."

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
    print_status "Download from: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Node.js 18+ is required. Current version: $NODE_VERSION"
    print_status "Please upgrade Node.js from: https://nodejs.org/"
    exit 1
fi

print_success "Node.js $NODE_VERSION detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

NPM_VERSION=$(npm -v)
print_success "npm $NPM_VERSION detected"

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    print_error "package.json not found in frontend directory"
    exit 1
fi

print_status "Found package.json with $(cat package.json | grep -o '"dependencies"' | wc -l) dependencies"

# Install dependencies
print_status "Installing dependencies..."
if npm install; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    print_warning ".env.local file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        print_success "Created .env.local file from template"
        print_warning "Please edit .env.local file with your actual configuration values"
    else
        print_warning "No .env.example found. Creating basic .env.local..."
        cat > .env.local << EOF
# Agent47 Frontend Environment Variables
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_DEBUG=true
NODE_ENV=development

# AI Services
NEXT_PUBLIC_CHUTES_API_URL=https://api.chutes.ai
NEXT_PUBLIC_GROK_API_URL=http://localhost:8001

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_VOICE=true
EOF
        print_success "Created basic .env.local file"
    fi
else
    print_success ".env.local file already exists"
fi

# Check if backend is running
print_status "Checking backend connection..."
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "Backend is running on http://localhost:8000"
else
    print_warning "Backend is not running on http://localhost:8000"
    print_status "Make sure to start the backend server first with: ./scripts/dev-backend.sh"
fi

# Run type check
print_status "Running TypeScript type check..."
if npx tsc --noEmit; then
    print_success "TypeScript type check passed"
else
    print_warning "TypeScript type check failed. Please fix type errors."
fi

# Run linting
print_status "Running ESLint..."
if npm run lint; then
    print_success "ESLint check passed"
else
    print_warning "ESLint found issues. Please fix them."
fi

# Go back to root directory
cd ..

print_success "Frontend setup completed!"
echo ""
print_status "Next steps:"
echo "1. Edit frontend/.env.local with your configuration"
echo "2. Start the backend: ./scripts/dev-backend.sh"
echo "3. Start the frontend: ./scripts/dev-frontend.sh"
echo "4. Open http://localhost:3000 in your browser"
echo ""
print_status "Available commands:"
echo "  ./scripts/dev-frontend.sh    # Start frontend development server"
echo "  ./scripts/dev-backend.sh     # Start backend development server"
echo "  ./scripts/start.sh           # Start full platform with Docker"
echo ""
print_success "Happy coding! 🎉"
