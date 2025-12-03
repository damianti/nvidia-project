#!/bin/bash

# NVIDIA Cloud Platform - Service Health Check Script
# Verifies the health status of all services

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service URLs
declare -A SERVICES=(
    ["UI"]="http://localhost:3000"
    ["API Gateway"]="http://localhost:8080"
    ["Orchestrator"]="http://localhost:3003"
    ["Load Balancer"]="http://localhost:3004"
    ["Service Discovery"]="http://localhost:3006"
    ["Billing"]="http://localhost:3007"
    ["Client Workload"]="http://localhost:3008"
)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Service Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

all_healthy=true

for service in "${!SERVICES[@]}"; do
    url="${SERVICES[$service]}"
    echo -n "Checking ${service}... "
    
    if curl -s -f "${url}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}Some services are unhealthy. Check logs with: docker-compose logs${NC}"
    exit 1
fi

