# 🚀 Inicio Rápido - Prueba de Conexión UI + Orchestrator

## 📋 Resumen

Esta configuración te permite probar la conexión básica entre el **Team 1 (UI)** y el **Team 3 (Orchestrator)** sin ejecutar todo el sistema completo.

## ⚡ Comandos Rápidos

### 1. Iniciar todo el sistema
```bash
./start-minimal.sh
```

### 2. Probar la conexión
```bash
./test-connection.sh
```

### 3. Detener y limpiar
```bash
./stop-minimal.sh
```

## 🌐 URLs de Acceso

Una vez iniciado, puedes acceder a:

- **UI**: http://localhost:3001
- **Orchestrator API**: http://localhost:3003
- **Adminer (DB)**: http://localhost:8082

## 🧪 Manual Testing

### Health Check del Orchestrator
```bash
curl http://localhost:3003/health
```

### Lista de Contenedores
```bash
curl http://localhost:3003/api/containers
```

### Verificar UI
Abrir http://localhost:3001 en el navegador

## 📁 Important Files

- `docker-compose-minimal.yml` - Configuración de servicios
- `start-minimal.sh` - Script de inicio automático
- `test-connection.sh` - Script de pruebas
- `stop-minimal.sh` - Script de limpieza
- `README-minimal-setup.md` - Complete documentation

## 🔧 Servicios Incluidos

- **PostgreSQL** (Base de datos)
- **Redis** (Cache)
- **Team 1 UI** (React)
- **Team 3 Orchestrator** (Python/FastAPI)
- **Adminer** (Administrador de DB)

## 🚨 Troubleshooting

### Si los puertos están ocupados:
```bash
lsof -i :3001,3003,5432,6379,8082
```

### If there are Docker permission issues:
```bash
sudo usermod -aG docker $USER
```

### Para ver logs:
```bash
docker logs nvidia-team3-orchestrator
docker logs nvidia-team1-ui
```

## 📞 Próximos Pasos

Una vez que la conexión básica funcione, puedes:

1. Agregar el Load Balancer (Team 2)
2. Implementar el Billing Service (Team 6)
3. Agregar el Client Workload (Team 7)
4. Configurar monitoreo completo

---

**¡Listo para probar!** 🎉
