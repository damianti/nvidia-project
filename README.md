# ScaleUp-NVIDIA Hackathon - Tel-Hai Summer 2025

## 🚀 Project Overview

This project simulates a **Distributed Public Cloud Infrastructure** similar to Google Cloud Run, where developers can deploy containerized applications with automated infrastructure and scaling. The system demonstrates core cloud principles including microservices architecture, distributed systems, and DevOps practices.

### 🎯 Project Goals

- **Educational**: Gain hands-on experience with cloud infrastructure components
- **Collaborative**: Work in teams with inter-group coordination
- **Practical**: Build a functional cloud platform with real-world components
- **Scalable**: Implement dynamic resource management and load balancing

## 🏗️ System Architecture

The system consists of several microservices that work together to create a complete cloud platform:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client UI     │    │  Load Balancer  │    │   Orchestrator  │
│   (Team 1)      │◄──►│   (Team 2)      │◄──►│   (Team 3)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Billing       │    │ Service Discovery│    │ Client Workload │
│   (Team 6)      │    │   (Team 3)      │    │   (Team 7)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 👥 Team Assignments

### 🖥️ Team 1 - User Interface (UI)
**Responsibilities:**
- User authentication (Sign-up/Sign-in)
- Docker image upload interface
- Resource configuration for images
- Dashboard showing:
  - Active instances per image
  - Average requests per second
  - Manual instance scaling controls
  - Cost tracking per image

**Technologies:** React/Vue.js, Docker API integration

### ⚖️ Team 2 - Load Balancer (API Gateway)
**Responsibilities:**
- Port management per client system
- Request routing to appropriate services
- Health-based pod selection
- Integration with orchestrator for pod status
- Service routing table management

**Technologies:** Node.js/Go, Reverse proxy, Health checks

### 🔄 Team 3 - Orchestrator & Service Discovery
**Responsibilities:**
- **Orchestrator:**
  - Container lifecycle management (start/stop/scale)
  - Resource monitoring (CPU, Memory, Disk, Status)
  - Dynamic scaling based on workload
  - Health monitoring API
- **Service Discovery:**
  - Service registry implementation
  - Dynamic service discovery
  - Service map visualization

**Technologies:** Python/Go, Docker API, Health monitoring

### 💰 Team 6 - Billing Service
**Responsibilities:**
- Usage monitoring and logging
- Cost calculation per user/service
- Billing API endpoints
- Usage analytics and reporting

**Technologies:** Python/Node.js, Database integration, Analytics

### 🔍 Team 7 - Client Workload
**Responsibilities:**
- Workload simulation application
- Various job types with different parameters
- Integration testing scenarios
- Stress testing and edge case validation

**Technologies:** Python/Node.js, Load testing tools

## 🛠️ Infrastructure Components

### Open Source Components (Configured)
- **Message Queue**: Kafka (for container lifecycle events)
- **Database**: PostgreSQL (for images, containers, users)
- **Container Runtime**: Docker-in-Docker (docker-dind)
- **Service Discovery**: Consul (planned)
- **Monitoring**: Prometheus + Grafana (planned)

### Components Implemented ✅
- ✅ **Orchestrator**: Container lifecycle management, image building, Kafka event publishing
- ✅ **Load Balancer**: Round-robin routing, website URL mapping, Kafka event consumption
- ✅ **API Gateway**: Request routing, caching with sticky sessions, proxy to containers
- ✅ **UI**: Next.js frontend with authentication, image/container management
- 🔄 **Service Discovery**: Consul setup (in progress)

## 📊 Current Status (Updated: November 1, 2025)

### ✅ Completed Features

**Core Functionality:**
- ✅ Complete API Gateway with proxy functionality
- ✅ Load Balancer with Round-Robin algorithm
- ✅ Container lifecycle management (create, start, stop, delete)
- ✅ Image building and management
- ✅ JWT-based authentication
- ✅ Database persistence (PostgreSQL)

**Event-Driven Architecture:**
- ✅ Kafka producer in Orchestrator (publishes container lifecycle events)
- ✅ Kafka consumer in Load Balancer (maintains in-memory container pool)
- ✅ Website URL mapping (website_url → image_id)
- ✅ Event types: `container.created`, `container.started`, `container.stopped`, `container.deleted`

**Load Balancing & Routing:**
- ✅ Round-robin container selection
- ✅ Routing by `website_url` (via Host header)
- ✅ Website URL normalization (removes protocol, handles www)
- ✅ Container pool management (in-memory, thread-safe)

**API Gateway Features:**
- ✅ Routing cache with sticky sessions (by client IP)
- ✅ Cache TTL: 30 minutes
- ✅ Automatic cache cleanup (every 60 seconds)
- ✅ Cache invalidation on container failures
- ✅ Error handling (404, 503, timeouts)

**Architecture:**
- ✅ Clean architecture pattern (repositories, application services, API layer)
- ✅ Thread-safe data structures (RLock for concurrent access)
- ✅ Container networking via docker-dind (ports exposed internally)

### 🔄 In Progress
- Service Discovery with Consul
- Professional logging (structured logs, correlation IDs)
- Comprehensive testing (unit, integration, E2E)

### 📋 Planned Features
- Health checks for individual containers
- Memory-based load balancing (instead of round-robin)
- Authentication moved to API Gateway
- Metrics and monitoring (Prometheus + Grafana)
- Billing service
- Client workload implementation
- UI improvements (health status, metrics dashboard)

## 📁 Project Structure

```
nvidia-project/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── api-specifications.md
│   └── deployment-guide.md
├── teams/
│   ├── team1-ui/
│   ├── team2-load-balancer/
│   ├── team3-orchestrator/
│   ├── team6-billing/
│   └── team7-client-workload/
├── shared/
│   ├── common/
│   ├── config/
│   └── utils/
└── infrastructure/
    ├── databases/
    ├── message-queues/
    └── monitoring/
```

## 🤝 Collaboration Requirements

### ⚠️ IMPORTANT: No Pre-Written Docker Compose
**Teams must work together to create the final docker-compose.yml file!**

### Day 1: Individual Development & API Design
- Each team develops their service independently
- Teams create their own Dockerfile and docker-compose.yml for their service
- Teams define their service's API contracts and interfaces
- **End of Day 1**: Teams must have working individual services

### Day 2: Integration Planning & Testing
- Teams meet to discuss integration points
- Define shared environment variables and configurations
- Plan the final docker-compose.yml structure
- Test inter-service communication
- **End of Day 2**: Teams must have integrated services working together

### Day 3: Final Integration & Presentation Preparation
- Teams work together to create the final docker-compose.yml
- Complete end-to-end testing
- Resolve any remaining integration issues
- Prepare final presentation and demo
- **End of Day 3**: Final presentation of the complete system

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js (v16+) or Python (3.8+)
- Git

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd nvidia-project

# Each team works in their respective folders
cd teams/team1-ui
npm install
npm start
```

### ⚠️ Important Notes
- **No pre-written docker-compose.yml exists**
- Teams must collaborate to create the final integration
- Each team should start with their own service development
- Infrastructure services (PostgreSQL, Redis, etc.) should be set up by teams as needed

## 📋 Development Guidelines

### API Design
- Use RESTful APIs with JSON responses
- Implement proper error handling
- Document all endpoints with OpenAPI/Swagger
- Use consistent naming conventions

### Code Quality
- Follow team-specific coding standards
- Implement unit tests for critical functions
- Use TypeScript for better type safety
- Add comprehensive logging

### Integration
- Define clear interfaces between teams
- Use shared configuration files
- Implement health check endpoints
- Test integration points regularly

### Team Collaboration
- **Weekly Integration Meetings**: Teams must meet to discuss integration progress
- **API Contract Reviews**: Teams review and approve each other's API designs
- **Shared Configuration**: Teams agree on environment variables and service names
- **Docker Compose Collaboration**: Teams work together to create the final docker-compose.yml
- **Integration Testing**: Teams test their services together before final submission

## 📊 Monitoring & Observability

- **Metrics**: CPU, Memory, Disk usage
- **Logging**: Centralized logging with correlation IDs
- **Tracing**: Request tracing across services
- **Alerts**: Health status and performance alerts

## 🧪 Testing Strategy

### Unit Testing
- Each team implements unit tests for their components
- Minimum 80% code coverage

### Integration Testing
- End-to-end testing of complete workflows
- Load testing with realistic scenarios
- Failure recovery testing

### Performance Testing
- Response time benchmarks
- Throughput testing
- Resource utilization under load

## 📝 Documentation Requirements

Each team must provide:
- Component architecture documentation
- API specifications
- Setup and deployment instructions
- Demo video (2-3 minutes)

## 🎯 Success Criteria

- ✅ All services integrate successfully
- ✅ System handles dynamic scaling
- ✅ Load balancing works correctly
- ✅ Billing calculations are accurate
- ✅ UI provides complete functionality
- ✅ System recovers from failures

## 🤝 Collaboration

### Communication
- Regular team sync meetings
- Shared Slack/Discord channel
- Code review process
- Integration testing sessions

### Version Control
- Feature branch workflow
- Pull request reviews
- Semantic versioning
- Release tagging

## 📞 Support & Resources

### Mentors
- Technical guidance available
- Architecture review sessions
- Code review assistance

### Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Microservices Patterns](https://microservices.io/)
- [Cloud Native Architecture](https://www.cncf.io/)

## 🏆 Final Deliverables

1. **Source Code**: Complete implementation in shared repository
2. **Documentation**: Comprehensive project documentation
3. **Demo**: Working system demonstration
4. **Presentation**: Technical overview and lessons learned

---

## 🚦 Getting Started - Quick Demo

### Prerequisites
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker compose version
```

### Running the Project
```bash
# Clone the repository
git clone <repository-url>
cd nvidia-project

# Copy environment variables (if needed)
cp .env.example .env

# Start all services
docker compose up -d

# Check services health
docker compose ps

# View logs
docker compose logs -f orchestrator
docker compose logs -f load-balancer
docker compose logs -f api-gateway
```

### Services Endpoints
- **UI**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Orchestrator API**: http://localhost:3003
- **Load Balancer**: http://localhost:3004
- **Kafka UI**: http://localhost:8081

### Testing the Flow
1. Register a user via UI (http://localhost:3000/signup)
2. Create an image with a `website_url` (e.g., `https://youtube.com`)
3. Create containers for that image
4. Test routing: `curl -H "Host: youtube.com" http://localhost:8080/route`

## 🔧 Architecture Details

### Networking Architecture
Containers are created inside `docker-dind` (Docker-in-Docker) and are accessed from `nvidia-network` through `docker-dind` using dynamically assigned external ports. Ports are only exposed within Docker network (not publicly on host).

### Event Flow
```
Container Created/Started → Orchestrator → Kafka → Load Balancer → Update Pool
                                                                    ↓
Client Request → API Gateway → Load Balancer → Select Container → Proxy
```

### Data Flow
```
UI → API Gateway → Orchestrator → Docker (docker-dind)
                           ↓
                      PostgreSQL
                           ↓
                      Kafka Events
                           ↓
                   Load Balancer (in-memory pool)
```

---
**Project Lead**: Michael, Wael, Bar  
**Hackathon**: ScaleUp-NVIDIA Tel-Hai Summer 2025  
**Last Updated**: November 1, 2025