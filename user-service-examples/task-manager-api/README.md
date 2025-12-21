# Task Manager API

Un servicio REST completo y listo para producción con autenticación JWT, base de datos SQLite, y operaciones CRUD completas.

## 🎯 Características

- ✅ **Autenticación JWT**: Registro y login de usuarios
- ✅ **Base de datos persistente**: SQLite con SQLAlchemy ORM
- ✅ **CRUD completo**: Crear, leer, actualizar y eliminar tareas
- ✅ **Filtros y búsqueda**: Filtrar por estado, prioridad, y buscar por texto
- ✅ **Paginación**: Para listas grandes de tareas
- ✅ **Validación de datos**: Validación robusta de inputs
- ✅ **CORS habilitado**: Para uso desde frontend
- ✅ **Manejo de errores**: Respuestas de error claras y consistentes

## 📋 Modelo de Datos

### Usuario (User)
- `id`: ID único
- `username`: Nombre de usuario (único)
- `email`: Email (único)
- `password_hash`: Hash de la contraseña
- `created_at`: Fecha de creación

### Tarea (Task)
- `id`: ID único
- `title`: Título de la tarea (requerido)
- `description`: Descripción opcional
- `completed`: Estado de completado (boolean)
- `priority`: Prioridad (`low`, `medium`, `high`)
- `due_date`: Fecha límite opcional
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización
- `user_id`: ID del usuario propietario

## 🚀 Cómo usar

### 1. Crear el archivo ZIP

```bash
cd task-manager-api
zip -r task-manager-api.zip . -x "*.git*" -x "*.zip" -x "*.db" -x "*.sqlite*" -x "README.md" -x ".env*"
```

### 2. Subir a la plataforma

1. Ve a la UI en `http://localhost:3000`
2. Inicia sesión o regístrate
3. Ve a "Images" → "Upload New Image"
4. Completa el formulario:
   - **Image Name**: `task-manager-api`
   - **Tag**: `latest`
   - **App Hostname**: `tasks.localhost` (o el que prefieras)
   - **Container Port**: `8080`
   - **Build Context File**: Selecciona `task-manager-api.zip`
   - **Min Instances**: `1`
   - **Max Instances**: `2`
   - **CPU Limit**: `0.5`
   - **Memory Limit**: `512m`
5. Haz clic en "Upload"

### 3. Crear y iniciar contenedor

1. Espera a que el build termine (estado "Ready")
2. Ve a "View Containers"
3. Crea e inicia un contenedor

### 4. Probar el servicio

La API estará disponible en:
```
http://localhost:8080/apps/tasks.localhost/
```

## 📡 Endpoints de la API

### Autenticación

#### POST `/auth/register` - Registrar usuario
```json
{
  "username": "usuario",
  "email": "usuario@example.com",
  "password": "password123"
}
```

**Respuesta:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@example.com",
    "created_at": "2025-12-21T..."
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST `/auth/login` - Iniciar sesión
```json
{
  "username": "usuario",
  "password": "password123"
}
```

**Respuesta:** Misma estructura que register

#### GET `/auth/me` - Obtener usuario actual
**Headers:** `Authorization: Bearer <access_token>`

### Tareas

#### GET `/tasks` - Listar tareas
**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `completed`: `true` o `false` (filtrar por estado)
- `priority`: `low`, `medium`, o `high`
- `search`: Texto para buscar en título/descripción
- `page`: Número de página (default: 1)
- `per_page`: Items por página (default: 20)

**Ejemplo:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8080/apps/tasks.localhost/tasks?completed=false&priority=high&page=1"
```

#### POST `/tasks` - Crear tarea
**Headers:** `Authorization: Bearer <access_token>`

```json
{
  "title": "Completar proyecto",
  "description": "Terminar la implementación del API",
  "priority": "high",
  "due_date": "2025-12-31T23:59:59Z"
}
```

#### GET `/tasks/<id>` - Obtener tarea específica
**Headers:** `Authorization: Bearer <access_token>`

#### PUT `/tasks/<id>` - Actualizar tarea
**Headers:** `Authorization: Bearer <access_token>`

```json
{
  "title": "Título actualizado",
  "completed": true,
  "priority": "low"
}
```

#### DELETE `/tasks/<id>` - Eliminar tarea
**Headers:** `Authorization: Bearer <access_token>`

### Otros

#### GET `/` - Información de la API
#### GET `/health` - Health check

## 🔐 Autenticación

Todas las rutas de tareas requieren autenticación JWT. Incluye el token en el header:

```
Authorization: Bearer <access_token>
```

El token expira después de 24 horas por defecto (configurable vía `JWT_ACCESS_TOKEN_EXPIRES`).

## 💾 Base de Datos

El servicio usa SQLite por defecto. La base de datos se guarda en `/app/data/tasks.db` dentro del contenedor.

**Nota:** Los datos persisten mientras el contenedor exista. Si eliminas el contenedor, los datos se pierden. Para producción, considera usar un volumen persistente o una base de datos externa (PostgreSQL, MySQL, etc.).

## 🔧 Configuración

El servicio usa variables de entorno (con valores por defecto):

- `PORT`: Puerto del servidor (default: 8080)
- `SECRET_KEY`: Clave secreta para Flask (cambiar en producción)
- `JWT_SECRET_KEY`: Clave secreta para JWT (cambiar en producción)
- `JWT_ACCESS_TOKEN_EXPIRES`: Expiración del token en segundos (default: 86400 = 24h)
- `DATABASE_URL`: URL de la base de datos (default: sqlite:///data/tasks.db)
- `SERVICE_NAME`: Nombre del servicio
- `VERSION`: Versión del servicio

## 📝 Ejemplo de Uso Completo

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8080/apps/tasks.localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# Guarda el access_token de la respuesta

# 2. Crear una tarea
curl -X POST http://localhost:8080/apps/tasks.localhost/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "title": "Mi primera tarea",
    "description": "Esta es una tarea de prueba",
    "priority": "high"
  }'

# 3. Listar tareas
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8080/apps/tasks.localhost/tasks

# 4. Actualizar tarea (ID 1)
curl -X PUT http://localhost:8080/apps/tasks.localhost/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "completed": true
  }'

# 5. Eliminar tarea (ID 1)
curl -X DELETE http://localhost:8080/apps/tasks.localhost/tasks/1 \
  -H "Authorization: Bearer <access_token>"
```

## 🎓 Casos de Uso Reales

Este servicio demuestra:
- ✅ API REST completa y profesional
- ✅ Autenticación segura con JWT
- ✅ Base de datos persistente
- ✅ Validación de datos
- ✅ Filtros y búsqueda
- ✅ Paginación
- ✅ Manejo de errores robusto
- ✅ Listo para producción (con configuración adecuada)

## 🔒 Seguridad

**Importante para producción:**
- Cambiar `SECRET_KEY` y `JWT_SECRET_KEY` por valores aleatorios seguros
- Usar HTTPS en producción
- Considerar rate limiting
- Validar y sanitizar todos los inputs
- Usar base de datos externa con backups
- Implementar logging de seguridad

## 📦 Dependencias

- `flask`: Framework web
- `flask-sqlalchemy`: ORM para base de datos
- `flask-jwt-extended`: Autenticación JWT
- `flask-cors`: Soporte CORS
- `werkzeug`: Utilidades (hashing de passwords)
- `python-dotenv`: Manejo de variables de entorno
