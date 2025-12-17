#!/bin/bash

# NVIDIA Cloud Platform - Demo Script
# This script demonstrates the complete system flow

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
UI_URL="http://localhost:3000"
API_GATEWAY_URL="http://localhost:8080"
ORCHESTRATOR_URL="http://localhost:3003"
LOAD_BALANCER_URL="http://localhost:3004"
SERVICE_DISCOVERY_URL="http://localhost:3006"
BILLING_URL="http://localhost:3007"
CLIENT_WORKLOAD_URL="http://localhost:3008"

# Default credentials
DEFAULT_EMAIL="example@gmail.com"
DEFAULT_PASSWORD="example123"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NVIDIA Cloud Platform - Demo Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a service is healthy
check_service() {
    local service_name=$1
    local url=$2
    
    echo -e "${YELLOW}Checking ${service_name}...${NC}"
    if curl -s -f "${url}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${service_name} is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ ${service_name} is not responding${NC}"
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}Waiting for ${service_name} to be ready...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "${url}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ${service_name} is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo -e "${RED}✗ ${service_name} failed to start after ${max_attempts} attempts${NC}"
    return 1
}

# Step 1: Check Docker Compose
echo -e "${BLUE}Step 1: Checking Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"
echo ""

# Step 2: Check if .env exists
echo -e "${BLUE}Step 2: Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}⚠ .env file not found. Copying from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file from .env.example${NC}"
        echo -e "${YELLOW}⚠ Please review .env file and update values if needed${NC}"
    else
        echo -e "${YELLOW}⚠ .env file not found. Using default values...${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi
echo ""

# Step 3: Start services
echo -e "${BLUE}Step 3: Starting services...${NC}"
echo -e "${YELLOW}Running: docker-compose up -d --build${NC}"
docker-compose up -d --build
echo ""

# Step 4: Wait for services to be ready
echo -e "${BLUE}Step 4: Waiting for services to be ready...${NC}"
echo -e "${YELLOW}This may take a few minutes on first run...${NC}"
echo ""
wait_for_service "UI" "${UI_URL}"
wait_for_service "API Gateway" "${API_GATEWAY_URL}"
wait_for_service "Orchestrator" "${ORCHESTRATOR_URL}"
wait_for_service "Load Balancer" "${LOAD_BALANCER_URL}"
wait_for_service "Service Discovery" "${SERVICE_DISCOVERY_URL}"
wait_for_service "Billing" "${BILLING_URL}"
wait_for_service "Client Workload" "${CLIENT_WORKLOAD_URL}"
echo ""

# Step 5: Check all services health
echo -e "${BLUE}Step 5: Verifying all services health...${NC}"
check_service "UI" "${UI_URL}"
check_service "API Gateway" "${API_GATEWAY_URL}"
check_service "Orchestrator" "${ORCHESTRATOR_URL}"
check_service "Load Balancer" "${LOAD_BALANCER_URL}"
check_service "Service Discovery" "${SERVICE_DISCOVERY_URL}"
check_service "Billing" "${BILLING_URL}"
check_service "Client Workload" "${CLIENT_WORKLOAD_URL}"
echo ""

# Step 6: Display system status
echo -e "${BLUE}Step 6: System Status${NC}"
echo -e "${GREEN}All services are running!${NC}"
echo ""
echo "Service URLs:"
echo "  - UI: ${UI_URL}"
echo "  - API Gateway: ${API_GATEWAY_URL}"
echo "  - Orchestrator: ${ORCHESTRATOR_URL}"
echo "  - Load Balancer: ${LOAD_BALANCER_URL}"
echo "  - Service Discovery: ${SERVICE_DISCOVERY_URL}"
echo "  - Billing: ${BILLING_URL}"
echo "  - Client Workload: ${CLIENT_WORKLOAD_URL}"
echo ""
echo "Default credentials:"
echo "  - Email: ${DEFAULT_EMAIL}"
echo "  - Password: ${DEFAULT_PASSWORD}"
echo ""

# Step 7: Demo instructions
echo -e "${BLUE}Step 7: Demo Instructions${NC}"
echo ""
echo "To complete the demo, follow these steps:"
echo ""
echo "1. Open the UI in your browser:"
echo "   ${GREEN}${UI_URL}${NC}"
echo ""
echo "2. Login with default credentials:"
echo "   Email: ${DEFAULT_EMAIL}"
echo "   Password: ${DEFAULT_PASSWORD}"
echo ""
echo "3. Create an Image:"
echo "   - Go to 'Images' page"
echo "   - Click 'Create Image'"
echo "   - Enter image name (e.g., 'nginx')"
echo "   - Enter tag (e.g., 'latest')"
echo "   - Enter app hostname (e.g., 'youtube.com')"
echo ""
echo "4. Create Containers:"
echo "   - Go to 'Containers' page"
echo "   - Select the image you created"
echo "   - Click 'Create Container'"
echo "   - Create 2-3 containers"
echo ""
echo "5. Test Routing:"
echo "   - Use the Load Balancer to route requests:"
echo "   ${YELLOW}curl -X POST ${LOAD_BALANCER_URL}/route \\${NC}"
echo "   ${YELLOW}  -H 'Content-Type: application/json' \\${NC}"
echo "   ${YELLOW}  -d '{\"app_hostname\": \"youtube.com\"}'${NC}"
echo ""
echo "6. View Billing:"
echo "   - Go to 'Billing' page in the UI"
echo "   - View billing summaries per image"
echo ""
echo "7. Test Client Workload:"
echo "   - Start a workload test:"
echo "   ${YELLOW}curl -X POST ${CLIENT_WORKLOAD_URL}/workload/start \\${NC}"
echo "   ${YELLOW}  -H 'Content-Type: application/json' \\${NC}"
echo "   ${YELLOW}  -d '{\"duration_seconds\": 30, \"requests_per_second\": 5}'${NC}"
echo ""
echo "8. Monitor Services:"
echo "   - Kafka UI: http://localhost:8081"
echo "   - Consul UI: http://localhost:8500"
echo "   - View logs: docker-compose logs -f <service-name>"
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}Demo script completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Open the UI and explore the dashboard"
echo "2. Create images and containers through the UI"
echo "3. Test the load balancing functionality"
echo "4. Check billing reports"
echo ""
echo -e "${YELLOW}For help, check the README.md or run: ./scripts/check-services.sh${NC}"
echo ""

