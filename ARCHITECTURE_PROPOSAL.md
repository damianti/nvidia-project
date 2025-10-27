# NVIDIA Project - Architecture Proposal

## Overview
This document outlines the proposed microservices architecture for the NVIDIA container orchestration platform.

## Current Architecture Issues
- Multiple services expose ports directly to the frontend
- No centralized authentication/authorization
- No rate limiting or traffic control
- Difficult to scale and maintain
- No service discovery between internal services

## Proposed Architecture

### 1. API Gateway (Single Entry Point)
**Port:** 8080
**Responsibilities:**
- Single entry point for all external traffic
- JWT authentication and authorization
- Rate limiting per user/IP
- Request routing to internal services
- SSL termination
- Request/response logging and monitoring

**Routes:**
```
/api/auth/* → Auth Service:3001
/api/images/* → Image Service:3002
/api/containers/* → Orchestrator:3003
/api/load-balancer/* → Load Balancer:3004
/api/service-discovery/* → Service Discovery:3005
/ui/* → UI Service:3000
```

### 2. Service Discovery (Consul)
**Port:** 8500
**Namespaces:**
- `internal-services` - System services (orchestrator, load-balancer, etc.)
- `client-containers` - Customer containers

**Responsibilities:**
- Service registration and health checks
- Service discovery for internal communication
- DNS resolution for services
- Health monitoring and automatic cleanup

### 3. Load Balancer Service
**Port:** 3004 (internal)
**Responsibilities:**
- Round-robin, Least Connection, Weighted algorithms
- Health checks before routing
- Port mapping (external port → internal service)
- Traffic distribution to customer containers
- Metrics collection (RPS, response times)

### 4. Orchestrator Service
**Port:** 3003 (internal)
**Responsibilities:**
- Container lifecycle management (create, start, stop, delete)
- Port management and allocation
- Docker operations
- Health data collection (CPU, Memory, FS)
- Integration with Service Discovery

### 5. Auth Service
**Port:** 3001 (internal)
**Responsibilities:**
- User authentication (signup, signin)
- JWT token generation and validation
- User management
- Session management

### 6. Image Service
**Port:** 3002 (internal)
**Responsibilities:**
- Docker image management
- Image upload and processing
- Image metadata storage
- Image scanning and optimization

### 7. UI Service
**Port:** 3000 (internal)
**Responsibilities:**
- Frontend application
- User interface for container management
- Dashboard and monitoring views

## Communication Patterns

### Synchronous Communication
- Frontend ↔ API Gateway (HTTP/HTTPS)
- API Gateway ↔ Internal Services (HTTP)
- Load Balancer ↔ Customer Containers (HTTP)

### Asynchronous Communication
- Orchestrator → Service Discovery (service registration)
- Service Discovery → Load Balancer (service updates)
- All services → Observability (metrics, logs)

## Data Storage

### PostgreSQL
- User data
- Image metadata
- Container metadata
- Port allocations
- Billing data
- Historical metrics

### Redis
- Session storage
- Cache for frequent queries
- Rate limiting counters
- Temporary service state

### Consul
- Service registry
- Health check results
- Service configuration
- Service discovery data

## Implementation Phases

### Phase 1: Core Infrastructure
1. Port Management System
2. Service Discovery (Consul)
3. Basic Load Balancer

### Phase 2: Service Separation
1. API Gateway implementation
2. Auth Service extraction
3. Image Service extraction

### Phase 3: Advanced Features
1. Advanced Load Balancer algorithms
2. Observability and monitoring
3. Billing and metering
4. Geographic routing

## Security Considerations
- All internal services communicate over private network
- JWT tokens for authentication
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration for frontend

## Scalability Considerations
- Horizontal scaling of all services
- Database connection pooling
- Redis clustering for high availability
- Load balancer can distribute across multiple instances
- Service discovery enables dynamic scaling

## Monitoring and Observability
- Centralized logging
- Metrics collection (Prometheus)
- Health checks and alerts
- Performance monitoring
- Billing data collection

## Benefits of This Architecture
- Single entry point simplifies client integration
- Service separation enables independent scaling
- Asynchronous communication improves resilience
- Service discovery enables dynamic service management
- Clear separation of concerns
- Easy to test and maintain individual services
