#!/bin/bash

# NVIDIA Cloud Platform - Pre-Push Lint Checks
# Runs ruff and black only — fast lint gate before pushing.
# Full test suite runs in GitHub Actions CI.

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
echo -e "${BLUE}Pre-Push Lint Checks${NC}"
echo -e "${BLUE}(Tests run in GitHub Actions CI)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Python services to lint (matching GitHub Actions matrix)
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

# Function to lint a Python service (ruff + black only)
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

    # Check if requirements-test.txt exists (contains ruff and black)
    if [ ! -f "requirements-test.txt" ]; then
        echo -e "${RED}  ✗ requirements-test.txt not found${NC}"
        FAILED_CHECKS+=("${service_name}: requirements-test.txt not found")
        ((FAILED_SERVICES++))
        cd "$PROJECT_ROOT"
        return 1
    fi

    # Setup Python environment
    PYTHON_CMD="python3"
    if command_exists python3.11; then
        PYTHON_CMD="python3.11"
    fi

    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}  Creating venv...${NC}"
        $PYTHON_CMD -m venv venv
    fi

    source venv/bin/activate

    # Install/upgrade lint dependencies from pinned requirements
    pip install --upgrade pip --quiet > /dev/null 2>&1 || true
    pip install -r requirements-test.txt --quiet > /dev/null 2>&1 || true

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

    deactivate
    cd "$PROJECT_ROOT"

    if [ "$has_errors" = true ]; then
        echo ""
        echo -e "${RED}❌ ${service_name} FAILED - See errors above${NC}"
        echo ""
        ((FAILED_SERVICES++))
        return 1
    else
        echo -e "${GREEN}  ✓ Lint passed for ${service_name}${NC}"
        ((PASSED_SERVICES++))
        return 0
    fi
}

# Lint all Python services
for service in "${PYTHON_SERVICES[@]}"; do
    ((TOTAL_SERVICES++))
    check_python_service "$service"
    echo ""
done

# Summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                      PRE-PUSH LINT SUMMARY                      ${NC}"
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
    echo -e "${YELLOW}Fix the lint errors above, then push again.${NC}"
    echo -e "${YELLOW}Tests will run automatically in GitHub Actions CI.${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
else
    echo -e "  ${GREEN}✗ Failed: 0${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                    ✅ ALL LINT CHECKS PASSED ✅                 ${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Pushing to remote. Full test suite will run in GitHub Actions CI.${NC}"
    echo ""
    exit 0
fi
