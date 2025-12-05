#!/bin/bash

# NVIDIA Cloud Platform - Log Viewer Script
# Easy way to view logs from all services

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Services
SERVICES=(
    "auth-service"
    "orchestrator"
    "api-gateway"
    "load-balancer"
    "service-discovery"
    "billing"
    "client-workload"
)

# Function to show usage
show_usage() {
    echo -e "${BLUE}NVIDIA Cloud Platform - Log Viewer${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "Options:"
    echo "  -a, --all              View logs from all services"
    echo "  -f, --follow           Follow log output (like tail -f)"
    echo "  -n, --lines N          Show last N lines (default: 50)"
    echo "  -e, --errors           Show only ERROR level logs"
    echo "  -w, --warnings         Show only WARNING and ERROR logs"
    echo "  -s, --search PATTERN   Search for pattern in logs"
    echo "  -l, --list             List available services"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 auth-service              # View last 50 lines from auth-service"
    echo "  $0 -f orchestrator           # Follow orchestrator logs"
    echo "  $0 -e --all                  # Show all errors from all services"
    echo "  $0 -s 'error' auth-service   # Search for 'error' in auth-service logs"
    echo "  $0 -n 100 api-gateway        # Show last 100 lines from api-gateway"
    echo ""
}

# Function to get log file path
get_log_file() {
    local service=$1
    echo "logs/${service}/app.log"
}

# Function to check if log file exists
log_exists() {
    local service=$1
    local log_file=$(get_log_file "$service")
    [ -f "$log_file" ]
}

# Function to view logs from a service
view_service_logs() {
    local service=$1
    local lines=${2:-50}
    local follow=$3
    local log_file=$(get_log_file "$service")
    
    if ! log_exists "$service"; then
        echo -e "${YELLOW}⚠ Warning: Log file not found for ${service}${NC}"
        echo -e "   File: ${log_file}"
        echo -e "   The service may not have started yet or no logs have been written."
        return 1
    fi
    
    echo -e "${CYAN}━━━ ${service} ━━━${NC}"
    if [ "$follow" = true ]; then
        tail -f "$log_file"
    else
        tail -n "$lines" "$log_file"
    fi
}

# Function to view all service logs
view_all_logs() {
    local lines=${1:-50}
    local follow=$2
    
    for service in "${SERVICES[@]}"; do
        if log_exists "$service"; then
            view_service_logs "$service" "$lines" false
            echo ""
        fi
    done
}

# Function to filter errors
filter_errors() {
    local service=$1
    local log_file=$(get_log_file "$service")
    
    if ! log_exists "$service"; then
        return 1
    fi
    
    echo -e "${CYAN}━━━ ${service} (ERRORS only) ━━━${NC}"
    grep -i '"level":"ERROR"' "$log_file" 2>/dev/null || echo "No errors found"
}

# Function to filter warnings and errors
filter_warnings() {
    local service=$1
    local log_file=$(get_log_file "$service")
    
    if ! log_exists "$service"; then
        return 1
    fi
    
    echo -e "${CYAN}━━━ ${service} (WARNINGS & ERRORS) ━━━${NC}"
    grep -iE '"level":"(WARNING|ERROR)"' "$log_file" 2>/dev/null || echo "No warnings or errors found"
}

# Function to search in logs
search_logs() {
    local service=$1
    local pattern=$2
    local log_file=$(get_log_file "$service")
    
    if ! log_exists "$service"; then
        return 1
    fi
    
    echo -e "${CYAN}━━━ ${service} (search: '${pattern}') ━━━${NC}"
    grep -i "$pattern" "$log_file" 2>/dev/null || echo "No matches found"
}

# Parse arguments
SERVICE=""
LINES=50
FOLLOW=false
SHOW_ALL=false
SHOW_ERRORS=false
SHOW_WARNINGS=false
SEARCH_PATTERN=""
LIST_SERVICES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            SHOW_ALL=true
            shift
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -e|--errors)
            SHOW_ERRORS=true
            shift
            ;;
        -w|--warnings)
            SHOW_WARNINGS=true
            shift
            ;;
        -s|--search)
            SEARCH_PATTERN="$2"
            shift 2
            ;;
        -l|--list)
            LIST_SERVICES=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
        *)
            SERVICE="$1"
            shift
            ;;
    esac
done

# List services
if [ "$LIST_SERVICES" = true ]; then
    echo -e "${BLUE}Available services:${NC}"
    for service in "${SERVICES[@]}"; do
        if log_exists "$service"; then
            echo -e "  ${GREEN}✓${NC} $service"
        else
            echo -e "  ${YELLOW}○${NC} $service (no logs yet)"
        fi
    done
    exit 0
fi

# Show all logs
if [ "$SHOW_ALL" = true ]; then
    if [ "$SHOW_ERRORS" = true ]; then
        for service in "${SERVICES[@]}"; do
            filter_errors "$service"
            echo ""
        done
    elif [ "$SHOW_WARNINGS" = true ]; then
        for service in "${SERVICES[@]}"; do
            filter_warnings "$service"
            echo ""
        done
    elif [ -n "$SEARCH_PATTERN" ]; then
        for service in "${SERVICES[@]}"; do
            search_logs "$service" "$SEARCH_PATTERN"
            echo ""
        done
    else
        view_all_logs "$LINES" "$FOLLOW"
    fi
    exit 0
fi

# Show specific service logs
if [ -z "$SERVICE" ]; then
    echo -e "${RED}Error: No service specified${NC}"
    echo ""
    show_usage
    exit 1
fi

# Validate service name
VALID_SERVICE=false
for svc in "${SERVICES[@]}"; do
    if [ "$svc" = "$SERVICE" ]; then
        VALID_SERVICE=true
        break
    fi
done

if [ "$VALID_SERVICE" = false ]; then
    echo -e "${RED}Error: Invalid service name: ${SERVICE}${NC}"
    echo ""
    echo -e "${BLUE}Available services:${NC}"
    for svc in "${SERVICES[@]}"; do
        echo "  - $svc"
    done
    exit 1
fi

# Execute based on options
if [ "$SHOW_ERRORS" = true ]; then
    filter_errors "$SERVICE"
elif [ "$SHOW_WARNINGS" = true ]; then
    filter_warnings "$SERVICE"
elif [ -n "$SEARCH_PATTERN" ]; then
    search_logs "$SERVICE" "$SEARCH_PATTERN"
else
    view_service_logs "$SERVICE" "$LINES" "$FOLLOW"
fi
