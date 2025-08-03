# Team 2 - Load Balancer (API Gateway)

## 🎯 Mission
Build a high-performance load balancer that acts as the API Gateway for the cloud platform, distributing requests across multiple service instances based on health and availability.

## 📋 Requirements

### Core Features
- [ ] **Request Routing**
  - Route requests to appropriate service instances
  - Support multiple routing algorithms (Round Robin, Least Connections, Health-based)
  - Handle dynamic service discovery

- [ ] **Health Monitoring**
  - Monitor health of all service instances
  - Remove unhealthy instances from rotation
  - Automatic recovery when instances become healthy again

- [ ] **Port Management**
  - Manage port assignments per client system
  - Dynamic port allocation and deallocation
  - Port conflict resolution

- [ ] **Load Distribution**
  - Distribute load across multiple instances
  - Implement sticky sessions when needed
  - Handle request queuing during high load

- [ ] **API Gateway Features**
  - Rate limiting per client/user
  - Request/response transformation
  - Authentication and authorization
  - Request logging and monitoring

### Technical Requirements
- **Language**: Node.js, Go, or Python
- **Protocol Support**: HTTP/HTTPS, WebSocket
- **Load Balancing**: Multiple algorithms
- **Health Checks**: Configurable intervals and timeouts
- **Monitoring**: Real-time metrics and logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │◄──►│   Load Balancer │◄──►│   Service       │
│   Requests      │    │   (This Team)   │    │   Instances     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Orchestrator  │    │   Service       │
                       │   (Team 3)      │    │   Discovery     │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
team2-load-balancer/
├── README.md
├── package.json
├── src/
│   ├── core/
│   │   ├── loadBalancer.js
│   │   ├── healthChecker.js
│   │   ├── portManager.js
│   │   └── routingEngine.js
│   ├── algorithms/
│   │   ├── roundRobin.js
│   │   ├── leastConnections.js
│   │   ├── healthBased.js
│   │   └── weightedRoundRobin.js
│   ├── middleware/
│   │   ├── auth.js
│   │   ├── rateLimit.js
│   │   ├── logging.js
│   │   └── cors.js
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.js
│   │   │   ├── metrics.js
│   │   │   └── admin.js
│   │   └── server.js
│   ├── config/
│   │   ├── default.js
│   │   └── production.js
│   └── utils/
│       ├── logger.js
│       └── helpers.js
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
├── docker/
│   └── Dockerfile
└── docs/
    ├── api.md
    └── deployment.md
```

## 🚀 Getting Started

### Prerequisites
- Node.js (v16+) or Go (1.19+) or Python (3.8+)
- Docker
- Redis (for session storage)

### ⚠️ Collaboration Requirements
- **Day 1**: Develop load balancer service independently
- **Day 2**: Meet with other teams to discuss API contracts and routing
- **Day 3**: Collaborate on final docker-compose.yml integration and prepare presentation
- **Integration Points**: Must coordinate with Teams 1, 3, and 6 for API integration

### Installation
```bash
cd teams/team2-load-balancer
npm install
npm start
```

### Development
```bash
# Start development server
npm run dev

# Run tests
npm test

# Run load tests
npm run load-test
```

## 🔌 API Endpoints

### Health Check API
- `GET /health` - Load balancer health status
- `GET /health/instances` - All instance health status
- `POST /health/check/:instanceId` - Manual health check

### Metrics API
- `GET /metrics` - Load balancer metrics
- `GET /metrics/instances` - Instance-specific metrics
- `GET /metrics/requests` - Request statistics

### Admin API
- `GET /admin/instances` - List all instances
- `POST /admin/instances` - Add new instance
- `DELETE /admin/instances/:id` - Remove instance
- `PUT /admin/instances/:id/weight` - Update instance weight

## ⚖️ Load Balancing Algorithms

### 1. Round Robin
- Distribute requests sequentially across instances
- Simple and predictable
- Good for evenly distributed load

### 2. Least Connections
- Route to instance with fewest active connections
- Better for long-running requests
- Requires connection tracking

### 3. Health-Based
- Route to healthiest instances first
- Considers CPU, memory, response time
- Automatic failover to healthy instances

### 4. Weighted Round Robin
- Assign weights to instances based on capacity
- Higher capacity instances get more requests
- Useful for heterogeneous infrastructure

## 🔍 Health Checking

### Health Check Types
- **HTTP Health Check**: GET request to `/health` endpoint
- **TCP Health Check**: Simple port connectivity test
- **Custom Health Check**: Custom script or command

### Configuration
```javascript
{
  "healthCheck": {
    "interval": 30000,        // 30 seconds
    "timeout": 5000,          // 5 seconds
    "unhealthyThreshold": 3,  // Mark unhealthy after 3 failures
    "healthyThreshold": 2     // Mark healthy after 2 successes
  }
}
```

## 📊 Monitoring & Metrics

### Key Metrics
- **Request Rate**: Requests per second
- **Response Time**: Average, 95th percentile, 99th percentile
- **Error Rate**: Percentage of failed requests
- **Instance Health**: Number of healthy/unhealthy instances
- **Connection Count**: Active connections per instance

### Metrics Collection
- Real-time metrics via Prometheus
- Historical data storage
- Alerting on thresholds
- Dashboard integration

## 🔒 Security Features

### Authentication & Authorization
- API key authentication
- JWT token validation
- Role-based access control
- Rate limiting per user/client

### Request Security
- Input validation and sanitization
- CORS configuration
- Request size limits
- Malicious request filtering

## 🧪 Testing Strategy

### Unit Tests
- Load balancing algorithm tests
- Health check functionality
- Port management tests
- Middleware tests

### Integration Tests
- End-to-end request routing
- Health check integration
- Instance management
- Metrics collection

### Load Tests
- High traffic simulation
- Concurrent request handling
- Memory and CPU usage under load
- Failure recovery testing

## 📈 Performance Optimization

### Caching
- Response caching for static content
- Connection pooling
- DNS caching
- Health check result caching

### Connection Management
- Keep-alive connections
- Connection pooling
- Timeout configuration
- Retry mechanisms

## 🔄 Integration Points

### With Team 1 (UI)
- Provide health status for dashboard
- Expose metrics for monitoring
- Handle UI API requests

### With Team 3 (Orchestrator)
- Receive instance health updates
- Request new instances when needed
- Report load metrics for scaling decisions

### With Team 6 (Billing)
- Track request counts for billing
- Monitor resource usage
- Provide usage analytics

## 🚨 Error Handling

### Failure Scenarios
- Instance becomes unavailable
- Network connectivity issues
- High load situations
- Configuration errors

### Recovery Mechanisms
- Automatic failover to healthy instances
- Circuit breaker pattern
- Graceful degradation
- Health check retry logic

## 📝 Configuration

### Environment Variables
```bash
PORT=3000
REDIS_URL=redis://localhost:6379
HEALTH_CHECK_INTERVAL=30000
LOG_LEVEL=info
```

### Configuration File
```javascript
{
  "port": 3000,
  "algorithms": {
    "default": "roundRobin",
    "healthBased": {
      "enabled": true,
      "weight": 0.7
    }
  },
  "healthCheck": {
    "interval": 30000,
    "timeout": 5000
  },
  "rateLimit": {
    "enabled": true,
    "requestsPerMinute": 1000
  }
}
```

## 🎯 Success Criteria

- [ ] Successfully routes requests to healthy instances
- [ ] Handles high traffic without performance degradation
- [ ] Automatically removes unhealthy instances
- [ ] Provides accurate metrics and monitoring
- [ ] Integrates seamlessly with other teams
- [ ] Maintains 99.9% uptime under normal conditions
- [ ] Recovers automatically from failures

## 📞 Support

For technical questions or integration issues, contact the team lead or refer to the main project documentation. 