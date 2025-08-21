# Team 2 - Load Balancer (API Gateway)

## 🎯 Mission

Build a high-performance load balancer that acts as the API Gateway for the cloud platform, distributing requests across multiple service instances based on health and availability.

## 🚀 Quick Start

### Development Mode
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Production Mode
```bash
# Start production server
npm start
```

### Docker Mode
```bash
# Build and run with Docker
docker build -t team2-load-balancer .
docker run -p 8080:8080 team2-load-balancer

# Or use docker-compose (includes mock services)
docker-compose up -d
```

## 📊 Service Status

The load balancer will be available at:
- **Main API**: http://localhost:8080
- **Health Check**: http://localhost:8080/health
- **Services Status**: http://localhost:8080/api/services

## 🔧 Architecture

### Core Components

1. **Load Balancer Service** (`src/services/loadBalancer.js`)
   - Round-robin load balancing algorithm
   - Health checks for all services
   - Request routing and metrics tracking

2. **API Routes** (`src/routes/loadBalancer.js`)
   - Service routing endpoints
   - Status monitoring endpoints
   - Mock data endpoints for development

3. **Health Check Routes** (`src/routes/health.js`)
   - Basic health checks
   - Detailed service status
   - Force health check triggers

### Mock Services

For development, the load balancer includes mock services:
- **UI Service**: http://localhost:3000
- **Orchestrator**: http://localhost:8081
- **Billing**: http://localhost:8083
- **Workload**: http://localhost:8084

## 📡 API Endpoints

### Service Status
```bash
# Get all services status
GET /api/services

# Get specific service status
GET /api/services/{serviceType}

# Add new service
POST /api/services
{
  "serviceType": "new-service",
  "instances": [
    {
      "id": "instance-1",
      "url": "http://localhost:8085",
      "port": 8085,
      "healthy": true,
      "load": 0
    }
  ]
}
```

### Health Checks
```bash
# Basic health check
GET /health

# Detailed health check
GET /health/detailed

# Service-specific health check
GET /health/service/{serviceType}

# Force health check
POST /health/check
```

### Request Routing
```bash
# Route to UI service
GET/POST/PUT/DELETE /api/ui/*

# Route to Orchestrator service
GET/POST/PUT/DELETE /api/orchestrator/*

# Route to Billing service
GET/POST/PUT/DELETE /api/billing/*

# Route to Workload service
GET/POST/PUT/DELETE /api/workload/*
```

### Mock Data (Development)
```bash
# Mock images data
GET /api/mock/images

# Mock metrics data
GET /api/mock/metrics
```

## 🔄 Load Balancing Algorithm

### Round-Robin
- Distributes requests evenly across healthy instances
- Automatically skips unhealthy instances
- Tracks load per instance for monitoring

### Health Checks
- Performed every 30 seconds
- Checks `/health` endpoint of each service
- Marks instances as unhealthy on connection failures
- Automatic recovery when health checks pass

## 📈 Metrics & Monitoring

### Service Metrics
- Total requests per service
- Active requests per service
- Instance health status
- Load distribution

### Instance Metrics
- Individual instance load
- Health status
- Response times
- Error rates

## 🐳 Docker Configuration

### Development
```yaml
# docker-compose.yml includes:
- Load Balancer (port 8080)
- Mock UI Service (port 3000)
- Mock Orchestrator (port 8081)
- Mock Billing (port 8083)
- Mock Workload (port 8084)
```

### Production
```dockerfile
# Multi-stage build with:
- Node.js 18 Alpine base
- Health checks
- Security headers
- Optimized for production
```

## 🔗 Integration Points

### With Team 1 (UI)
- Receives requests from UI components
- Routes image management requests
- Provides service status for dashboard

### With Team 3 (Orchestrator)
- Routes container management requests
- Receives health status updates
- Manages instance scaling requests

### With Team 6 (Billing)
- Routes billing and cost requests
- Provides usage metrics
- Handles payment processing

### With Team 7 (Workload)
- Routes workload generation requests
- Manages test traffic distribution
- Provides performance metrics

## 🧪 Testing

### Manual Testing
```bash
# Test health check
curl http://localhost:8080/health

# Test service status
curl http://localhost:8080/api/services

# Test routing to mock services
curl http://localhost:8080/api/ui/
curl http://localhost:8080/api/orchestrator/
```

### Load Testing
```bash
# Simple load test with curl
for i in {1..100}; do
  curl http://localhost:8080/api/mock/images &
done
wait
```

## 🚨 Error Handling

### Service Unavailable
- Returns 503 status when no healthy instances
- Logs error details for debugging
- Continues monitoring for recovery

### Connection Timeouts
- 5-second timeout for service requests
- Automatic instance marking as unhealthy
- Retry logic for transient failures

### Invalid Routes
- 404 for unknown service types
- Detailed error messages
- Request logging for debugging

## 📝 Development Notes

### Adding New Services
1. Update `initializeMockServices()` in `loadBalancer.js`
2. Add routing endpoint in `loadBalancer.js`
3. Create health check configuration
4. Update documentation

### Configuration
- Health check interval: 30 seconds
- Request timeout: 5 seconds
- Port: 8080 (configurable via PORT env var)

### Logging
- Request logging with Morgan
- Error logging for debugging
- Health check status logging

## 🎯 Success Criteria

- [x] Basic load balancing functionality
- [x] Health checks for all services
- [x] Round-robin algorithm implementation
- [x] Service status monitoring
- [x] Docker containerization
- [x] Mock services for development
- [x] API documentation
- [x] Error handling and logging

## 🔄 Next Steps

1. **Integration Testing**: Test with real services from other teams
2. **Advanced Load Balancing**: Implement weighted round-robin or least connections
3. **Rate Limiting**: Add request rate limiting per service
4. **Circuit Breaker**: Implement circuit breaker pattern
5. **Metrics Dashboard**: Add Prometheus metrics and Grafana dashboard
6. **SSL/TLS**: Add HTTPS support for production
7. **Authentication**: Add API key or JWT authentication

## 👥 Team Communication Checklist

### Day 1 - Independent Development
- [x] Basic load balancer implementation
- [x] Mock services setup
- [x] Health check system
- [x] API documentation

### Day 2 - Integration Planning
- [ ] Coordinate with Team 1 (UI) for API contracts
- [ ] Coordinate with Team 3 (Orchestrator) for service discovery
- [ ] Define shared environment variables
- [ ] Plan integration testing

### Day 3 - Final Integration
- [ ] Integrate with all teams
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Presentation preparation 