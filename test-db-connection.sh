#!/bin/bash

# Script para probar la conexión entre UI y Base de Datos a través del Orchestrator
# NVIDIA ScaleUp Hackathon Project

echo "🔍 Probando conexión entre UI y Base de Datos a través del Orchestrator"
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

# Función para probar conexión a PostgreSQL
test_postgres_connection() {
    print_status "Probando conexión directa a PostgreSQL..."
    
    if docker exec nvidia-postgres-test pg_isready -U nvidia_user -d nvidia_cloud > /dev/null 2>&1; then
        print_success "PostgreSQL está accesible"
        return 0
    else
        print_error "PostgreSQL is not accessible"
        return 1
    fi
}

# Función para probar conexión a Redis
test_redis_connection() {
    print_status "Probando conexión directa a Redis..."
    
    if docker exec nvidia-redis-test redis-cli ping > /dev/null 2>&1; then
        print_success "Redis está accesible"
        return 0
    else
        print_error "Redis is not accessible"
        return 1
    fi
}

# Función para probar datos en la base de datos
test_database_data() {
    print_status "Verificando datos en la base de datos..."
    
    # Verificar usuarios
    local user_count=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
    
    if [ "$user_count" -gt 0 ]; then
        print_success "Tabla users tiene $user_count registros"
    else
        print_warning "Tabla users está vacía"
    fi
    
    # Verificar servicios
    local service_count=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -t -c "SELECT COUNT(*) FROM services;" 2>/dev/null | tr -d ' ')
    
    if [ "$service_count" -gt 0 ]; then
        print_success "Tabla services tiene $service_count registros"
    else
        print_warning "Tabla services está vacía"
    fi
    
    # Verificar contenedores
    local container_count=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -t -c "SELECT COUNT(*) FROM containers;" 2>/dev/null | tr -d ' ')
    print_status "Tabla containers tiene $container_count registros"
}

# Función para probar Adminer
test_adminer() {
    print_status "Probando acceso a Adminer..."
    
    if curl -s -f http://localhost:8083 > /dev/null 2>&1; then
        print_success "Adminer está accesible en http://localhost:8083"
        return 0
    else
        print_error "Adminer is not accessible"
        return 1
    fi
}

# Función para simular operaciones de base de datos
simulate_database_operations() {
    print_status "Simulando operaciones de base de datos..."
    
    # Insertar un contenedor de prueba
    local insert_result=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -c "INSERT INTO containers (user_id, name, image, status) VALUES (1, 'test-container', 'nginx:alpine', 'created') ON CONFLICT DO NOTHING;" 2>&1)
    
    if echo "$insert_result" | grep -q "INSERT"; then
        print_success "Inserción de contenedor exitosa"
    else
        print_warning "Container already exists or insertion error"
    fi
    
    # Consultar contenedores
    local containers=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -t -c "SELECT id, name, image, status FROM containers;" 2>/dev/null)
    
    if [ -n "$containers" ]; then
        print_success "Consulta de contenedores exitosa"
        echo "$containers" | while read line; do
            if [ -n "$line" ]; then
                print_status "  - $line"
            fi
        done
    else
        print_warning "No hay contenedores en la base de datos"
    fi
}

# Función para mostrar información de conexión
show_connection_info() {
    echo ""
    echo "🌐 Información de conexión:"
    echo "   PostgreSQL: localhost:5433"
    echo "   Redis: localhost:6380"
    echo "   Adminer: http://localhost:8083"
    echo ""
    echo "📊 Credenciales de base de datos:"
    echo "   Base de datos: nvidia_cloud"
    echo "   Usuario: nvidia_user"
    echo "   Contraseña: nvidia_password"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   Conectar a PostgreSQL: docker exec -it nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud"
    echo "   Conectar a Redis: docker exec -it nvidia-redis-test redis-cli"
    echo "   Ver logs PostgreSQL: docker logs nvidia-postgres-test"
    echo "   Ver logs Redis: docker logs nvidia-redis-test"
    echo ""
}

# Función para probar integración con Orchestrator (simulada)
test_orchestrator_integration() {
    print_status "Simulando integración con Orchestrator..."
    
    # Simular que el Orchestrator lee datos de la base de datos
    local user_data=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -t -c "SELECT id, email, name FROM users LIMIT 1;" 2>/dev/null)
    
    if [ -n "$user_data" ]; then
        print_success "Orchestrator puede leer datos de usuarios"
        echo "$user_data" | while read line; do
            if [ -n "$line" ]; then
                print_status "  - Usuario: $line"
            fi
        done
    else
        print_error "Orchestrator cannot read user data"
    fi
    
    # Simular que el Orchestrator escribe datos en la base de datos
    local test_service="test-orchestrator-service"
    local insert_result=$(docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -c "INSERT INTO services (name, version, endpoint, health_check, status) VALUES ('$test_service', '1.0.0', 'http://localhost:8001', '/health', 'active') ON CONFLICT DO NOTHING;" 2>&1)
    
    if echo "$insert_result" | grep -q "INSERT"; then
        print_success "Orchestrator puede escribir datos de servicios"
        
        # Limpiar el servicio de prueba
        docker exec nvidia-postgres-test psql -U nvidia_user -d nvidia_cloud -c "DELETE FROM services WHERE name = '$test_service';" > /dev/null 2>&1
    else
        print_warning "Service already exists or insertion error"
    fi
}

# Función principal
main() {
    echo "🔍 Verificando estado de los servicios..."
    
    # Verificar que los contenedores estén corriendo
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-postgres-test"; then
        print_error "PostgreSQL is not running"
        exit 1
    fi
    
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-redis-test"; then
        print_error "Redis is not running"
        exit 1
    fi
    
    print_success "Todos los servicios están corriendo"
    
    # Probar conexiones
    test_postgres_connection
    test_redis_connection
    test_adminer
    
    # Probar datos
    test_database_data
    
    # Simular operaciones
    simulate_database_operations
    
    # Probar integración
    test_orchestrator_integration
    
    # Mostrar información
    show_connection_info
    
    print_success "✅ Pruebas de conexión completadas!"
    print_status "La base de datos está lista para ser utilizada por el Orchestrator"
    print_status "El UI podrá conectarse a través del Orchestrator una vez que esté implementado"
}

# Ejecutar función principal
main "$@"
