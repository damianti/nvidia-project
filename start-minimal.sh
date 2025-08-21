#!/bin/bash

# Script de inicio rápido para configuración minimalista
# NVIDIA ScaleUp Hackathon Project

echo "🚀 Iniciando configuración minimalista: Team 1 UI + Team 3 Orchestrator"
echo "=================================================================="

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

# Función para verificar prerrequisitos
check_prerequisites() {
    print_status "Verificando prerrequisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Verificar que Docker esté corriendo
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        exit 1
    fi
    
    print_success "Prerrequisitos verificados"
}

# Función para verificar puertos disponibles
check_ports() {
    print_status "Verificando puertos disponibles..."
    
    local ports=(3001 3003 5432 6379 8082)
    local ports_in_use=()
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            ports_in_use+=($port)
        fi
    done
    
    if [ ${#ports_in_use[@]} -gt 0 ]; then
        print_warning "Los siguientes puertos están en uso: ${ports_in_use[*]}"
        read -p "¿Deseas continuar de todas formas? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Operación cancelada"
            exit 0
        fi
    else
        print_success "Todos los puertos están disponibles"
    fi
}

# Función para detener servicios existentes
stop_existing_services() {
    print_status "Deteniendo servicios existentes..."
    
    # Detener servicios de nvidia si están corriendo
    if docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q .; then
        print_status "Deteniendo contenedores existentes..."
        docker-compose -f docker-compose-minimal.yml down 2>/dev/null || true
        docker stop $(docker ps --filter "name=nvidia-" --format "{{.Names}}") 2>/dev/null || true
    fi
    
    print_success "Servicios existentes detenidos"
}

# Función para iniciar servicios
start_services() {
    print_status "Iniciando servicios..."
    
    # Construir imágenes si es necesario
    print_status "Construyendo imágenes..."
    docker-compose -f docker-compose-minimal.yml build --no-cache
    
    # Iniciar servicios
    print_status "Iniciando contenedores..."
    docker-compose -f docker-compose-minimal.yml up -d
    
    if [ $? -eq 0 ]; then
        print_success "Servicios iniciados correctamente"
    else
        print_error "Error starting services"
        exit 1
    fi
}

# Función para esperar que los servicios estén listos
wait_for_services() {
    print_status "Esperando que los servicios estén listos..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Verificar PostgreSQL
        if docker exec nvidia-postgres-minimal pg_isready -U nvidia_user -d nvidia_cloud &> /dev/null; then
            print_success "PostgreSQL está listo"
            break
        fi
        
        print_status "Intento $attempt/$max_attempts - Esperando servicios..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Services did not start correctly"
        show_logs
        exit 1
    fi
}

# Función para mostrar logs
show_logs() {
    print_status "Mostrando logs de los servicios..."
    echo ""
    
    echo "=== Logs del Orchestrator ==="
    docker logs nvidia-team3-orchestrator --tail 20 2>/dev/null || print_warning "No se pudieron obtener logs del orchestrator"
    echo ""
    
    echo "=== Logs del UI ==="
    docker logs nvidia-team1-ui --tail 20 2>/dev/null || print_warning "No se pudieron obtener logs del UI"
    echo ""
}

# Función para mostrar información de conexión
show_connection_info() {
    echo ""
    echo "🌐 Información de conexión:"
    echo "   UI: http://localhost:3001"
    echo "   Orchestrator API: http://localhost:3003"
    echo "   Adminer (DB): http://localhost:8082"
    echo "   PostgreSQL: localhost:5432"
    echo "   Redis: localhost:6379"
    echo ""
    
    print_success "✅ Configuración minimalista iniciada correctamente!"
    print_status "Puedes acceder al UI en: http://localhost:3001"
    print_status "Puedes probar la API del Orchestrator en: http://localhost:3003"
    print_status "Ejecuta './test-connection.sh' para verificar la conexión"
}

# Función principal
main() {
    echo "🔍 Verificando configuración..."
    
    # Verificar que el archivo docker-compose-minimal.yml existe
    if [ ! -f "docker-compose-minimal.yml" ]; then
        print_error "The docker-compose-minimal.yml file does not exist"
        exit 1
    fi
    
    # Verificar que el script de pruebas existe
    if [ ! -f "test-connection.sh" ]; then
        print_warning "El script test-connection.sh no existe"
    fi
    
    # Ejecutar verificaciones
    check_prerequisites
    check_ports
    stop_existing_services
    start_services
    wait_for_services
    
    # Mostrar información final
    show_connection_info
    
    # Preguntar si ejecutar pruebas
    read -p "¿Deseas ejecutar las pruebas de conexión ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "test-connection.sh" ]; then
            ./test-connection.sh
        else
            print_warning "Script de pruebas no disponible"
        fi
    fi
}

# Ejecutar función principal
main "$@"
