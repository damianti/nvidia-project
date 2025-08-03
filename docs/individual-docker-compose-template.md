# Individual Docker Compose Template

## 🎯 Purpose

This template shows how each team should create their own docker-compose.yml during the independent development phase (Weeks 1-2). Teams will later collaborate to create the final integrated docker-compose.yml.

## 📋 Template for Each Team

### Team 1 - UI Service Template
```yaml
# teams/team1-ui/docker-compose.yml
version: '3.8'

services:
  ui:
    build: .
    container_name: team1-ui-dev
    ports:
      - "3001:3000"
    environment:
      - NODE_ENV=development
      - REACT_APP_API_URL=http://localhost:3002
      - REACT_APP_WS_URL=ws://localhost:3002
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - team1-network

  # Mock services for development (remove in final integration)
  mock-load-balancer:
    image: nginx:alpine
    container_name: mock-load-balancer
    ports:
      - "3002:80"
    volumes:
      - ./mock-data:/usr/share/nginx/html
    networks:
      - team1-network

  mock-orchestrator:
    image: nginx:alpine
    container_name: mock-orchestrator
    ports:
      - "3003:80"
    volumes:
      - ./mock-data:/usr/share/nginx/html
    networks:
      - team1-network

  mock-billing:
    image: nginx:alpine
    container_name: mock-billing
    ports:
      - "3006:80"
    volumes:
      - ./mock-data:/usr/share/nginx/html
    networks:
      - team1-network

networks:
  team1-network:
    driver: bridge
```

### Team 2 - Load Balancer Template
```yaml
# teams/team2-load-balancer/docker-compose.yml
version: '3.8'

services:
  load-balancer:
    build: .
    container_name: team2-load-balancer-dev
    ports:
      - "3002:3000"
    environment:
      - NODE_ENV=development
      - REDIS_URL=redis://redis:6379
      - ORCHESTRATOR_URL=http://orchestrator:3000
      - BILLING_URL=http://billing:3000
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - team2-network
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: team2-redis
    ports:
      - "6379:6379"
    networks:
      - team2-network

  # Mock services for development
  mock-orchestrator:
    image: nginx:alpine
    container_name: mock-orchestrator
    ports:
      - "3003:80"
    networks:
      - team2-network

  mock-billing:
    image: nginx:alpine
    container_name: mock-billing
    ports:
      - "3006:80"
    networks:
      - team2-network

networks:
  team2-network:
    driver: bridge
```

### Team 3 - Orchestrator Template
```yaml
# teams/team3-orchestrator/docker-compose.yml
version: '3.8'

services:
  orchestrator:
    build: .
    container_name: team3-orchestrator-dev
    ports:
      - "3003:3000"
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://nvidia_user:nvidia_password@postgres:5432/nvidia_cloud
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://nvidia_user:nvidia_password@rabbitmq:5672/
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - .:/app
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - team3-network
    depends_on:
      - postgres
      - redis
      - rabbitmq

  postgres:
    image: postgres:15-alpine
    container_name: team3-postgres
    environment:
      POSTGRES_DB: nvidia_cloud
      POSTGRES_USER: nvidia_user
      POSTGRES_PASSWORD: nvidia_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - team3-network

  redis:
    image: redis:7-alpine
    container_name: team3-redis
    ports:
      - "6379:6379"
    networks:
      - team3-network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: team3-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: nvidia_user
      RABBITMQ_DEFAULT_PASS: nvidia_password
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - team3-network

volumes:
  postgres_data:

networks:
  team3-network:
    driver: bridge
```

### Team 6 - Billing Template
```yaml
# teams/team6-billing/docker-compose.yml
version: '3.8'

services:
  billing:
    build: .
    container_name: team6-billing-dev
    ports:
      - "3006:3000"
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://nvidia_user:nvidia_password@postgres:5432/nvidia_cloud
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://nvidia_user:nvidia_password@rabbitmq:5672/
    volumes:
      - .:/app
    networks:
      - team6-network
    depends_on:
      - postgres
      - redis
      - rabbitmq

  postgres:
    image: postgres:15-alpine
    container_name: team6-postgres
    environment:
      POSTGRES_DB: nvidia_cloud
      POSTGRES_USER: nvidia_user
      POSTGRES_PASSWORD: nvidia_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - team6-network

  redis:
    image: redis:7-alpine
    container_name: team6-redis
    ports:
      - "6379:6379"
    networks:
      - team6-network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: team6-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: nvidia_user
      RABBITMQ_DEFAULT_PASS: nvidia_password
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - team6-network

volumes:
  postgres_data:

networks:
  team6-network:
    driver: bridge
```

### Team 7 - Client Workload Template
```yaml
# teams/team7-client-workload/docker-compose.yml
version: '3.8'

services:
  client-workload:
    build: .
    container_name: team7-client-workload-dev
    ports:
      - "3007:3000"
    environment:
      - PYTHONPATH=/app
      - CLOUD_API_URL=http://load-balancer:3000
      - REDIS_URL=redis://redis:6379
      - PROMETHEUS_URL=http://prometheus:9090
    volumes:
      - .:/app
    networks:
      - team7-network
    depends_on:
      - redis
      - prometheus

  redis:
    image: redis:7-alpine
    container_name: team7-redis
    ports:
      - "6379:6379"
    networks:
      - team7-network

  prometheus:
    image: prom/prometheus:latest
    container_name: team7-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - team7-network

  # Mock services for testing
  mock-load-balancer:
    image: nginx:alpine
    container_name: mock-load-balancer
    ports:
      - "3002:80"
    networks:
      - team7-network

networks:
  team7-network:
    driver: bridge
```

## 🔄 Migration to Final Integration

### Day 2: Integration Planning
During Day 2, teams should:

1. **Review Individual Configurations**: Compare each team's docker-compose.yml
2. **Identify Conflicts**: Find port conflicts, network issues, etc.
3. **Plan Integration**: Decide how to merge configurations
4. **Agree on Standards**: Standardize environment variables, service names, etc.

### Day 3: Final Integration
During Day 3, teams should:

1. **Create Integration Template**: One team creates initial integrated template
2. **Iterative Refinement**: All teams review and refine the configuration
3. **Testing**: Test the integrated configuration
4. **Finalization**: Agree on final docker-compose.yml

## 📋 Checklist for Each Team

### Day 1: Individual Development
- [ ] Create Dockerfile for service
- [ ] Create individual docker-compose.yml
- [ ] Test service in isolation
- [ ] Document environment variables
- [ ] Implement health check endpoint
- [ ] **End of Day**: Working individual service

### Day 2: Integration Planning
- [ ] Share docker-compose.yml with other teams
- [ ] Review other teams' configurations
- [ ] Identify potential conflicts
- [ ] Plan integration strategy
- [ ] Start inter-service communication
- [ ] **End of Day**: Integrated services working together

### Day 3: Final Integration
- [ ] Contribute to final docker-compose.yml
- [ ] Test integrated configuration
- [ ] Resolve any integration issues
- [ ] Prepare presentation and demo
- [ ] **End of Day**: Final presentation of complete system

## 🚨 Common Issues and Solutions

### Port Conflicts
**Issue**: Multiple services trying to use the same port
**Solution**: Agree on standard port assignments early

### Network Conflicts
**Issue**: Services can't communicate across networks
**Solution**: Use shared network or external network configuration

### Environment Variable Conflicts
**Issue**: Different teams using different variable names
**Solution**: Standardize environment variable names in Week 3

### Volume Conflicts
**Issue**: Multiple services trying to mount the same volumes
**Solution**: Use named volumes and agree on volume naming

## 📚 Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Networking](https://docs.docker.com/network/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Environment Variables in Docker Compose](https://docs.docker.com/compose/environment-variables/) 