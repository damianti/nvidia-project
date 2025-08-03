# Deployment Guide

## 🚀 Overview

This guide provides step-by-step instructions for deploying the NVIDIA ScaleUp hackathon project. The system can be deployed in multiple environments: development, testing, and production.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: Version 2.30+
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: Minimum 20GB free space
- **CPU**: 4 cores minimum (8 cores recommended)

### Software Installation

#### Docker Installation
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS
brew install --cask docker

# Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### Docker Compose Installation
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🏗️ Project Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd nvidia-project
```

### 2. Environment Configuration
Create environment files for different environments:

#### Development Environment
```bash
# Create .env file
cp .env.example .env

# Edit .env file
nano .env
```

**Example .env file:**
```bash
# Database Configuration
DATABASE_URL=postgresql://nvidia_user:nvidia_password@postgres:5432/nvidia_cloud
REDIS_URL=redis://redis:6379
RABBITMQ_URL=amqp://nvidia_user:nvidia_password@rabbitmq:5672/

# Service Ports
UI_PORT=3001
LOAD_BALANCER_PORT=3002
ORCHESTRATOR_PORT=3003
BILLING_PORT=3006
WORKLOAD_PORT=3007

# Monitoring Ports
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090

# Development Tools Ports
ADMINER_PORT=8082
REDIS_COMMANDER_PORT=8083

# Security
JWT_SECRET=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-32-character-encryption-key

# Logging
LOG_LEVEL=debug
```

#### Production Environment
```bash
# Create production environment file
cp .env.example .env.production

# Edit production environment
nano .env.production
```

**Production .env file:**
```bash
# Database Configuration
DATABASE_URL=postgresql://prod_user:prod_password@prod-db:5432/nvidia_cloud
REDIS_URL=redis://prod-redis:6379
RABBITMQ_URL=amqp://prod_user:prod_password@prod-rabbitmq:5672/

# Service Ports
UI_PORT=80
LOAD_BALANCER_PORT=443
ORCHESTRATOR_PORT=3003
BILLING_PORT=3006
WORKLOAD_PORT=3007

# Monitoring Ports
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090

# Security
JWT_SECRET=your-production-jwt-secret
ENCRYPTION_KEY=your-production-encryption-key

# Logging
LOG_LEVEL=info

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/nvidia-cloud.crt
SSL_KEY_PATH=/etc/ssl/private/nvidia-cloud.key
```

### 3. Database Initialization
Create the database initialization script:

```bash
# Create database init directory
mkdir -p infrastructure/databases

# Create init.sql file
nano infrastructure/databases/init.sql
```

**Example init.sql:**
```sql
-- Create database if not exists
CREATE DATABASE IF NOT EXISTS nvidia_cloud;

-- Use the database
\c nvidia_cloud;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create containers table
CREATE TABLE IF NOT EXISTS containers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    image VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'created',
    ports JSONB,
    environment JSONB,
    resources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create usage table
CREATE TABLE IF NOT EXISTS usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    container_id UUID REFERENCES containers(id),
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    network_io BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create billing table
CREATE TABLE IF NOT EXISTS billing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    container_id UUID REFERENCES containers(id),
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_containers_user_id ON containers(user_id);
CREATE INDEX idx_containers_status ON containers(status);
CREATE INDEX idx_usage_container_id ON usage(container_id);
CREATE INDEX idx_usage_timestamp ON usage(timestamp);
CREATE INDEX idx_billing_user_id ON billing(user_id);
CREATE INDEX idx_billing_period ON billing(period_start, period_end);
```

## 🚀 Deployment Steps

### Development Deployment

#### 1. Start Infrastructure Services
```bash
# Start only infrastructure services first
docker-compose up -d postgres redis rabbitmq prometheus grafana

# Wait for services to be ready
docker-compose ps
```

#### 2. Initialize Database
```bash
# Wait for PostgreSQL to be ready
sleep 30

# Check database connection
docker-compose exec postgres psql -U nvidia_user -d nvidia_cloud -c "\dt"
```

#### 3. Start Application Services
```bash
# Start all application services
docker-compose up -d team1-ui team2-load-balancer team3-orchestrator team6-billing team7-client-workload

# Check all services
docker-compose ps
```

#### 4. Verify Deployment
```bash
# Check service health
curl http://localhost:3002/api/health

# Check UI
curl http://localhost:3001

# Check Grafana
curl http://localhost:3000
```

### Production Deployment

#### 1. Production Environment Setup
```bash
# Use production environment
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml

# Set production environment variables
export NODE_ENV=production
export PYTHON_ENV=production
```

#### 2. SSL/TLS Configuration
```bash
# Create SSL certificates directory
mkdir -p ssl

# Generate self-signed certificates (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nvidia-cloud.key \
  -out ssl/nvidia-cloud.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=nvidia-cloud.com"
```

#### 3. Production Docker Compose
Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Production-specific configurations
  team1-ui:
    environment:
      NODE_ENV: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  team2-load-balancer:
    environment:
      NODE_ENV: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  team3-orchestrator:
    environment:
      PYTHON_ENV: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  team6-billing:
    environment:
      PYTHON_ENV: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  team7-client-workload:
    environment:
      PYTHON_ENV: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  # Production database with persistence
  postgres:
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # Production Redis with persistence
  redis:
    volumes:
      - redis_prod_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

volumes:
  postgres_prod_data:
    driver: local
  redis_prod_data:
    driver: local
```

#### 4. Deploy to Production
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check deployment status
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

## 🔧 Configuration Management

### Environment-Specific Configurations

#### Development Configuration
```bash
# Development-specific settings
LOG_LEVEL=debug
DEBUG=true
CORS_ORIGIN=http://localhost:3001
```

#### Testing Configuration
```bash
# Testing-specific settings
LOG_LEVEL=info
DEBUG=false
CORS_ORIGIN=http://localhost:3001
TEST_MODE=true
```

#### Production Configuration
```bash
# Production-specific settings
LOG_LEVEL=warn
DEBUG=false
CORS_ORIGIN=https://nvidia-cloud.com
SECURE_COOKIES=true
```

### Service Configuration Files

#### Load Balancer Configuration
```javascript
// teams/team2-load-balancer/config/production.js
module.exports = {
  port: process.env.LOAD_BALANCER_PORT || 3002,
  redis: {
    url: process.env.REDIS_URL
  },
  rateLimit: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100 // limit each IP to 100 requests per windowMs
  },
  cors: {
    origin: process.env.CORS_ORIGIN,
    credentials: true
  }
};
```

#### Orchestrator Configuration
```python
# teams/team3-orchestrator/config/production.py
import os

config = {
    'database': {
        'url': os.getenv('DATABASE_URL'),
        'pool_size': 20,
        'max_overflow': 30
    },
    'redis': {
        'url': os.getenv('REDIS_URL'),
        'pool_size': 10
    },
    'rabbitmq': {
        'url': os.getenv('RABBITMQ_URL'),
        'connection_pool_size': 5
    },
    'docker': {
        'host': os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock'),
        'timeout': 30
    },
    'scaling': {
        'min_replicas': 1,
        'max_replicas': 10,
        'cpu_threshold': 80,
        'memory_threshold': 85
    }
}
```

## 📊 Monitoring Setup

### Prometheus Configuration
Create `infrastructure/monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'load-balancer'
    static_configs:
      - targets: ['team2-load-balancer:3000']
    metrics_path: '/metrics'

  - job_name: 'orchestrator'
    static_configs:
      - targets: ['team3-orchestrator:3000']
    metrics_path: '/metrics'

  - job_name: 'billing'
    static_configs:
      - targets: ['team6-billing:3000']
    metrics_path: '/metrics'

  - job_name: 'workload'
    static_configs:
      - targets: ['team7-client-workload:3000']
    metrics_path: '/metrics'
```

### Grafana Dashboards
Create dashboard configuration:

```bash
# Create Grafana configuration directories
mkdir -p infrastructure/monitoring/grafana/dashboards
mkdir -p infrastructure/monitoring/grafana/datasources

# Create datasource configuration
cat > infrastructure/monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
```

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key \
  -out ssl/certificate.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Configure Nginx for SSL termination
cat > nginx.conf << EOF
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/certificate.crt;
    ssl_certificate_key /etc/ssl/private/private.key;

    location / {
        proxy_pass http://team2-load-balancer:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
```

### Firewall Configuration
```bash
# Configure firewall rules
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus

# Enable firewall
sudo ufw enable
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker images
      run: |
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml push
    
    - name: Deploy to production
      run: |
        ssh ${{ secrets.SSH_HOST }} << 'EOF'
          cd /opt/nvidia-project
          git pull origin main
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        EOF
```

## 🧪 Testing Deployment

### Health Checks
```bash
# Check all services
./scripts/health-check.sh

# Health check script content
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash

echo "Checking service health..."

# Check UI
curl -f http://localhost:3001 || echo "UI service is down"

# Check Load Balancer
curl -f http://localhost:3002/api/health || echo "Load Balancer is down"

# Check Orchestrator
curl -f http://localhost:3003/api/health || echo "Orchestrator is down"

# Check Billing
curl -f http://localhost:3006/api/health || echo "Billing service is down"

# Check Workload
curl -f http://localhost:3007/api/health || echo "Workload service is down"

# Check Grafana
curl -f http://localhost:3000 || echo "Grafana is down"

# Check Prometheus
curl -f http://localhost:9090 || echo "Prometheus is down"

echo "Health check completed"
EOF

chmod +x scripts/health-check.sh
```

### Load Testing
```bash
# Run load tests
docker-compose exec team7-client-workload python -m pytest tests/load/ -v

# Manual load testing
curl -X POST http://localhost:3007/api/testing/load \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "web_app",
    "duration": 60,
    "users": 10
  }'
```

## 📈 Performance Optimization

### Resource Limits
```yaml
# Add to docker-compose.yml
services:
  team1-ui:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Database Optimization
```sql
-- Add database indexes for performance
CREATE INDEX CONCURRENTLY idx_usage_user_timestamp ON usage(user_id, timestamp);
CREATE INDEX CONCURRENTLY idx_billing_user_period ON billing(user_id, period_start, period_end);

-- Configure connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service logs
docker-compose logs team1-ui

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart team1-ui
```

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec postgres psql -U nvidia_user -d nvidia_cloud -c "SELECT 1;"

# Check database logs
docker-compose logs postgres
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limits
docker-compose down
docker system prune -f
docker-compose up -d
```

### Log Analysis
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs -f team2-load-balancer

# Search logs for errors
docker-compose logs | grep ERROR
```

## 📚 Additional Resources

### Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### Monitoring Tools
- [Prometheus](https://prometheus.io/) - Metrics collection
- [Grafana](https://grafana.com/) - Visualization
- [Jaeger](https://www.jaegertracing.io/) - Distributed tracing
- [ELK Stack](https://www.elastic.co/elk-stack) - Log management

### Security Tools
- [Vault](https://www.vaultproject.io/) - Secret management
- [Certbot](https://certbot.eff.org/) - SSL certificate management
- [Fail2ban](https://www.fail2ban.org/) - Intrusion prevention 