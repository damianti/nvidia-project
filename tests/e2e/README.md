# End-to-End Testing

This directory contains end-to-end tests for the Cloud Run-style image upload and deployment flow.

## Overview

The test validates the complete flow:
1. **Authentication** - Login/register a test user
2. **Upload & Build** - Upload a Dockerfile archive and build the image
3. **Deploy** - Create containers from the built image
4. **Route** - Test routing requests through API Gateway → Load Balancer → Container
5. **Cleanup** - Optionally delete test resources

## Test Application

The `test-app/` directory contains a simple Flask application that:
- Listens on port 8080 (configurable via `PORT` env var)
- Responds with JSON messages
- Includes health check endpoint
- Supports path-based routing tests

### Test App Structure

```
test-app/
├── Dockerfile          # Dockerfile for the test app
├── app.py             # Flask application
└── requirements.txt   # Python dependencies
```

## Running the Tests

### Prerequisites

1. All services must be running:
   ```bash
   docker-compose up -d
   ```

2. Wait for services to be healthy (especially Orchestrator, API Gateway, Load Balancer, Service Discovery)

3. Install Python dependencies (for Python script):
   ```bash
   pip install requests
   ```

### Option 1: Bash Script

```bash
cd tests/e2e
./test-e2e.sh
```

### Option 2: Python Script (Recommended)

```bash
cd tests/e2e
python3 test-e2e.py
```

The Python script provides better error handling and is more maintainable.

### Configuration

You can configure the test via environment variables:

```bash
export API_GATEWAY_URL="http://localhost:8080"
export ORCHESTRATOR_URL="http://localhost:3002"
export TEST_EMAIL="test@example.com"
export TEST_PASSWORD="testpass123"
export APP_HOSTNAME="testapp.localhost"

python3 test-e2e.py
```

## Test Flow Details

### 1. Authentication
- Attempts to login with test credentials
- If login fails, attempts to register a new user
- Stores JWT token in session cookies

### 2. Upload & Build
- Creates a tar.gz archive of the test app
- Uploads via `POST /api/images` (multipart/form-data)
- Polls build status until completion (max 120 seconds)
- Retrieves build logs if build fails

### 3. Deploy Containers
- Creates 1 container from the built image
- Waits for container to start (5 seconds)

### 4. Test Routing
- Tests path-based routing: `GET /apps/{app_hostname}/`
- Tests nested paths: `GET /apps/{app_hostname}/test/hello`
- Validates responses contain expected content

### 5. Cleanup
- Prompts user to delete test resources
- Deletes container and image if confirmed

## Expected Output

```
=== End-to-End Test Script ===
API Gateway: http://localhost:8080
Orchestrator: http://localhost:3002
App Hostname: testapp.localhost

[1/6] Authenticating user...
✓ Authentication successful (login)

[2/6] Creating test app archive...
✓ Archive created: /tmp/test-app.tar.gz

[3/6] Uploading image and building...
✓ Image uploaded. ID: 1
Waiting for build to complete...
✓ Build completed successfully

[4/6] Creating containers...
✓ Container created. ID: 1
Waiting for container to start...

[5/6] Testing routing via API Gateway...
✓ Path-based routing works!
✓ Nested path routing works!

[6/6] Cleanup...
Delete test image and containers? (y/N): y
✓ Cleanup completed

=== All tests passed! ===
```

## Troubleshooting

### Build Fails
- Check Orchestrator logs: `docker logs nvidia-orchestrator`
- Verify Docker-in-Docker is running: `docker ps | grep docker-dind`
- Check build logs via API: `GET /api/images/{id}/build-logs`

### Routing Fails
- Verify Service Discovery is running: `docker ps | grep service-discovery`
- Check Load Balancer logs: `docker logs nvidia-load-balancer`
- Verify container is running: `GET /api/containers`

### Authentication Fails
- Check Auth Service: `docker logs nvidia-auth-service`
- Verify API Gateway is proxying correctly
- Check database connectivity

## Manual Testing

You can also test manually using `curl`:

### 1. Login
```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' \
  -c cookies.txt
```

### 2. Upload Image
```bash
curl -X POST http://localhost:3002/api/images \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=test-app" \
  -F "tag=latest" \
  -F "app_hostname=testapp.localhost" \
  -F "container_port=8080" \
  -F "file=@test-app.tar.gz"
```

### 3. Create Containers
```bash
curl -X POST http://localhost:3002/api/containers/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-container","image_id":1,"count":1}'
```

### 4. Test Routing
```bash
curl http://localhost:8080/apps/testapp.localhost/ \
  -H "Host: testapp.localhost"
```

## Next Steps

After successful E2E testing:
1. Update UI to support the new upload flow
2. Add integration tests to CI/CD pipeline
3. Test with multiple containers and load balancing
4. Test error scenarios (build failures, container crashes, etc.)
