#!/bin/bash

# Script to verify all critical services are up and running
# Usage: ./scripts/verify-services.sh

set -e

echo "🔍 Verifying Agent47 Services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "Checking $service_name... "
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not Running${NC}"
        return 1
    fi
}

# Check Redis
check_service "Redis" "redis-cli -h localhost -p 6379 ping"

# Check Zookeeper
check_service "Zookeeper" "echo ruok | nc localhost 2181 | grep imok"

# Check Kafka
check_service "Kafka" "kafka-topics --bootstrap-server localhost:9092 --list"

# Check ChromaDB
check_service "ChromaDB" "curl -f http://localhost:8009/api/v1/heartbeat"

# Check Backend API
check_service "Backend API" "curl -f http://localhost:8000/health"

echo ""
echo "✅ Service verification complete!"

