#!/bin/bash

# NVIDIA Cloud Platform - Setup Virtual Environments
# Creates venv for each Python service if they don't exist

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setting up Virtual Environments${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# List of Python services
SERVICES=(
    "auth-service"
    "orchestrator"
    "load-balancer"
    "billing"
    "service-discovery"
    "api-gateway"
    "client-workload"
)

for service in "${SERVICES[@]}"; do
    service_path="services/${service}"
    
    if [ ! -d "${service_path}" ]; then
        echo -e "${YELLOW}⚠ ${service} directory not found, skipping${NC}"
        continue
    fi
    
    if [ -d "${service_path}/venv" ]; then
        echo -e "${GREEN}✓ ${service} venv already exists${NC}"
        continue
    fi
    
    echo -e "${YELLOW}Creating venv for ${service}...${NC}"
    cd "${service_path}"
    
    # Create venv
    python3 -m venv venv
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    
    if [ -f "requirements.txt" ]; then
        echo -e "  Installing dependencies from requirements.txt..."
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    deactivate
    cd - > /dev/null
    
    echo -e "${GREEN}✓ ${service} venv created${NC}"
done

echo ""
echo -e "${GREEN}All virtual environments are ready!${NC}"
echo ""
echo "To activate a service's venv:"
echo "  cd services/<service-name>"
echo "  source venv/bin/activate"

