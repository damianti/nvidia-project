# 🚀 Configuración Minimalista - Team 1 UI + Team 3 Orchestrator

## 📋 Descripción

Esta configuración permite probar la conexión básica entre el **Team 1 (UI)** y el **Team 3 (Orchestrator)** sin ejecutar todo el sistema completo. Es ideal para desarrollo incremental y pruebas de integración.

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Team 1 UI     │◄──►│   PostgreSQL    │◄──►│   Team 3        │
│   (React)       │    │   Database      │    │   Orchestrator  │
│   Port: 3001    │    │   Port: 5432    │    │   Port: 3003    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis         │    │   Adminer       │    │   Docker        │
│   Cache         │    │   DB Admin      │    │   Engine        │
│   Port: 6379    │    │   Port: 8082    │    │   (Host)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Inicio Rápido

### 1. Verificar Prerrequisitos

```bash
# Verificar que Docker esté instalado y funcionando
docker --version
docker-compose --version

# Verificar que los puertos estén disponibles
lsof -i :3001,3003,5432,6379,8082
```

### 2. Iniciar los Servicios

```bash
# Iniciar solo los servicios necesarios
docker-compose -f docker-compose-minimal.yml up -d

# Verificar que todos los servicios estén corriendo
docker-compose -f docker-compose-minimal.yml ps
```

### 3. Probar la Conexión

```bash
# Ejecutar el script de pruebas automáticas
./test-connection.sh
```

### 4. Acceder a los Servicios

- **UI**: http://localhost:3001
- **Orchestrator API**: http://localhost:3003
- **Adminer (DB)**: http://localhost:8082
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Configuración

### Variables de Entorno

El archivo `docker-compose-minimal.yml` incluye las siguientes configuraciones:

```yaml
# Team 1 UI
REACT_APP_API_URL: http://localhost:3003
REACT_APP_ORCHESTRATOR_URL: http://team3-orchestrator:3000
REACT_APP_MOCK_MODE: false

# Team 3 Orchestrator
DATABASE_URL: postgresql://nvidia_user:nvidia_password@postgres:5432/nvidia_cloud
REDIS_URL: redis://redis:6379
DOCKER_HOST: unix:///var/run/docker.sock
```

### Base de Datos

La base de datos se inicializa automáticamente con:

- Tablas para usuarios, contenedores, servicios, uso y facturación
- Índices para optimizar consultas
- Datos de prueba para desarrollo

### Redes

Todos los servicios están conectados a la red `nvidia-minimal-network` para comunicación interna.

## 🧪 Pruebas

### Pruebas Automáticas

El script `test-connection.sh` realiza las siguientes verificaciones:

1. **Estado de Contenedores**: Verifica que todos los servicios estén corriendo
2. **Health Checks**: Prueba endpoints de salud de cada servicio
3. **Comunicación**: Verifica que el UI pueda comunicarse con el Orchestrator
4. **API Endpoints**: Prueba endpoints básicos de la API

### Manual Testing

#### 1. Probar Health Check del Orchestrator

```bash
curl http://localhost:3003/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T10:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "docker": "connected"
  }
}
```

#### 2. Probar Lista de Contenedores

```bash
curl http://localhost:3003/api/containers
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "containers": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 0,
      "pages": 0
    }
  }
}
```

#### 3. Probar UI

Abrir http://localhost:3001 en el navegador y verificar que:

- La página se carga correctamente
- No errors in browser console
- Los componentes se renderizan correctamente

## 🔍 Monitoreo

### Logs de Servicios

```bash
# Ver logs del Orchestrator
docker logs nvidia-team3-orchestrator -f

# Ver logs del UI
docker logs nvidia-team1-ui -f

# Ver logs de PostgreSQL
docker logs nvidia-postgres-minimal -f
```

### Estado de Contenedores

```bash
# Ver estado de todos los contenedores
docker ps --filter "name=nvidia-"

# Ver uso de recursos
docker stats --filter "name=nvidia-"
```

### Base de Datos

Acceder a Adminer en http://localhost:8082:

- **Sistema**: PostgreSQL
- **Servidor**: postgres
- **Usuario**: nvidia_user
- **Contraseña**: nvidia_password
- **Base de datos**: nvidia_cloud

## 🛠️ Desarrollo

### Modificar el UI

```bash
# Los cambios en ./teams/team1-ui se reflejan automáticamente
# thanks to the mounted volume
```

### Modificar el Orchestrator

```bash
# Los cambios en ./teams/team3-orchestrator se reflejan automáticamente
# Reiniciar el contenedor si es necesario
docker-compose -f docker-compose-minimal.yml restart team3-orchestrator
```

### Agregar Nuevos Endpoints

1. Agregar el endpoint en el Orchestrator
2. Update API documentation
3. Probar con curl o Postman
4. Integrar en el UI

## 🚨 Troubleshooting

### Common Issues

#### 1. Puerto ya en uso

```bash
# Verificar qué está usando el puerto
lsof -i :3001
lsof -i :3003

# Detener el proceso o cambiar el puerto en docker-compose-minimal.yml
```

#### 2. Base de datos no se conecta

```bash
# Verificar que PostgreSQL esté corriendo
docker logs nvidia-postgres-minimal

# Verificar la conexión
docker exec -it nvidia-postgres-minimal psql -U nvidia_user -d nvidia_cloud
```

#### 3. UI no se carga

```bash
# Verificar logs del UI
docker logs nvidia-team1-ui

# Verificar que el Orchestrator esté disponible
curl http://localhost:3003/health
```

#### 4. Docker socket no accesible

```bash
# Verificar permisos del socket de Docker
ls -la /var/run/docker.sock

# Agregar el usuario al grupo docker si es necesario
sudo usermod -aG docker $USER
```

### Comandos Útiles

```bash
# Reiniciar todos los servicios
docker-compose -f docker-compose-minimal.yml restart

# Reconstruir imágenes
docker-compose -f docker-compose-minimal.yml build --no-cache

# Clean volumes (WARNING! This deletes the database)
docker-compose -f docker-compose-minimal.yml down -v

# Ver logs de todos los servicios
docker-compose -f docker-compose-minimal.yml logs -f
```

## 📊 Métricas

### Endpoints de Métricas

- **Orchestrator Metrics**: http://localhost:3003/metrics
- **Health Status**: http://localhost:3003/health

### Monitoreo de Recursos

```bash
# Ver uso de CPU y memoria
docker stats --filter "name=nvidia-"

# Ver uso de disco
docker system df
```

## 🔄 Próximos Pasos

Una vez que la conexión básica entre UI y Orchestrator esté funcionando, puedes:

1. **Agregar el Load Balancer** (Team 2)
2. **Implementar el Billing Service** (Team 6)
3. **Agregar el Client Workload** (Team 7)
4. **Configurar monitoreo completo** (Prometheus + Grafana)

## 📞 Soporte

For specific issues:

1. Revisar los logs de los servicios
2. Ejecutar el script de pruebas: `./test-connection.sh`
3. Check each team's documentation
4. Consultar con el equipo de desarrollo

---

**Note**: This configuration is for development and testing. For production, it's recommended to use the complete configuration with all services.
