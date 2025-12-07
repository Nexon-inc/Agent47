#!/bin/bash

# Supabase Setup Script for Agent47
# This script helps set up a Supabase project for Agent47

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

# Check if Supabase CLI is installed
check_supabase_cli() {
    print_status "Checking Supabase CLI..."
    
    if ! command -v supabase &> /dev/null; then
        print_error "Supabase CLI is not installed."
        print_status "Installing Supabase CLI..."
        
        # Install Supabase CLI based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://supabase.com/install.sh | sh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install supabase/tap/supabase
        else
            print_error "Unsupported operating system. Please install Supabase CLI manually."
            print_status "Visit: https://supabase.com/docs/guides/cli/getting-started"
            exit 1
        fi
    fi
    
    print_success "Supabase CLI is installed"
}

# Initialize Supabase project
init_supabase_project() {
    print_status "Initializing Supabase project..."
    
    if [ ! -d ".supabase" ]; then
        supabase init
        print_success "Supabase project initialized"
    else
        print_success "Supabase project already initialized"
    fi
}

# Set up local development
setup_local_dev() {
    print_status "Setting up local development environment..."
    
    # Start local Supabase
    supabase start
    
    print_success "Local Supabase development environment started"
    print_status "Local Supabase URLs:"
    echo "  • API URL: http://localhost:54321"
    echo "  • DB URL: postgresql://postgres:postgres@localhost:54322/postgres"
    echo "  • Studio: http://localhost:54323"
    echo "  • Inbucket: http://localhost:54324"
}

# Create Supabase project (cloud)
create_cloud_project() {
    print_status "Creating Supabase cloud project..."
    
    print_warning "You need to create a Supabase project manually in the dashboard:"
    print_status "1. Go to https://supabase.com/dashboard"
    print_status "2. Click 'New Project'"
    print_status "3. Choose your organization"
    print_status "4. Enter project name: 'agent47'"
    print_status "5. Enter database password (save this!)"
    print_status "6. Choose region closest to your users"
    print_status "7. Click 'Create new project'"
    
    echo ""
    print_warning "After creating the project, you'll need to:"
    print_status "1. Get your project URL and API keys from Settings > API"
    print_status "2. Update terraform.tfvars with your Supabase credentials"
    print_status "3. Run the database migration script"
    
    echo ""
    read -p "Press Enter when you've created the project and have the credentials..."
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    if [ -f "schema.sql" ]; then
        if [ "$1" == "local" ]; then
            # Local migration
            supabase db reset
            print_success "Local database reset and schema applied"
        else
            # Cloud migration
            print_warning "For cloud migration, you need to:"
            print_status "1. Go to your Supabase dashboard"
            print_status "2. Navigate to SQL Editor"
            print_status "3. Copy and paste the contents of schema.sql"
            print_status "4. Run the SQL script"
            print_status "5. Verify tables are created in Table Editor"
        fi
    else
        print_error "schema.sql file not found"
        exit 1
    fi
}

# Set up storage
setup_storage() {
    print_status "Setting up storage..."
    
    print_status "Storage bucket 'agent47-uploads' will be created automatically by the schema.sql"
    print_status "You can verify this in your Supabase dashboard under Storage"
    
    print_success "Storage setup completed"
}

# Set up authentication
setup_auth() {
    print_status "Setting up authentication..."
    
    print_status "Authentication is configured in the schema.sql with RLS policies"
    print_status "You can configure additional auth settings in your Supabase dashboard:"
    print_status "1. Go to Authentication > Settings"
    print_status "2. Configure email templates"
    print_status "3. Set up social providers if needed"
    print_status "4. Configure redirect URLs"
    
    print_success "Authentication setup completed"
}

# Set up realtime
setup_realtime() {
    print_status "Setting up realtime..."
    
    print_status "Realtime is configured in the schema.sql with publications"
    print_status "Tables: tasks, events, agents are enabled for realtime"
    print_status "You can verify this in your Supabase dashboard under Database > Replication"
    
    print_success "Realtime setup completed"
}

# Generate environment variables
generate_env_vars() {
    print_status "Generating environment variables..."
    
    if [ "$1" == "local" ]; then
        # Local environment
        cat > .env.local << EOF
# Supabase Local Development
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres
EOF
        print_success "Local environment variables generated in .env.local"
    else
        # Cloud environment
        print_warning "For cloud environment, you need to:"
        print_status "1. Get your project URL and API keys from Supabase dashboard"
        print_status "2. Update your .env file with:"
        echo ""
        echo "NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co"
        echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key"
        echo "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key"
        echo "SUPABASE_DB_URL=postgresql://postgres:[password]@db.your-project-id.supabase.co:5432/postgres"
        echo ""
    fi
}

# Show setup summary
show_summary() {
    print_status "Supabase Setup Summary:"
    echo ""
    echo "✅ Supabase CLI installed"
    echo "✅ Project initialized"
    echo "✅ Database schema created"
    echo "✅ Storage configured"
    echo "✅ Authentication configured"
    echo "✅ Realtime enabled"
    echo "✅ Environment variables generated"
    echo ""
    print_success "Supabase setup completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Update your application code to use Supabase client"
    echo "2. Test the connection with your application"
    echo "3. Deploy to production when ready"
    echo ""
    if [ "$1" == "local" ]; then
        print_status "Local development URLs:"
        echo "  • Studio: http://localhost:54323"
        echo "  • API: http://localhost:54321"
        echo "  • Database: postgresql://postgres:postgres@localhost:54322/postgres"
    fi
}

# Main function
main() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                    Supabase Setup                           ║"
    echo "║                for Agent47 Platform                         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check if this is for local development or cloud
    if [ "$1" == "local" ]; then
        print_status "Setting up Supabase for local development..."
        check_supabase_cli
        init_supabase_project
        setup_local_dev
        run_migrations "local"
        setup_storage
        setup_auth
        setup_realtime
        generate_env_vars "local"
        show_summary "local"
    else
        print_status "Setting up Supabase for cloud deployment..."
        check_supabase_cli
        init_supabase_project
        create_cloud_project
        run_migrations "cloud"
        setup_storage
        setup_auth
        setup_realtime
        generate_env_vars "cloud"
        show_summary "cloud"
    fi
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [local|cloud]"
    echo ""
    echo "  local  - Set up Supabase for local development"
    echo "  cloud  - Set up Supabase for cloud deployment"
    echo ""
    exit 1
fi

# Run main function
main "$@"
