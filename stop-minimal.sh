#!/bin/bash

# Script para detener y limpiar la configuración minimalista
# NVIDIA ScaleUp Hackathon Project

echo "🛑 Deteniendo configuración minimalista: Team 1 UI + Team 3 Orchestrator"
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

# Función para detener servicios
stop_services() {
    print_status "Deteniendo servicios..."
    
    if [ -f "docker-compose-minimal.yml" ]; then
        docker-compose -f docker-compose-minimal.yml down
        print_success "Servicios detenidos"
    else
        print_warning "Archivo docker-compose-minimal.yml no encontrado"
    fi
}

# Función para limpiar contenedores
cleanup_containers() {
    print_status "Limpiando contenedores..."
    
    # Detener contenedores de nvidia si están corriendo
    local containers=$(docker ps --filter "name=nvidia-" --format "{{.Names}}")
    
    if [ -n "$containers" ]; then
        echo "$containers" | xargs docker stop
        print_success "Contenedores detenidos"
    else
        print_status "No hay contenedores de nvidia corriendo"
    fi
    
    # Eliminar contenedores de nvidia
    local containers=$(docker ps -a --filter "name=nvidia-" --format "{{.Names}}")
    
    if [ -n "$containers" ]; then
        echo "$containers" | xargs docker rm
        print_success "Contenedores eliminados"
    else
        print_status "No hay contenedores de nvidia para eliminar"
    fi
}

# Función para limpiar volúmenes (opcional)
cleanup_volumes() {
    read -p "¿Deseas eliminar también los volúmenes de datos? (Esto borrará la base de datos) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Eliminando volúmenes..."
        
        # Eliminar volúmenes específicos
        docker volume rm nvidia-project_postgres_data 2>/dev/null || true
        docker volume rm nvidia-project_redis_data 2>/dev/null || true
        
        # Eliminar volúmenes huérfanos
        docker volume prune -f
        
        print_success "Volúmenes eliminados"
    else
        print_status "Volúmenes preservados"
    fi
}

# Función para limpiar imágenes (opcional)
cleanup_images() {
    read -p "¿Deseas eliminar también las imágenes de Docker? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Eliminando imágenes..."
        
        # Eliminar imágenes de nvidia
        docker images --filter "reference=nvidia*" --format "{{.ID}}" | xargs docker rmi 2>/dev/null || true
        
        # Eliminar imágenes huérfanas
        docker image prune -f
        
        print_success "Imágenes eliminadas"
    else
        print_status "Imágenes preservadas"
    fi
}

# Función para limpiar redes (opcional)
cleanup_networks() {
    read -p "¿Deseas eliminar también las redes de Docker? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Eliminando redes..."
        
        # Eliminar red de nvidia
        docker network rm nvidia-project_nvidia-minimal-network 2>/dev/null || true
        
        # Eliminar redes huérfanas
        docker network prune -f
        
        print_success "Redes eliminadas"
    else
        print_status "Redes preservadas"
    fi
}

# Función para mostrar estado final
show_final_status() {
    print_status "Estado final del sistema:"
    echo ""
    
    echo "=== Contenedores corriendo ==="
    docker ps --filter "name=nvidia-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    echo "=== Contenedores detenidos ==="
    docker ps -a --filter "name=nvidia-" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    
    echo "=== Volúmenes ==="
    docker volume ls --filter "name=nvidia"
    echo ""
    
    echo "=== Redes ==="
    docker network ls --filter "name=nvidia"
    echo ""
}

# Función principal
main() {
    echo "🔍 Verificando estado actual..."
    
    # Mostrar estado inicial
    print_status "Estado inicial:"
    docker ps --filter "name=nvidia-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || print_status "No hay contenedores corriendo"
    echo ""
    
    # Detener servicios
    stop_services
    
    # Limpiar contenedores
    cleanup_containers
    
    # Preguntar por limpieza adicional
    echo ""
    print_status "Opciones de limpieza adicional:"
    echo "1. Eliminar volúmenes (borra datos de la base de datos)"
    echo "2. Eliminar imágenes de Docker"
    echo "3. Eliminar redes de Docker"
    echo "4. Limpieza completa (todo lo anterior)"
    echo "5. Solo detener servicios (preservar todo)"
    echo ""
    
    read -p "Selecciona una opción (1-5): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            cleanup_volumes
            ;;
        2)
            cleanup_images
            ;;
        3)
            cleanup_networks
            ;;
        4)
            cleanup_volumes
            cleanup_images
            cleanup_networks
            ;;
        5)
            print_status "Solo deteniendo servicios"
            ;;
        *)
            print_status "Opción no válida, solo deteniendo servicios"
            ;;
    esac
    
    # Mostrar estado final
    show_final_status
    
    print_success "✅ Limpieza completada!"
    print_status "Para reiniciar, ejecuta: ./start-minimal.sh"
}

# Ejecutar función principal
main "$@"
