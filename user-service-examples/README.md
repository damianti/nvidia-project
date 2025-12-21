# User Service Examples

Ready-to-deploy service examples for the NVIDIA Cloud platform. These services demonstrate different complexity levels and use cases.

## 📁 Available Services

### 1. Simple API (`simple-api/`)

A basic example service with simple REST endpoints. Ideal for:
- Learning the deployment flow
- Testing the system
- Simple services without a database

**Features:**
- Basic REST API
- Health checks
- In-memory item management
- No authentication

**See:** [Simple API README](simple-api/README.md)

### 2. Task Manager API (`task-manager-api/`)

A complete production-ready service with authentication, database, and full CRUD operations. Ideal for:
- Demonstrating real platform capabilities
- Services that require persistence
- APIs with authentication

**Features:**
- ✅ JWT Authentication
- ✅ Persistent SQLite database
- ✅ Full CRUD for tasks
- ✅ Filters, search, and pagination
- ✅ Data validation
- ✅ Robust error handling

**See:** [Task Manager API README](task-manager-api/README.md)

## 🚀 How to Use These Examples

### Step 1: Choose a service

Navigate to the folder of the service you want to use:
- `simple-api/` - For basic services
- `task-manager-api/` - For complete services

### Step 2: Create the ZIP file

From the service folder:

```bash
cd simple-api  # or task-manager-api
zip -r service-name.zip . -x "*.git*" -x "*.zip" -x "*.db" -x "*.sqlite*" -x "README.md" -x ".env*"
```

### Step 3: Upload to the platform

1. Go to `http://localhost:3000`
2. Log in
3. Go to "Images" → "Upload New Image"
4. Fill out the form and select the ZIP file
5. Wait for the build to complete

### Step 4: Create container

1. Go to "View Containers"
2. Create and start a container
3. Access the service using the provided URL

## 📝 Service Structure

Each service should include:

```
service-name/
├── app.py              # Main application code
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .dockerignore      # Files to exclude from build
└── README.md          # Service documentation
```

## 🔧 Requirements

All services must:
- ✅ Listen on port **8080** (or configurable via `PORT`)
- ✅ Listen on `0.0.0.0` (not `localhost`)
- ✅ Include a `/health` endpoint for health checks
- ✅ Be stateless (or use external storage)
- ✅ Handle errors appropriately

## 📚 Documentation

Each service has its own README with:
- Feature description
- Usage instructions
- Endpoint examples
- Use cases

## 🎯 Future Examples

Possible future services:
- E-commerce API (products, cart, orders)
- Blog API (posts, comments, categories)
- Chat API (messages, rooms, users)
- Analytics API (metrics, events, reports)
- Games with shared state (chess, checkers, etc.)

## ⚠️ Important Considerations

### Services with Shared State

If your service needs **shared state** across multiple containers (like a game, real-time chat, etc.), read:

📄 **[Architecture for Stateful Games](chess-game-architecture.md)**

This document explains:
- The Round Robin problem with stateful services
- Possible solutions (shared state, sticky sessions, WebSockets)
- Implementation examples
- Recommendations based on use case

## 📄 License

These examples are for educational and demonstration purposes.
