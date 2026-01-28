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
    # Prefer Python 3.11 (same as CI), fallback to python3
    PYTHON_CMD="python3"
    if command_exists python3.11; then
        PYTHON_CMD="python3.11"
        echo -e "${YELLOW}  Using Python 3.11 (matching CI)${NC}"
    fi
    
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}  Creating venv with ${PYTHON_CMD}...${NC}"
        $PYTHON_CMD -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install/upgrade dependencies
    echo -e "${YELLOW}  Installing dependencies...${NC}"
    pip install --upgrade pip --quiet > /dev/null 2>&1 || true
    
    # Try to install dependencies
    # Temporarily disable set -e to handle installation errors gracefully
    set +e
    pip install -r requirements-test.txt > /tmp/pip-install-${service_name}.log 2>&1
    pip_exit_code=$?
    set -e
    
    # Show last few lines of output (filtering warnings)
    tail -5 /tmp/pip-install-${service_name}.log | grep -v "WARNING:" || true
    
    # Check if critical dependencies are installed even if pip install failed
    if [ $pip_exit_code -ne 0 ]; then
        # Try to install critical tools directly if they're not available
        if ! python -c "import pytest" 2>/dev/null; then
            echo -e "${YELLOW}  Installing pytest...${NC}"
            pip install pytest pytest-cov pytest-asyncio --quiet > /dev/null 2>&1 || true
        fi
        if ! python -c "import black" 2>/dev/null; then
            echo -e "${YELLOW}  Installing black...${NC}"
            pip install black --quiet > /dev/null 2>&1 || true
        fi
        if ! python -c "import ruff" 2>/dev/null; then
            echo -e "${YELLOW}  Installing ruff...${NC}"
            pip install ruff --quiet > /dev/null 2>&1 || true
        fi
        # Install httpx if needed (required by FastAPI TestClient)
        if ! python -c "import httpx" 2>/dev/null; then
            echo -e "${YELLOW}  Installing httpx...${NC}"
            pip install httpx --quiet > /dev/null 2>&1 || true
        fi
        
        # Check again if critical dependencies are now available
        if python -c "import pytest, black, ruff" 2>/dev/null; then
            echo -e "${YELLOW}  ⚠ Some dependencies failed, but core tools are available${NC}"
            echo -e "${YELLOW}  Continuing with available dependencies...${NC}"
        else
            echo -e "${RED}  ✗ Failed to install critical dependencies${NC}"
            echo -e "${RED}  Last 10 lines of error:${NC}"
            tail -10 /tmp/pip-install-${service_name}.log | grep -E "ERROR|Failed" || tail -10 /tmp/pip-install-${service_name}.log
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
    ruff_output=$(python -m ruff check app/ 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Ruff check passed${NC}"
    else
        echo -e "  ${RED}✗ Ruff check failed${NC}"
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo "$ruff_output" | head -20
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  Fix with: cd services/${service_name} && ruff check app/ --fix${NC}"
        FAILED_CHECKS+=("${service_name}: ruff check failed")
        has_errors=true
    fi
    
    # 2. Check formatting with black
    echo -e "  ${BLUE}Running black check...${NC}"
    black_output=$(python -m black --check app/ 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Black check passed${NC}"
    else
        echo -e "  ${RED}✗ Black check failed${NC}"
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo "$black_output" | grep "would reformat"
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  Fix with: cd services/${service_name} && black app/${NC}"
        FAILED_CHECKS+=("${service_name}: black check failed")
        has_errors=true
    fi
    
    # 3. Run tests
    echo -e "  ${BLUE}Running tests...${NC}"
    # Check if pytest.ini has coverage options and install pytest-cov if needed
    if [ -f "pytest.ini" ] && grep -q "cov" pytest.ini 2>/dev/null; then
        # pytest.ini has coverage config, ensure pytest-cov is installed
        if ! python -c "import pytest_cov" 2>/dev/null; then
            echo -e "${YELLOW}  Installing pytest-cov...${NC}"
            pip install pytest-cov --quiet > /dev/null 2>&1 || true
        fi
        pytest_cmd="python -m pytest tests/ -q"
    else
        pytest_cmd="python -m pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing -q"
    fi
    test_output=$(eval "$pytest_cmd" 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Tests passed${NC}"
    else
        echo -e "  ${RED}✗ Tests failed${NC}"
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo "$test_output" | grep -E "FAILED|ERROR" | head -10
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  Run tests with: cd services/${service_name} && pytest tests/ -v${NC}"
        FAILED_CHECKS+=("${service_name}: tests failed")
        has_errors=true
    fi
    
    deactivate
    cd "$PROJECT_ROOT"
    
    if [ "$has_errors" = true ]; then
        echo ""
        echo -e "${RED}❌ ${service_name} FAILED - See errors above${NC}"
        echo ""
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
    test_output=$(npm test -- --passWithNoTests 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Tests passed${NC}"
    else
        echo -e "  ${RED}✗ Tests failed${NC}"
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo "$test_output" | grep -E "FAIL|Error" | head -10
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  Run tests with: cd services/ui && npm test${NC}"
        FAILED_CHECKS+=("ui: tests failed")
        has_errors=true
    fi
    
    # Run build
    echo -e "  ${BLUE}Running build...${NC}"
    build_output=$(npm run build 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Build passed${NC}"
    else
        echo -e "  ${RED}✗ Build failed${NC}"
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo "$build_output" | grep -E "Error|Failed" | head -10
        echo -e "${RED}════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  Run build with: cd services/ui && npm run build${NC}"
        FAILED_CHECKS+=("ui: build failed")
        has_errors=true
    fi
    
    cd "$PROJECT_ROOT"
    
    if [ "$has_errors" = true ]; then
        echo ""
        echo -e "${RED}❌ UI FAILED - See errors above${NC}"
        echo ""
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
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                         PRE-PUSH CHECK SUMMARY                  ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Total Services Checked: ${TOTAL_SERVICES}"
echo -e "  ${GREEN}✓ Passed: ${PASSED_SERVICES}${NC}"

if [ ${FAILED_SERVICES} -gt 0 ]; then
    echo -e "  ${RED}✗ Failed: ${FAILED_SERVICES}${NC}"
    echo ""
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}                         ❌ PUSH BLOCKED ❌                      ${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${RED}The following checks failed:${NC}"
    echo ""
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "  ${RED}✗ ${check}${NC}"
    done
    echo ""
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Please fix the errors above before pushing to remote.${NC}"
    echo -e "${YELLOW}See the detailed error output above for specific files and issues.${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
else
    echo -e "  ${GREEN}✗ Failed: ${FAILED_SERVICES}${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                    ✅ ALL CHECKS PASSED ✅                     ${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Safe to push to remote!${NC}"
    echo ""
    exit 0
fi

