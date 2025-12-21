# Example Cloud Run Service

Este es un servicio de ejemplo completo que puedes subir a la plataforma NVIDIA Cloud usando el modelo Cloud Run-style.

## 📋 Descripción

Este servicio es una API REST simple construida con Flask que:
- Escucha en el puerto 8080 (puerto estándar)
- Proporciona endpoints para gestionar items
- Incluye health checks
- Demuestra routing basado en paths

## 🚀 Cómo usar este ejemplo

### 1. Crear el archivo ZIP

Desde la carpeta del servicio:

```bash
cd simple-api
./create-zip.sh
```

O manualmente:

```bash
cd simple-api
zip -r example-service.zip . -x "*.git*" -x "*.zip" -x "*.tar.gz" -x "create-zip.sh" -x "README.md"
```

O si prefieres tar.gz:

```bash
cd temp
tar -czf example-service.tar.gz .
```

### 2. Subir a la plataforma

1. Ve a la UI en `http://localhost:3000`
2. Inicia sesión o regístrate
3. Ve a la página de "Images"
4. Haz clic en "Upload New Image"
5. Completa el formulario:
   - **Image Name**: `example-service`
   - **Tag**: `latest`
   - **App Hostname**: `example.localhost` (o el que prefieras)
   - **Container Port**: `8080`
   - **Build Context File**: Selecciona el archivo `example-service.zip` o `example-service.tar.gz`
   - **Min Instances**: `1`
   - **Max Instances**: `2`
   - **CPU Limit**: `0.5`
   - **Memory Limit**: `512m`
6. Haz clic en "Upload"

### 3. Esperar el build

- El estado cambiará de "Building" a "Ready" cuando el build termine
- Si falla, puedes ver los logs haciendo clic en "View Build Logs"

### 4. Crear contenedores

1. Una vez que la imagen esté "Ready", haz clic en "View Containers"
2. Haz clic en "Create Container"
3. Selecciona la imagen y crea 1 contenedor
4. Inicia el contenedor si no se inicia automáticamente

### 5. Probar el servicio

Una vez que el contenedor esté corriendo, puedes acceder al servicio en:

```
http://localhost:8080/apps/example.localhost/
```

O usando curl:

```bash
# Health check
curl http://localhost:8080/apps/example.localhost/health

# Root endpoint
curl http://localhost:8080/apps/example.localhost/

# Crear un item
curl -X POST http://localhost:8080/apps/example.localhost/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "This is a test"}'

# Listar items
curl http://localhost:8080/apps/example.localhost/items

# Obtener información del servicio
curl http://localhost:8080/apps/example.localhost/info
```

## 📡 Endpoints disponibles

- `GET /` - Información del servicio
- `GET /health` - Health check
- `GET /info` - Información detallada
- `GET /items` - Listar todos los items
- `POST /items` - Crear un nuevo item
- `GET /items/<id>` - Obtener un item específico
- `DELETE /items/<id>` - Eliminar un item
- `GET /test/<path>` - Endpoint de prueba para routing

## 🔧 Personalización

Puedes modificar `app.py` para agregar más funcionalidad:
- Agregar más endpoints
- Conectar a una base de datos
- Agregar autenticación
- Implementar lógica de negocio específica

Solo asegúrate de:
- Mantener el puerto 8080 (o actualizar `container_port` en el formulario)
- Incluir un endpoint `/health` para health checks
- Escuchar en `0.0.0.0` (no `localhost`)

## 📝 Notas

- Este servicio usa almacenamiento en memoria, así que los datos se pierden al reiniciar
- Para producción, deberías usar una base de datos persistente
- El servicio está diseñado para ser stateless y escalable
