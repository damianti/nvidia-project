#!/bin/bash

# NVIDIA Cloud Platform - Run All Tests Script
# Executes tests for all services (backend and frontend)

# Get the project root directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root to ensure relative paths work
cd "$PROJECT_ROOT"

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track test results
TOTAL_SERVICES=0
PASSED_SERVICES=0
FAILED_SERVICES=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Running All Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to setup venv for a service if it doesn't exist
setup_venv() {
    local service_path=$1
    
    if [ ! -d "${service_path}/venv" ]; then
        echo -e "${YELLOW}  Creating venv...${NC}"
        cd "${service_path}"
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip --quiet
        
        echo -e "${YELLOW}  Installing dependencies...${NC}"
        if [ -f "requirements.txt" ]; then
            # Install core dependencies needed for tests (avoiding problematic ones for Python 3.13)
            pip install fastapi uvicorn "pydantic>=2.5" sqlalchemy pytest pytest-asyncio PyJWT passlib bcrypt python-multipart python-dotenv "email-validator>=2.1" --quiet
            
            # Try to install psycopg2-binary but don't fail if it doesn't work (tests use mocks)
            pip install psycopg2-binary --quiet 2>/dev/null || echo -e "${YELLOW}    ⚠ psycopg2-binary skipped (not critical for tests)${NC}"
            
            # Install additional dependencies for specific services
            if [[ "$service_path" == *"orchestrator"* ]]; then
                pip install docker redis confluent-kafka --quiet 2>/dev/null || true
            fi
            if [[ "$service_path" == *"billing"* ]]; then
                # Billing dependencies are already covered above
                :
            fi
            if [[ "$service_path" == *"api-gateway"* ]]; then
                pip install httpx --quiet 2>/dev/null || true
            fi
        else
            # If no requirements.txt, install minimal test dependencies
            pip install pytest pytest-asyncio --quiet
        fi
        
        deactivate
        cd - > /dev/null
    else
        # Even if venv exists, check if pytest is installed and install missing dependencies
        cd "${service_path}"
        source venv/bin/activate
        if ! python -c "import pytest" 2>/dev/null; then
            echo -e "${YELLOW}  Installing missing dependencies...${NC}"
            if [ -f "requirements.txt" ]; then
                pip install fastapi uvicorn "pydantic>=2.5" sqlalchemy pytest pytest-asyncio PyJWT passlib bcrypt python-multipart python-dotenv "email-validator>=2.1" --quiet
                pip install psycopg2-binary --quiet 2>/dev/null || true
                
                # Install additional dependencies for specific services
                if [[ "$service_path" == *"orchestrator"* ]]; then
                    pip install docker redis confluent-kafka --quiet 2>/dev/null || true
                fi
                if [[ "$service_path" == *"api-gateway"* ]]; then
                    pip install httpx --quiet 2>/dev/null || true
                fi
            else
                pip install pytest pytest-asyncio --quiet
            fi
        fi
        deactivate
        cd "$PROJECT_ROOT"
    fi
}

# Function to run tests for a Python service
run_python_tests() {
    local service_name=$1
    local service_path=$2
    
    echo -e "${YELLOW}Testing ${service_name}...${NC}"
    
    if [ ! -d "${service_path}/tests" ]; then
        echo -e "${YELLOW}  ⚠ No tests directory found, skipping${NC}"
        return 0
    fi
    
    if [ ! -f "${service_path}/pytest.ini" ]; then
        echo -e "${YELLOW}  ⚠ No pytest.ini found, skipping${NC}"
        return 0
    fi
    
    # Setup venv if it doesn't exist
    setup_venv "${service_path}"
    
    cd "${service_path}"
    
    # Activate venv and run tests
    source venv/bin/activate
    if python -m pytest tests/ -v --tb=short 2>&1; then
        deactivate
        echo -e "${GREEN}  ✓ ${service_name} tests passed${NC}"
        ((PASSED_SERVICES++))
        cd "$PROJECT_ROOT"
        return 0
    else
        deactivate
        echo -e "${RED}  ✗ ${service_name} tests failed${NC}"
        ((FAILED_SERVICES++))
        cd "$PROJECT_ROOT"
        return 1
    fi
}

# Function to run tests for the UI (Next.js)
run_ui_tests() {
    local service_path="services/ui"
    
    echo -e "${YELLOW}Testing UI (Next.js)...${NC}"
    
    if [ ! -d "${service_path}" ]; then
        echo -e "${YELLOW}  ⚠ UI directory not found, skipping${NC}"
        return 0
    fi
    
    cd "${service_path}"
    
    # Check if node_modules exists, if not install dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}  Installing dependencies...${NC}"
        npm install
    fi
    
    if npm test -- --passWithNoTests 2>&1; then
        echo -e "${GREEN}  ✓ UI tests passed${NC}"
        ((PASSED_SERVICES++))
        return 0
    else
        echo -e "${RED}  ✗ UI tests failed${NC}"
        ((FAILED_SERVICES++))
        return 1
    fi
}

# Run tests for each Python service
echo -e "${BLUE}Python Services:${NC}"
echo ""

# Auth Service
((TOTAL_SERVICES++))
run_python_tests "Auth Service" "services/auth-service"
cd "$PROJECT_ROOT"

# Orchestrator
((TOTAL_SERVICES++))
run_python_tests "Orchestrator" "services/orchestrator"
cd "$PROJECT_ROOT"

# Load Balancer
((TOTAL_SERVICES++))
run_python_tests "Load Balancer" "services/load-balancer"
cd "$PROJECT_ROOT"

# Billing
((TOTAL_SERVICES++))
run_python_tests "Billing" "services/billing"
cd "$PROJECT_ROOT"

# Service Discovery
((TOTAL_SERVICES++))
run_python_tests "Service Discovery" "services/service-discovery"
cd "$PROJECT_ROOT"

# API Gateway
((TOTAL_SERVICES++))
run_python_tests "API Gateway" "services/api-gateway"
cd "$PROJECT_ROOT"

# Client Workload
((TOTAL_SERVICES++))
run_python_tests "Client Workload" "services/client-workload"
cd "$PROJECT_ROOT"

# UI (Next.js)
echo ""
echo -e "${BLUE}Frontend:${NC}"
echo ""
((TOTAL_SERVICES++))
run_ui_tests
cd - > /dev/null

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Services: ${TOTAL_SERVICES}"
echo -e "${GREEN}Passed: ${PASSED_SERVICES}${NC}"
if [ ${FAILED_SERVICES} -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED_SERVICES}${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: ${FAILED_SERVICES}${NC}"
    exit 0
fi

