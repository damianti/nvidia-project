#!/bin/bash

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is ready"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to test Redis connection
test_redis() {
    print_status "Testing Redis connection..."
    
    if docker exec nvidia-redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis is running and responding"
        return 0
    else
        print_error "Redis is not responding"
        return 1
    fi
}

# Function to test service discovery
test_service_discovery() {
    print_status "Testing Service Discovery..."
    
    # Check if services are registered
    local orchestrator_count=$(docker exec nvidia-redis redis-cli smembers "services:orchestrator" | wc -l)
    local load_balancer_count=$(docker exec nvidia-redis redis-cli smembers "services:load_balancer" | wc -l)
    
    if [ $orchestrator_count -gt 0 ]; then
        print_success "Orchestrator service registered in service discovery"
    else
        print_error "Orchestrator service not found in service discovery"
        return 1
    fi
    
    if [ $load_balancer_count -gt 0 ]; then
        print_success "Load Balancer service registered in service discovery"
    else
        print_error "Load Balancer service not found in service discovery"
        return 1
    fi
    
    return 0
}

# Function to test message queue
test_message_queue() {
    print_status "Testing Message Queue..."
    
    # Test sending a health check message
    local response=$(curl -s -X POST "http://localhost:3002/api/load-balancer/containers/create" \
        -H "Content-Type: application/json" \
        -d '{
            "image_name": "nginx",
            "tag": "latest",
            "min_instances": 1,
            "max_instances": 2
        }')
    
    if echo "$response" | grep -q "message_id"; then
        local message_id=$(echo "$response" | grep -o '"message_id":"[^"]*"' | cut -d'"' -f4)
        print_success "Message sent successfully: $message_id"
        
        # Wait a bit for processing
        sleep 5
        
        # Check message status
        local status_response=$(curl -s "http://localhost:3002/api/load-balancer/messages/$message_id/status")
        if echo "$status_response" | grep -q "status"; then
            local status=$(echo "$status_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            print_success "Message status: $status"
        else
            print_warning "Could not get message status"
        fi
        
        return 0
    else
        print_error "Failed to send message"
        return 1
    fi
}

# Function to test load balancer endpoints
test_load_balancer() {
    print_status "Testing Load Balancer endpoints..."
    
    # Test health endpoint
    if curl -s "http://localhost:3002/api/load-balancer/health" | grep -q "healthy"; then
        print_success "Load Balancer health check passed"
    else
        print_error "Load Balancer health check failed"
        return 1
    fi
    
    # Test services endpoint
    if curl -s "http://localhost:3002/api/load-balancer/services" | grep -q "available_services"; then
        print_success "Load Balancer services endpoint working"
    else
        print_error "Load Balancer services endpoint failed"
        return 1
    fi
    
    # Test stats endpoint
    if curl -s "http://localhost:3002/api/load-balancer/stats" | grep -q "load_balancer"; then
        print_success "Load Balancer stats endpoint working"
    else
        print_error "Load Balancer stats endpoint failed"
        return 1
    fi
    
    return 0
}

# Function to test orchestrator endpoints
test_orchestrator() {
    print_status "Testing Orchestrator endpoints..."
    
    # Test health endpoint
    if curl -s "http://localhost:3003/health" | grep -q "healthy"; then
        print_success "Orchestrator health check passed"
    else
        print_error "Orchestrator health check failed"
        return 1
    fi
    
    # Test status endpoint
    if curl -s "http://localhost:3003/api/orchestrator/status" | grep -q "service_discovery"; then
        print_success "Orchestrator status endpoint working"
    else
        print_error "Orchestrator status endpoint failed"
        return 1
    fi
    
    return 0
}

# Function to show service logs
show_logs() {
    print_status "Recent logs from services:"
    echo "=== Load Balancer Logs ==="
    docker logs nvidia-load-balancer --tail 10
    echo ""
    echo "=== Orchestrator Logs ==="
    docker logs nvidia-orchestrator --tail 10
    echo ""
    echo "=== Redis Logs ==="
    docker logs nvidia-redis --tail 5
}

# Main test function
main() {
    print_status "Starting Service Discovery and Message Queue tests..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running"
        exit 1
    fi
    
    # Check if services are running
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-redis"; then
        print_error "Redis container is not running"
        print_status "Please start the services with: docker-compose -f docker-compose-service-discovery.yml up -d"
        exit 1
    fi
    
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-load-balancer"; then
        print_error "Load Balancer container is not running"
        exit 1
    fi
    
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-orchestrator"; then
        print_error "Orchestrator container is not running"
        exit 1
    fi
    
    # Wait for services to be ready
    wait_for_service "Redis" "http://localhost:6379" || exit 1
    wait_for_service "Load Balancer" "http://localhost:3002/api/load-balancer/health" || exit 1
    wait_for_service "Orchestrator" "http://localhost:3003/health" || exit 1
    
    # Run tests
    local all_tests_passed=true
    
    test_redis || all_tests_passed=false
    test_service_discovery || all_tests_passed=false
    test_load_balancer || all_tests_passed=false
    test_orchestrator || all_tests_passed=false
    test_message_queue || all_tests_passed=false
    
    # Show results
    echo ""
    if [ "$all_tests_passed" = true ]; then
        print_success "All tests passed! Service Discovery and Message Queue are working correctly."
        echo ""
        print_status "Service URLs:"
        echo "  - Load Balancer: http://localhost:3002"
        echo "  - Orchestrator: http://localhost:3003"
        echo "  - Redis: localhost:6379"
        echo "  - Adminer: http://localhost:8083"
        echo ""
        print_status "Load Balancer API endpoints:"
        echo "  - Health: http://localhost:3002/api/load-balancer/health"
        echo "  - Services: http://localhost:3002/api/load-balancer/services"
        echo "  - Stats: http://localhost:3002/api/load-balancer/stats"
        echo "  - Create Container: POST http://localhost:3002/api/load-balancer/containers/create"
    else
        print_error "Some tests failed. Check the logs below:"
        show_logs
        exit 1
    fi
}

# Run main function
main "$@"
