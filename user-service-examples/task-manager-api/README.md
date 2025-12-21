# Task Manager API

A complete production-ready REST service with JWT authentication, SQLite database, and full CRUD operations.

## 🎯 Features

- ✅ **JWT Authentication**: User registration and login
- ✅ **Persistent database**: SQLite with SQLAlchemy ORM
- ✅ **Full CRUD**: Create, read, update, and delete tasks
- ✅ **Filters and search**: Filter by status, priority, and text search
- ✅ **Pagination**: For large task lists
- ✅ **Data validation**: Robust input validation
- ✅ **CORS enabled**: For frontend usage
- ✅ **Error handling**: Clear and consistent error responses

## 📋 Data Model

### User
- `id`: Unique ID
- `username`: Username (unique)
- `email`: Email (unique)
- `password_hash`: Password hash
- `created_at`: Creation date

### Task
- `id`: Unique ID
- `title`: Task title (required)
- `description`: Optional description
- `completed`: Completion status (boolean)
- `priority`: Priority (`low`, `medium`, `high`)
- `due_date`: Optional due date
- `created_at`: Creation date
- `updated_at`: Last update date
- `user_id`: Owner user ID

## 🚀 How to Use

### 1. Create the ZIP file

```bash
cd task-manager-api
zip -r task-manager-api.zip . -x "*.git*" -x "*.zip" -x "*.db" -x "*.sqlite*" -x "README.md" -x ".env*"
```

### 2. Upload to the platform

1. Go to the UI at `http://localhost:3000`
2. Log in or register
3. Go to "Images" → "Upload New Image"
4. Fill out the form:
   - **Image Name**: `task-manager-api`
   - **Tag**: `latest`
   - **App Hostname**: `tasks.localhost` (or your preferred name)
   - **Container Port**: `8080`
   - **Build Context File**: Select `task-manager-api.zip`
   - **Min Instances**: `1`
   - **Max Instances**: `2`
   - **CPU Limit**: `0.5`
   - **Memory Limit**: `512m`
5. Click "Upload"

### 3. Create and start container

1. Wait for the build to finish (status "Ready")
2. Go to "View Containers"
3. Create and start a container

### 4. Test the service

The API will be available at:
```
http://localhost:8080/apps/tasks.localhost/
```

## 📡 API Endpoints

### Authentication

#### POST `/auth/register` - Register user
```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "created_at": "2025-12-21T..."
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST `/auth/login` - Login
```json
{
  "username": "user",
  "password": "password123"
}
```

**Response:** Same structure as register

#### GET `/auth/me` - Get current user
**Headers:** `Authorization: Bearer <access_token>`

### Tasks

#### GET `/tasks` - List tasks
**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `completed`: `true` or `false` (filter by status)
- `priority`: `low`, `medium`, or `high`
- `search`: Text to search in title/description
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8080/apps/tasks.localhost/tasks?completed=false&priority=high&page=1"
```

#### POST `/tasks` - Create task
**Headers:** `Authorization: Bearer <access_token>`

```json
{
  "title": "Complete project",
  "description": "Finish API implementation",
  "priority": "high",
  "due_date": "2025-12-31T23:59:59Z"
}
```

#### GET `/tasks/<id>` - Get specific task
**Headers:** `Authorization: Bearer <access_token>`

#### PUT `/tasks/<id>` - Update task
**Headers:** `Authorization: Bearer <access_token>`

```json
{
  "title": "Updated title",
  "completed": true,
  "priority": "low"
}
```

#### DELETE `/tasks/<id>` - Delete task
**Headers:** `Authorization: Bearer <access_token>`

### Others

#### GET `/` - API information
#### GET `/health` - Health check

## 🔐 Authentication

All task routes require JWT authentication. Include the token in the header:

```
Authorization: Bearer <access_token>
```

The token expires after 24 hours by default (configurable via `JWT_ACCESS_TOKEN_EXPIRES`).

## 💾 Database

### ⚠️ Multiple Containers Problem

**IMPORTANT:** The service uses SQLite by default, which **is NOT suitable for multiple containers**.

**The problem:**
- Each container has its own SQLite database at `/app/data/tasks.db`
- If you have 2+ containers running, each has different data
- The Load Balancer uses Round Robin, so requests go to different containers
- A user can create a task in container A, but when listing tasks it may go to container B (which doesn't have that task)

**Production Solution:**

To use multiple containers, **you must use a shared external database**:

1. **PostgreSQL** (recommended):
   ```bash
   # In docker-compose.yml or as external service
   DATABASE_URL=postgresql://user:password@postgres-host:5432/tasksdb
   ```

2. **MySQL**:
   ```bash
   DATABASE_URL=mysql://user:password@mysql-host:3306/tasksdb
   ```

3. **Shared volume** (NOT recommended for SQLite):
   - Even if you share the `.db` file, SQLite doesn't handle concurrent writes from multiple processes well
   - Can cause data corruption or "database is locked" errors

**For development/testing with a single container:**
- SQLite works fine if you only have 1 container
- Data persists while the container exists
- If you delete the container, data is lost

### Authentication (JWT) ✅

Authentication **DOES work** with multiple containers because:
- JWT is **stateless** (no state)
- The token contains all necessary information (`user_id`)
- All containers share the same `JWT_SECRET_KEY`
- Any container can validate the token without needing shared session

## 🔧 Configuration

The service uses environment variables (with default values):

- `PORT`: Server port (default: 8080)
- `SECRET_KEY`: Secret key for Flask (change in production)
- `JWT_SECRET_KEY`: Secret key for JWT (change in production)
- `JWT_ACCESS_TOKEN_EXPIRES`: Token expiration in seconds (default: 86400 = 24h)
- `DATABASE_URL`: Database URL (default: sqlite:///data/tasks.db)
- `SERVICE_NAME`: Service name
- `VERSION`: Service version

## 📝 Complete Usage Example

```bash
# 1. Register user
curl -X POST http://localhost:8080/apps/tasks.localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# Save the access_token from the response

# 2. Create a task
curl -X POST http://localhost:8080/apps/tasks.localhost/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "title": "My first task",
    "description": "This is a test task",
    "priority": "high"
  }'

# 3. List tasks
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8080/apps/tasks.localhost/tasks

# 4. Update task (ID 1)
curl -X PUT http://localhost:8080/apps/tasks.localhost/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "completed": true
  }'

# 5. Delete task (ID 1)
curl -X DELETE http://localhost:8080/apps/tasks.localhost/tasks/1 \
  -H "Authorization: Bearer <access_token>"
```

## 🎓 Real-World Use Cases

This service demonstrates:
- ✅ Complete and professional REST API
- ✅ Secure authentication with JWT
- ✅ Persistent database
- ✅ Data validation
- ✅ Filters and search
- ✅ Pagination
- ✅ Robust error handling
- ✅ Production-ready (with proper configuration)

## 🔒 Security

**Important for production:**
- Change `SECRET_KEY` and `JWT_SECRET_KEY` to secure random values
- Use HTTPS in production
- Consider rate limiting
- Validate and sanitize all inputs
- **Use shared external database** (PostgreSQL/MySQL) for multiple containers
- Implement database backups
- Implement security logging
- Use environment variables for secrets (never hardcode)

## 🏗️ Architecture for Multiple Containers

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │
│  (Round Robin)  │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Container │ │Container │ │Container │
│    A     │ │    B     │ │    C     │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │           │           │
     └───────────┴───────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  PostgreSQL DB  │  ← Shared database
        │  (Shared)       │     (all containers)
        └─────────────────┘

✅ JWT: Works (stateless, all validate with same key)
❌ SQLite: Does NOT work (each container has its own DB)
✅ PostgreSQL: Works (all share the same DB)
```

## 📦 Dependencies

- `flask`: Web framework
- `flask-sqlalchemy`: Database ORM
- `flask-jwt-extended`: JWT authentication
- `flask-cors`: CORS support
- `werkzeug`: Utilities (password hashing)
- `python-dotenv`: Environment variable management
