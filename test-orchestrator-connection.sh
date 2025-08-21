#!/bin/bash

# Script para probar la conexión del Team 3 Orchestrator con su base de datos
# NVIDIA ScaleUp Hackathon Project

echo "🔍 Probando conexión del Team 3 Orchestrator con su base de datos"
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

# Función para probar conexión a PostgreSQL del Orchestrator
test_orchestrator_postgres() {
    print_status "Probando conexión a PostgreSQL del Orchestrator..."
    
    if docker exec nvidia-postgres-orchestrator pg_isready -U postgres -d orchestrator > /dev/null 2>&1; then
        print_success "PostgreSQL del Orchestrator está accesible"
        return 0
    else
        print_error "Orchestrator PostgreSQL is not accessible"
        return 1
    fi
}

# Función para probar conexión a Redis del Orchestrator
test_orchestrator_redis() {
    print_status "Probando conexión a Redis del Orchestrator..."
    
    if docker exec nvidia-redis-orchestrator redis-cli ping > /dev/null 2>&1; then
        print_success "Redis del Orchestrator está accesible"
        return 0
    else
        print_error "Orchestrator Redis is not accessible"
        return 1
    fi
}

# Función para verificar tablas del Orchestrator
test_orchestrator_tables() {
    print_status "Verificando tablas específicas del Orchestrator..."
    
    # Verificar tabla users
    local user_count=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
    if [ "$user_count" -ge 0 ]; then
        print_success "Tabla users existe con $user_count registros"
    else
        print_error "Table users does not exist"
        return 1
    fi
    
    # Verificar tabla images
    local image_count=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -t -c "SELECT COUNT(*) FROM images;" 2>/dev/null | tr -d ' ')
    if [ "$image_count" -ge 0 ]; then
        print_success "Tabla images existe con $image_count registros"
    else
        print_error "Table images does not exist"
        return 1
    fi
    
    # Verificar tabla containers
    local container_count=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -t -c "SELECT COUNT(*) FROM containers;" 2>/dev/null | tr -d ' ')
    if [ "$container_count" -ge 0 ]; then
        print_success "Tabla containers existe con $container_count registros"
    else
        print_error "Table containers does not exist"
        return 1
    fi
    
    # Verificar tabla billings
    local billing_count=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -t -c "SELECT COUNT(*) FROM billings;" 2>/dev/null | tr -d ' ')
    if [ "$billing_count" -ge 0 ]; then
        print_success "Tabla billings existe con $billing_count registros"
    else
        print_error "Table billings does not exist"
        return 1
    fi
}

# Función para probar operaciones específicas del Orchestrator
test_orchestrator_operations() {
    print_status "Probando operaciones específicas del Orchestrator..."
    
    # Probar inserción de usuario
    local insert_user=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "INSERT INTO users (username, email, password) VALUES ('test_orchestrator', 'test@orchestrator.com', 'password123') ON CONFLICT DO NOTHING;" 2>&1)
    if echo "$insert_user" | grep -q "INSERT"; then
        print_success "Inserción de usuario exitosa"
    else
        print_warning "User already exists or insertion error"
    fi
    
    # Probar inserción de imagen
    local insert_image=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "INSERT INTO images (name, tag, min_instances, max_instances, cpu_limit, memory_limit, status, user_id) VALUES ('test-image', 'latest', 1, 3, '0.5', '512m', 'registered', 1) ON CONFLICT DO NOTHING;" 2>&1)
    if echo "$insert_image" | grep -q "INSERT"; then
        print_success "Inserción de imagen exitosa"
    else
        print_warning "Image already exists or insertion error"
    fi
    
    # Probar inserción de contenedor
    local insert_container=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "INSERT INTO containers (container_id, name, port, status, cpu_usage, memory_usage, image_id) VALUES ('test-container-456', 'test-container', 8080, 'running', '0.2', '256m', 1) ON CONFLICT DO NOTHING;" 2>&1)
    if echo "$insert_container" | grep -q "INSERT"; then
        print_success "Inserción de contenedor exitosa"
    else
        print_warning "Container already exists or insertion error"
    fi
    
    # Probar inserción de billing
    local insert_billing=$(docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "INSERT INTO billings (user_id, amount) VALUES (1, 25.75) ON CONFLICT DO NOTHING;" 2>&1)
    if echo "$insert_billing" | grep -q "INSERT"; then
        print_success "Inserción de billing exitosa"
    else
        print_warning "Billing already exists or insertion error"
    fi
}

# Función para mostrar datos del Orchestrator
show_orchestrator_data() {
    print_status "Mostrando datos del Orchestrator..."
    
    echo ""
    echo "👥 Usuarios:"
    docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "SELECT id, username, email FROM users;" 2>/dev/null
    
    echo ""
    echo "🖼️ Imágenes:"
    docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "SELECT id, name, tag, cpu_limit, memory_limit, status FROM images;" 2>/dev/null
    
    echo ""
    echo "📦 Contenedores:"
    docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "SELECT id, container_id, name, port, status, cpu_usage, memory_usage FROM containers;" 2>/dev/null
    
    echo ""
    echo "💰 Billing:"
    docker exec nvidia-postgres-orchestrator psql -U postgres -d orchestrator -c "SELECT id, user_id, amount, created_at FROM billings;" 2>/dev/null
}

# Función para probar Adminer del Orchestrator
test_orchestrator_adminer() {
    print_status "Probando acceso a Adminer del Orchestrator..."
    
    if curl -s -f http://localhost:8083 > /dev/null 2>&1; then
        print_success "Adminer del Orchestrator está accesible en http://localhost:8083"
        return 0
    else
        print_error "Orchestrator Adminer is not accessible"
        return 1
    fi
}

# Función para mostrar información de conexión del Orchestrator
show_orchestrator_connection_info() {
    echo ""
    echo "🌐 Información de conexión del Orchestrator:"
    echo "   PostgreSQL: localhost:5433"
    echo "   Redis: localhost:6380"
    echo "   Adminer: http://localhost:8083"
    echo "   Orchestrator API: http://localhost:3003"
    echo ""
    echo "📊 Credenciales de base de datos del Orchestrator:"
    echo "   Base de datos: orchestrator"
    echo "   Usuario: postgres"
    echo "   Contraseña: postgres"
    echo "   Host: localhost"
    echo "   Puerto: 5433"
    echo ""
    echo "🔧 Comandos útiles para el Orchestrator:"
    echo "   Conectar a PostgreSQL: docker exec -it nvidia-postgres-orchestrator psql -U postgres -d orchestrator"
    echo "   Conectar a Redis: docker exec -it nvidia-redis-orchestrator redis-cli"
    echo "   Ver logs PostgreSQL: docker logs nvidia-postgres-orchestrator"
    echo "   Ver logs Redis: docker logs nvidia-redis-orchestrator"
    echo "   Ver logs Orchestrator: docker logs nvidia-team3-orchestrator"
    echo ""
}

# Función principal
main() {
    echo "🔍 Verificando estado de los servicios del Orchestrator..."
    
    # Verificar que los contenedores del Orchestrator estén corriendo
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-postgres-orchestrator"; then
        print_error "Orchestrator PostgreSQL is not running"
        print_status "Ejecuta: docker-compose -f docker-compose-orchestrator.yml up -d"
        exit 1
    fi
    
    if ! docker ps --filter "name=nvidia-" --format "{{.Names}}" | grep -q "nvidia-redis-orchestrator"; then
        print_error "Orchestrator Redis is not running"
        exit 1
    fi
    
    print_success "Todos los servicios del Orchestrator están corriendo"
    
    # Probar conexiones
    test_orchestrator_postgres
    test_orchestrator_redis
    test_orchestrator_adminer
    
    # Probar tablas específicas
    test_orchestrator_tables
    
    # Probar operaciones
    test_orchestrator_operations
    
    # Mostrar datos
    show_orchestrator_data
    
    # Mostrar información
    show_orchestrator_connection_info
    
    print_success "✅ Pruebas de conexión del Orchestrator completadas!"
    print_status "El Team 3 Orchestrator está listo para conectarse con el Team 1 UI"
    print_status "La base de datos tiene las tablas específicas: users, images, containers, billings"
}

# Ejecutar función principal
main "$@"
