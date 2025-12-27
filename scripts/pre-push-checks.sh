#!/bin/bash

# NVIDIA Cloud Platform - Pre-Push Checks
# Replicates GitHub Actions workflow locally to catch errors before pushing

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

# Track results
TOTAL_SERVICES=0
PASSED_SERVICES=0
FAILED_SERVICES=0
FAILED_CHECKS=()

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Pre-Push Checks (CI Simulation)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Python services to test (matching GitHub Actions matrix)
PYTHON_SERVICES=(
    "orchestrator"
    "api-gateway"
    "load-balancer"
    "auth-service"
    "billing"
    "service-discovery"
)

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python service
check_python_service() {
    local service_name=$1
    local service_path="services/${service_name}"
    local has_errors=false
    
    echo -e "${YELLOW}Checking ${service_name}...${NC}"
    
    # Check if service directory exists
    if [ ! -d "$service_path" ]; then
        echo -e "${RED}  ✗ Service directory not found: ${service_path}${NC}"
        FAILED_CHECKS+=("${service_name}: directory not found")
        ((FAILED_SERVICES++))
        return 1
    fi
    
    cd "$service_path"
    
    # Check if requirements-test.txt exists
    if [ ! -f "requirements-test.txt" ]; then
        echo -e "${RED}  ✗ requirements-test.txt not found${NC}"
        FAILED_CHECKS+=("${service_name}: requirements-test.txt not found")
        has_errors=true
    fi
    
    # Setup Python environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}  Creating venv...${NC}"
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install/upgrade dependencies
    echo -e "${YELLOW}  Installing dependencies...${NC}"
    pip install --upgrade pip --quiet > /dev/null 2>&1
    
    # Try to install dependencies, but be tolerant of optional dependencies
    if ! pip install -r requirements-test.txt --quiet 2>&1 | tee /tmp/pip-install-${service_name}.log; then
        # Check if it's a critical error or just optional dependencies
        if grep -q "ERROR: Failed building wheel\|Failed to build" /tmp/pip-install-${service_name}.log; then
            echo -e "${YELLOW}  ⚠ Some dependencies failed to install (may be optional)${NC}"
            echo -e "${YELLOW}  Attempting to continue with available dependencies...${NC}"
            # Try to install core dependencies manually
            pip install pytest pytest-asyncio pytest-cov black ruff --quiet > /dev/null 2>&1 || true
        else
            echo -e "${RED}  ✗ Failed to install dependencies${NC}"
            cat /tmp/pip-install-${service_name}.log | tail -10
            FAILED_CHECKS+=("${service_name}: dependency installation failed")
            has_errors=true
            deactivate
            cd "$PROJECT_ROOT"
            return 1
        fi
    fi
    
    # Check if ruff is available
    if ! command_exists ruff && ! python -m ruff --version > /dev/null 2>&1; then
        echo -e "${YELLOW}  Installing ruff...${NC}"
        pip install ruff --quiet > /dev/null 2>&1
    fi
    
    # Check if black is available
    if ! command_exists black && ! python -m black --version > /dev/null 2>&1; then
        echo -e "${YELLOW}  Installing black...${NC}"
        pip install black --quiet > /dev/null 2>&1
    fi
    
    # 1. Lint with ruff
    echo -e "  ${BLUE}Running ruff check...${NC}"
    if python -m ruff check app/ 2>&1; then
        echo -e "  ${GREEN}✓ Ruff check passed${NC}"
    else
        echo -e "  ${RED}✗ Ruff check failed${NC}"
        FAILED_CHECKS+=("${service_name}: ruff check failed")
        has_errors=true
    fi
    
    # 2. Check formatting with black
    echo -e "  ${BLUE}Running black check...${NC}"
    if python -m black --check app/ 2>&1; then
        echo -e "  ${GREEN}✓ Black check passed${NC}"
    else
        echo -e "  ${RED}✗ Black check failed (run 'black app/' to fix)${NC}"
        FAILED_CHECKS+=("${service_name}: black check failed")
        has_errors=true
    fi
    
    # 3. Run tests
    echo -e "  ${BLUE}Running tests...${NC}"
    if python -m pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing -q 2>&1; then
        echo -e "  ${GREEN}✓ Tests passed${NC}"
    else
        echo -e "  ${RED}✗ Tests failed${NC}"
        FAILED_CHECKS+=("${service_name}: tests failed")
        has_errors=true
    fi
    
    deactivate
    cd "$PROJECT_ROOT"
    
    if [ "$has_errors" = true ]; then
        ((FAILED_SERVICES++))
        return 1
    else
        echo -e "${GREEN}  ✓ All checks passed for ${service_name}${NC}"
        ((PASSED_SERVICES++))
        return 0
    fi
}

# Function to check frontend
check_frontend() {
    local service_path="services/ui"
    local has_errors=false
    
    echo -e "${YELLOW}Checking Frontend (UI)...${NC}"
    
    # Check if service directory exists
    if [ ! -d "$service_path" ]; then
        echo -e "${RED}  ✗ Service directory not found: ${service_path}${NC}"
        FAILED_CHECKS+=("ui: directory not found")
        ((FAILED_SERVICES++))
        return 1
    fi
    
    cd "$service_path"
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        echo -e "${RED}  ✗ package.json not found${NC}"
        FAILED_CHECKS+=("ui: package.json not found")
        has_errors=true
        cd "$PROJECT_ROOT"
        return 1
    fi
    
    # Check if node_modules exists, if not install
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}  Installing dependencies...${NC}"
        npm ci > /dev/null 2>&1 || {
            echo -e "${RED}  ✗ Failed to install dependencies${NC}"
            FAILED_CHECKS+=("ui: dependency installation failed")
            has_errors=true
            cd "$PROJECT_ROOT"
            return 1
        }
    fi
    
    # Run tests
    echo -e "  ${BLUE}Running tests...${NC}"
    if npm test -- --passWithNoTests > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Tests passed${NC}"
    else
        echo -e "  ${RED}✗ Tests failed${NC}"
        FAILED_CHECKS+=("ui: tests failed")
        has_errors=true
    fi
    
    # Run build
    echo -e "  ${BLUE}Running build...${NC}"
    if npm run build > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Build passed${NC}"
    else
        echo -e "  ${RED}✗ Build failed${NC}"
        FAILED_CHECKS+=("ui: build failed")
        has_errors=true
    fi
    
    cd "$PROJECT_ROOT"
    
    if [ "$has_errors" = true ]; then
        ((FAILED_SERVICES++))
        return 1
    else
        echo -e "${GREEN}  ✓ All checks passed for UI${NC}"
        ((PASSED_SERVICES++))
        return 0
    fi
}

# Check all Python services
for service in "${PYTHON_SERVICES[@]}"; do
    ((TOTAL_SERVICES++))
    check_python_service "$service"
    echo ""
done

# Check frontend
((TOTAL_SERVICES++))
check_frontend
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Services: ${TOTAL_SERVICES}"
echo -e "${GREEN}Passed: ${PASSED_SERVICES}${NC}"

if [ ${FAILED_SERVICES} -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED_SERVICES}${NC}"
    echo ""
    echo -e "${RED}Failed Checks:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "  ${RED}✗ ${check}${NC}"
    done
    echo ""
    echo -e "${YELLOW}Fix the errors above before pushing.${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: ${FAILED_SERVICES}${NC}"
    echo ""
    echo -e "${GREEN}✓ All checks passed! Safe to push.${NC}"
    exit 0
fi

