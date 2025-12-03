# Health Check Endpoints

All services in the NVIDIA Cloud Platform implement health check endpoints for monitoring and orchestration.

## Service Health Endpoints

| Service | Endpoint | Method | Response Format |
|---------|----------|--------|-----------------|
| **UI** | `/health` | GET | `200 OK` with `"healthy\n"` (via nginx) |
| **API Gateway** | `/health` | GET | `{"status": "healthy", "service": "api-gateway"}` |
| **Auth Service** | `/health` | GET | `{"status": "healthy", "service": "auth-service"}` |
| **Orchestrator** | `/health` | GET | `{"status": "healthy", "database": "...", "docker": "..."}` |
| **Load Balancer** | `/health` | GET | `{"status": "ok"}` |
| **Service Discovery** | `/health` | GET | `{"status": "healthy"}` |
| **Billing** | `/health` | GET | `{"status": "healthy"}` |
| **Client Workload** | `/health` | GET | `{"status": "healthy"}` |

## Health Check Details

### UI Service
- **Implementation**: Nginx configuration returns static response
- **Response**: HTTP 200 with plain text `"healthy\n"`
- **Purpose**: Simple availability check

### API Gateway
- **Implementation**: FastAPI endpoint
- **Response**: JSON with service name
- **Purpose**: Verify gateway is accepting requests

### Auth Service
- **Implementation**: FastAPI endpoint
- **Response**: JSON with service name
- **Purpose**: Verify authentication service is available

### Orchestrator
- **Implementation**: FastAPI endpoint with dependency checks
- **Response**: JSON with status of database and Docker connections
- **Purpose**: Verify orchestrator can manage containers
- **Checks**:
  - Database connectivity (PostgreSQL)
  - Docker daemon connectivity

### Load Balancer
- **Implementation**: FastAPI endpoint
- **Response**: Simple JSON status
- **Purpose**: Verify load balancer is operational

### Service Discovery
- **Implementation**: FastAPI endpoint
- **Response**: Simple JSON status
- **Purpose**: Verify service discovery is running

### Billing
- **Implementation**: FastAPI endpoint
- **Response**: Simple JSON status
- **Purpose**: Verify billing service is available

### Client Workload
- **Implementation**: FastAPI endpoint
- **Response**: Simple JSON status
- **Purpose**: Verify workload generator is ready

## Docker Compose Health Checks

All services have health checks configured in `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:<port>/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Usage

### Check All Services
```bash
./scripts/check-services.sh
```

### Check Individual Service
```bash
curl http://localhost:3000/health    # UI
curl http://localhost:8080/health   # API Gateway
curl http://localhost:3003/health   # Orchestrator
curl http://localhost:3004/health   # Load Balancer
curl http://localhost:3006/health   # Service Discovery
curl http://localhost:3007/health   # Billing
curl http://localhost:3008/health   # Client Workload
```

### Using Docker Compose
```bash
# Check service health status
docker-compose ps

# View health check logs
docker inspect <container-name> | grep -A 10 Health
```

## Health Check Standards

All health check endpoints should:
1. Return HTTP 200 status code when healthy
2. Return HTTP 503 or 500 when unhealthy
3. Respond quickly (< 1 second)
4. Not require authentication
5. Be lightweight (no heavy operations)

## Monitoring Integration

Health checks are used by:
- Docker Compose for service dependency management
- Service Discovery for container health monitoring
- Load Balancer for routing decisions
- Monitoring tools (future: Prometheus, Grafana)

