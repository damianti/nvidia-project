# User Service Examples

Ejemplos de servicios listos para desplegar en la plataforma NVIDIA Cloud. Estos servicios demuestran diferentes niveles de complejidad y casos de uso.

## 📁 Servicios Disponibles

### 1. Simple API (`simple-api/`)

Un servicio básico de ejemplo con endpoints REST simples. Ideal para:
- Aprender el flujo de deployment
- Probar el sistema
- Servicios simples sin base de datos

**Características:**
- API REST básica
- Health checks
- Gestión de items en memoria
- Sin autenticación

**Ver:** [README de Simple API](simple-api/README.md)

### 2. Task Manager API (`task-manager-api/`)

Un servicio completo y listo para producción con autenticación, base de datos y CRUD completo. Ideal para:
- Demostrar capacidades reales de la plataforma
- Servicios que requieren persistencia
- APIs con autenticación

**Características:**
- ✅ Autenticación JWT
- ✅ Base de datos SQLite persistente
- ✅ CRUD completo de tareas
- ✅ Filtros, búsqueda y paginación
- ✅ Validación de datos
- ✅ Manejo de errores robusto

**Ver:** [README de Task Manager API](task-manager-api/README.md)

## 🚀 Cómo Usar Estos Ejemplos

### Paso 1: Elegir un servicio

Navega a la carpeta del servicio que quieres usar:
- `simple-api/` - Para servicios básicos
- `task-manager-api/` - Para servicios completos

### Paso 2: Crear el archivo ZIP

Desde la carpeta del servicio:

```bash
cd simple-api  # o task-manager-api
zip -r service-name.zip . -x "*.git*" -x "*.zip" -x "*.db" -x "*.sqlite*" -x "README.md" -x ".env*"
```

### Paso 3: Subir a la plataforma

1. Ve a `http://localhost:3000`
2. Inicia sesión
3. Ve a "Images" → "Upload New Image"
4. Completa el formulario y selecciona el archivo ZIP
5. Espera a que el build termine

### Paso 4: Crear contenedor

1. Ve a "View Containers"
2. Crea e inicia un contenedor
3. Accede al servicio usando la URL proporcionada

## 📝 Estructura de un Servicio

Cada servicio debe incluir:

```
service-name/
├── app.py              # Código principal de la aplicación
├── Dockerfile          # Configuración de Docker
├── requirements.txt    # Dependencias de Python
├── .dockerignore      # Archivos a excluir del build
└── README.md          # Documentación del servicio
```

## 🔧 Requisitos

Todos los servicios deben:
- ✅ Escuchar en el puerto **8080** (o configurable vía `PORT`)
- ✅ Escuchar en `0.0.0.0` (no `localhost`)
- ✅ Incluir un endpoint `/health` para health checks
- ✅ Ser stateless (o usar almacenamiento externo)
- ✅ Manejar errores apropiadamente

## 📚 Documentación

Cada servicio tiene su propio README con:
- Descripción de características
- Instrucciones de uso
- Ejemplos de endpoints
- Casos de uso

## 🎯 Próximos Ejemplos

Posibles servicios futuros:
- E-commerce API (productos, carrito, órdenes)
- Blog API (posts, comentarios, categorías)
- Chat API (mensajes, salas, usuarios)
- Analytics API (métricas, eventos, reportes)

## 📄 Licencia

Estos ejemplos son para uso educativo y demostración.
