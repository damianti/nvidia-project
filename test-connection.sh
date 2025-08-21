#!/bin/bash

# Script para probar la conexión entre Team 1 UI y Team 3 Orchestrator
# NVIDIA ScaleUp Hackathon Project

echo "🚀 Iniciando pruebas de conexión entre Team 1 UI y Team 3 Orchestrator"
echo "================================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para esperar que un servicio esté listo
wait_for_service() {
    local service_name=$1
    local service_url=$2
    local max_attempts=30
    local attempt=1

    print_status "Esperando que $service_name esté listo..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$service_url" > /dev/null 2>&1; then
            print_success "$service_name está listo!"
            return 0
        fi
        
        print_status "Intento $attempt/$max_attempts - $service_name no está listo aún..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name could not connect after $max_attempts attempts"
    return 1
}

# Función para probar endpoint de health check
test_health_endpoint() {
    local service_name=$1
    local health_url=$2
    
    print_status "Probando health check de $service_name..."
    
    if curl -s -f "$health_url" > /dev/null 2>&1; then
        print_success "Health check de $service_name: OK"
        return 0
    else
        print_error "Health check of $service_name: FAILED"
        return 1
    fi
}

# Función para probar API endpoints
test_api_endpoint() {
    local endpoint_name=$1
    local endpoint_url=$2
    local expected_status=$3
    
    print_status "Probando endpoint: $endpoint_name"
    
    response=$(curl -s -w "%{http_code}" "$endpoint_url" -o /dev/null)
    
    if [ "$response" = "$expected_status" ]; then
        print_success "Endpoint $endpoint_name: OK (Status: $response)"
        return 0
    else
        print_error "Endpoint $endpoint_name: FAILED (Expected: $expected_status, Got: $response)"
        return 1
    fi
}

# Función para probar conexión entre servicios
test_service_communication() {
    print_status "Probando comunicación entre servicios..."
    
    # Probar que el UI puede comunicarse con el Orchestrator
    local orchestrator_url="http://localhost:3003"
    local ui_url="http://localhost:3001"
    
    # Verificar que el orchestrator responde
    if curl -s -f "$orchestrator_url/health" > /dev/null 2>&1; then
        print_success "Orchestrator responde correctamente"
        
        # Probar endpoint de containers
        if test_api_endpoint "Containers List" "$orchestrator_url/api/containers" "200"; then
            print_success "Comunicación UI -> Orchestrator: OK"
        else
            print_warning "Endpoint de containers no disponible aún"
        fi
    else
        print_error "Orchestrator not responding"
        return 1
    fi
}

# Función para mostrar logs de los servicios
show_service_logs() {
    print_status "Mostrando logs de los servicios..."
    echo ""
    
    echo "=== Logs del Orchestrator ==="
    docker logs nvidia-team3-orchestrator --tail 10 2>/dev/null || print_warning "No se pudieron obtener logs del orchestrator"
    echo ""
    
    echo "=== Logs del UI ==="
    docker logs nvidia-team1-ui --tail 10 2>/dev/null || print_warning "No se pudieron obtener logs del UI"
    echo ""
}

# Función para mostrar estado de los contenedores
show_container_status() {
    print_status "Estado de los contenedores:"
    docker ps --filter "name=nvidia-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
}

# Función principal
main() {
    echo "🔍 Verificando estado de los contenedores..."
    show_container_status
    
    # Esperar a que los servicios estén listos
    if ! wait_for_service "PostgreSQL" "http://localhost:5432"; then
        print_error "PostgreSQL is not available"
        exit 1
    fi
    
    if ! wait_for_service "Redis" "http://localhost:6379"; then
        print_error "Redis is not available"
        exit 1
    fi
    
    if ! wait_for_service "Orchestrator" "http://localhost:3003/health"; then
        print_error "Orchestrator is not available"
        show_service_logs
        exit 1
    fi
    
    if ! wait_for_service "UI" "http://localhost:3001"; then
        print_error "UI is not available"
        show_service_logs
        exit 1
    fi
    
    # Probar health checks
    test_health_endpoint "Orchestrator" "http://localhost:3003/health"
    test_health_endpoint "UI" "http://localhost:3001"
    
    # Probar comunicación entre servicios
    test_service_communication
    
    # Mostrar información de conexión
    echo ""
    echo "🌐 Información de conexión:"
    echo "   UI: http://localhost:3001"
    echo "   Orchestrator API: http://localhost:3003"
    echo "   Adminer (DB): http://localhost:8082"
    echo "   PostgreSQL: localhost:5432"
    echo "   Redis: localhost:6379"
    echo ""
    
    print_success "✅ Pruebas de conexión completadas!"
    print_status "Puedes acceder al UI en: http://localhost:3001"
    print_status "Puedes probar la API del Orchestrator en: http://localhost:3003"
}

# Ejecutar función principal
main "$@"
