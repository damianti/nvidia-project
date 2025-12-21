# Example Cloud Run Service

This is a complete example service that you can upload to the NVIDIA Cloud platform using the Cloud Run-style model.

## 📋 Description

This service is a simple REST API built with Flask that:
- Listens on port 8080 (standard port)
- Provides endpoints for managing items
- Includes health checks
- Demonstrates path-based routing

## 🚀 How to Use This Example

### 1. Create the ZIP file

From the service folder:

```bash
cd simple-api
./create-zip.sh
```

Or manually:

```bash
cd simple-api
zip -r example-service.zip . -x "*.git*" -x "*.zip" -x "*.tar.gz" -x "create-zip.sh" -x "README.md"
```

Or if you prefer tar.gz:

```bash
cd simple-api
tar -czf example-service.tar.gz .
```

### 2. Upload to the platform

1. Go to the UI at `http://localhost:3000`
2. Log in or register
3. Go to the "Images" page
4. Click "Upload New Image"
5. Fill out the form:
   - **Image Name**: `example-service`
   - **Tag**: `latest`
   - **App Hostname**: `example.localhost` (or your preferred name)
   - **Container Port**: `8080`
   - **Build Context File**: Select the `example-service.zip` or `example-service.tar.gz` file
   - **Min Instances**: `1`
   - **Max Instances**: `2`
   - **CPU Limit**: `0.5`
   - **Memory Limit**: `512m`
6. Click "Upload"

### 3. Wait for the build

- The status will change from "Building" to "Ready" when the build completes
- If it fails, you can view the logs by clicking "View Build Logs"

### 4. Create containers

1. Once the image is "Ready", click "View Containers"
2. Click "Create Container"
3. Select the image and create 1 container
4. Start the container if it doesn't start automatically

### 5. Test the service

Once the container is running, you can access the service at:

```
http://localhost:8080/apps/example.localhost/
```

Or using curl:

```bash
# Health check
curl http://localhost:8080/apps/example.localhost/health

# Root endpoint
curl http://localhost:8080/apps/example.localhost/

# Create an item
curl -X POST http://localhost:8080/apps/example.localhost/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "This is a test"}'

# List items
curl http://localhost:8080/apps/example.localhost/items

# Get service information
curl http://localhost:8080/apps/example.localhost/info
```

## 📡 Available Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /info` - Detailed information
- `GET /items` - List all items
- `POST /items` - Create a new item
- `GET /items/<id>` - Get a specific item
- `DELETE /items/<id>` - Delete an item
- `GET /test/<path>` - Test endpoint for routing

## 🔧 Customization

You can modify `app.py` to add more functionality:
- Add more endpoints
- Connect to a database
- Add authentication
- Implement specific business logic

Just make sure to:
- Keep port 8080 (or update `container_port` in the form)
- Include a `/health` endpoint for health checks
- Listen on `0.0.0.0` (not `localhost`)

## 📝 Notes

- This service uses in-memory storage, so data is lost on restart
- For production, you should use a persistent database
- The service is designed to be stateless and scalable
