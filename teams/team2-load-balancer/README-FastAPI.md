# Load Balancer API - FastAPI Implementation

This is a high-performance load balancer built with FastAPI that acts as an API Gateway for the cloud platform, distributing requests across multiple service instances based on health and availability.

## Features

- **Multiple Load Balancing Algorithms**: Round-robin and least connections
- **Health Monitoring**: Automatic health checks for containers
- **Service Registration**: Dynamic service registration and discovery
- **Request Forwarding**: Proxy requests to appropriate containers
- **Statistics**: Real-time load balancer statistics
- **Port Mapping**: External port to service mapping

## Architecture

The load balancer consists of several components:

1. **Models** (`app/models/`): Pydantic models for data validation
2. **Services** (`app/services/`): Core load balancing logic
3. **Routes** (`app/routes/`): API endpoints
4. **Main Application** (`main.py`): FastAPI application setup

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

3. Access the API documentation:
```
http://localhost:3000/docs
```

## API Endpoints

### Health Check
- `GET /health` - Check if the load balancer is running

### Service Management
- `POST /api/v1/services/{image_id}/register` - Register a service with containers
- `GET /api/v1/services/{image_id}` - Get information about a specific service
- `GET /api/v1/services` - Get all registered services

### Port Mappings
- `GET /api/v1/port-mappings` - Get all port mappings

### Request Proxy
- `GET/POST/PUT/DELETE/PATCH /api/v1/proxy/{image_id}/{path}` - Proxy requests to containers

### Health Checks
- `POST /api/v1/health-check` - Trigger health check on all containers

### Statistics
- `GET /api/v1/stats` - Get load balancer statistics

## Usage Examples

### Register a Service

```python
import httpx

async def register_service():
    containers = [
        {
            "container_id": "container-1",
            "name": "my-app-1",
            "port": 4001,
            "image_id": 1,
            "status": "healthy"
        },
        {
            "container_id": "container-2",
            "name": "my-app-2", 
            "port": 4002,
            "image_id": 1,
            "status": "healthy"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3000/api/v1/services/1/register",
            params={"image_name": "my-app"},
            json=containers
        )
        print(response.json())
```

### Proxy a Request

```python
# This will forward the request to one of the healthy containers
# for image_id 1 using the round-robin algorithm
response = await client.get("http://localhost:3000/api/v1/proxy/1/api/users")
```

## Load Balancing Algorithms

### Round Robin (Default)
- Distributes requests evenly across all healthy containers
- Simple and effective for most use cases

### Least Connections
- Routes requests to the container with the fewest active connections
- Better for long-running connections

## Health Monitoring

The load balancer performs health checks on containers by:
1. Making HTTP requests to `/health` endpoint on each container
2. Marking containers as healthy/unhealthy based on response
3. Only routing requests to healthy containers

## Docker Support

Build and run with Docker:

```bash
# Build the image
docker build -t load-balancer .

# Run the container
docker run -p 3000:3000 load-balancer
```

## Testing

Run the test script to verify functionality:

```bash
python test_load_balancer.py
```

## Configuration

The load balancer can be configured through environment variables:

- `HEALTH_CHECK_INTERVAL`: Interval between health checks (default: 30s)
- `MAX_RETRIES`: Maximum retries for failed requests (default: 3)
- `TIMEOUT`: Request timeout (default: 30s)

## Integration with Other Services

This load balancer integrates with:

1. **Orchestrator**: Receives container information and health status
2. **Service Discovery**: Registers and discovers services
3. **UI**: Provides statistics and service information
4. **Billing**: Tracks request counts for billing purposes

## Development

### Project Structure

```
teams/team2-load-balancer/
├── app/
│   ├── models/
│   │   └── load_balancer.py      # Pydantic models
│   ├── services/
│   │   └── load_balancer_service.py  # Core logic
│   └── routes/
│       └── load_balancer.py      # API endpoints
├── main.py                       # FastAPI application
├── requirements.txt              # Python dependencies
├── test_load_balancer.py         # Test script
└── Dockerfile                    # Docker configuration
```

### Adding New Features

1. **New Load Balancing Algorithm**: Add to `LoadBalancingAlgorithm` enum and implement in `LoadBalancerService`
2. **New Endpoints**: Add to `app/routes/load_balancer.py`
3. **New Models**: Add to `app/models/load_balancer.py`

## Performance Considerations

- Uses async/await for non-blocking I/O
- HTTPX for efficient HTTP client operations
- Connection pooling for better performance
- Health checks run asynchronously

## Security

- CORS middleware configured
- Input validation with Pydantic models
- Error handling and logging
- Non-root user in Docker container

## Monitoring and Logging

The application includes comprehensive logging:
- Request forwarding logs
- Health check results
- Error handling
- Performance metrics

## Next Steps

Future enhancements could include:
- Weighted load balancing
- Geographic routing
- Rate limiting
- SSL/TLS termination
- Metrics export (Prometheus)
- Circuit breaker pattern
