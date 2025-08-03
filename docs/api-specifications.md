# API Specifications

## 🎯 Overview

This document defines the API specifications for all services in the NVIDIA ScaleUp hackathon project. All APIs follow RESTful principles and use JSON for data exchange.

## 📋 Common API Standards

### Base URL
- **Development**: `http://localhost:3002` (via Load Balancer)
- **Production**: `https://api.nvidia-cloud.com`

### Authentication
All APIs require authentication using JWT tokens:

```http
Authorization: Bearer <jwt_token>
```

### Response Format
Standard response format for all APIs:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2025-01-10T10:30:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {}
  },
  "timestamp": "2025-01-10T10:30:00Z"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 🔐 Authentication APIs

### Register User
```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2025-01-10T10:30:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Login User
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "name": "John Doe"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

## 🖼️ Container Management APIs

### List Containers
```http
GET /api/containers
```

**Query Parameters:**
- `status` (optional): Filter by container status
- `user_id` (optional): Filter by user ID
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "containers": [
      {
        "id": "container_123",
        "user_id": "user_123",
        "name": "web-app",
        "image": "nginx:alpine",
        "status": "running",
        "ports": ["80:80"],
        "resources": {
          "cpu": "1.0",
          "memory": "512m"
        },
        "created_at": "2025-01-10T10:30:00Z",
        "updated_at": "2025-01-10T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

### Create Container
```http
POST /api/containers
```

**Request Body:**
```json
{
  "name": "web-app",
  "image": "nginx:alpine",
  "ports": ["80:80"],
  "environment": {
    "NODE_ENV": "production"
  },
  "resources": {
    "cpu": "1.0",
    "memory": "512m",
    "storage": "10Gi"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "container": {
      "id": "container_123",
      "user_id": "user_123",
      "name": "web-app",
      "image": "nginx:alpine",
      "status": "creating",
      "ports": ["80:80"],
      "resources": {
        "cpu": "1.0",
        "memory": "512m",
        "storage": "10Gi"
      },
      "created_at": "2025-01-10T10:30:00Z"
    }
  }
}
```

### Get Container Details
```http
GET /api/containers/{container_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "container": {
      "id": "container_123",
      "user_id": "user_123",
      "name": "web-app",
      "image": "nginx:alpine",
      "status": "running",
      "ports": ["80:80"],
      "resources": {
        "cpu": "1.0",
        "memory": "512m",
        "storage": "10Gi"
      },
      "metrics": {
        "cpu_usage": 25.5,
        "memory_usage": 45.2,
        "network_io": "1.2MB/s"
      },
      "created_at": "2025-01-10T10:30:00Z",
      "updated_at": "2025-01-10T10:30:00Z"
    }
  }
}
```

### Start Container
```http
PUT /api/containers/{container_id}/start
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Container started successfully",
    "container_id": "container_123"
  }
}
```

### Stop Container
```http
PUT /api/containers/{container_id}/stop
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Container stopped successfully",
    "container_id": "container_123"
  }
}
```

### Scale Container
```http
POST /api/containers/{container_id}/scale
```

**Request Body:**
```json
{
  "replicas": 3,
  "strategy": "rolling"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Container scaled successfully",
    "container_id": "container_123",
    "replicas": 3
  }
}
```

### Delete Container
```http
DELETE /api/containers/{container_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Container deleted successfully",
    "container_id": "container_123"
  }
}
```

## 📊 Monitoring APIs

### Get System Health
```http
GET /api/health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "services": {
      "load_balancer": "healthy",
      "orchestrator": "healthy",
      "billing": "healthy",
      "database": "healthy",
      "redis": "healthy"
    },
    "timestamp": "2025-01-10T10:30:00Z"
  }
}
```

### Get Container Metrics
```http
GET /api/containers/{container_id}/metrics
```

**Query Parameters:**
- `period` (optional): Time period (1h, 24h, 7d, 30d)

**Response:**
```json
{
  "success": true,
  "data": {
    "container_id": "container_123",
    "metrics": {
      "cpu": [
        {
          "timestamp": "2025-01-10T10:00:00Z",
          "value": 25.5
        }
      ],
      "memory": [
        {
          "timestamp": "2025-01-10T10:00:00Z",
          "value": 45.2
        }
      ],
      "network": [
        {
          "timestamp": "2025-01-10T10:00:00Z",
          "bytes_in": 1024,
          "bytes_out": 2048
        }
      ]
    }
  }
}
```

### Get System Metrics
```http
GET /api/metrics
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "total_containers": 15,
      "running_containers": 12,
      "total_cpu_usage": 65.5,
      "total_memory_usage": 78.2,
      "total_network_io": "5.2MB/s"
    },
    "requests": {
      "total_requests": 15000,
      "requests_per_second": 250,
      "error_rate": 0.5
    }
  }
}
```

## 💰 Billing APIs

### Get User Billing Summary
```http
GET /api/billing/summary
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user_123",
    "current_period": {
      "start_date": "2025-01-01T00:00:00Z",
      "end_date": "2025-01-31T23:59:59Z",
      "total_cost": 45.67,
      "currency": "USD"
    },
    "containers": [
      {
        "container_id": "container_123",
        "name": "web-app",
        "cost": 23.45,
        "usage": {
          "cpu_hours": 720,
          "memory_gb_hours": 1440,
          "storage_gb_days": 30
        }
      }
    ]
  }
}
```

### Get Billing History
```http
GET /api/billing/history
```

**Query Parameters:**
- `start_date` (optional): Start date (ISO 8601)
- `end_date` (optional): End date (ISO 8601)
- `page` (optional): Page number
- `limit` (optional): Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "bills": [
      {
        "id": "bill_123",
        "period": "2025-01-01 to 2025-01-31",
        "amount": 45.67,
        "currency": "USD",
        "status": "paid",
        "due_date": "2025-02-15T00:00:00Z",
        "paid_date": "2025-02-10T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

### Get Container Usage
```http
GET /api/billing/containers/{container_id}/usage
```

**Query Parameters:**
- `start_date` (optional): Start date (ISO 8601)
- `end_date` (optional): End date (ISO 8601)

**Response:**
```json
{
  "success": true,
  "data": {
    "container_id": "container_123",
    "usage": {
      "cpu": {
        "total_hours": 720,
        "cost": 36.00
      },
      "memory": {
        "total_gb_hours": 1440,
        "cost": 7.20
      },
      "storage": {
        "total_gb_days": 30,
        "cost": 3.00
      },
      "network": {
        "total_gb": 50,
        "cost": 0.50
      }
    },
    "total_cost": 46.70
  }
}
```

## 🔍 Service Discovery APIs

### List Services
```http
GET /api/services
```

**Response:**
```json
{
  "success": true,
  "data": {
    "services": [
      {
        "id": "service_123",
        "name": "web-app",
        "version": "1.0.0",
        "endpoint": "http://web-app:80",
        "health": "healthy",
        "instances": 3,
        "metadata": {
          "environment": "production",
          "team": "frontend"
        }
      }
    ]
  }
}
```

### Get Service Details
```http
GET /api/services/{service_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "service": {
      "id": "service_123",
      "name": "web-app",
      "version": "1.0.0",
      "endpoint": "http://web-app:80",
      "health": "healthy",
      "instances": [
        {
          "id": "instance_1",
          "endpoint": "http://web-app-1:80",
          "health": "healthy",
          "metrics": {
            "cpu_usage": 25.5,
            "memory_usage": 45.2
          }
        }
      ],
      "metadata": {
        "environment": "production",
        "team": "frontend"
      }
    }
  }
}
```

## 🧪 Testing APIs

### Start Load Test
```http
POST /api/testing/load
```

**Request Body:**
```json
{
  "scenario": "web_app",
  "duration": 300,
  "users": 100,
  "ramp_up_time": 60
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "test_id": "test_123",
    "status": "running",
    "scenario": "web_app",
    "started_at": "2025-01-10T10:30:00Z"
  }
}
```

### Get Test Results
```http
GET /api/testing/results/{test_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "test_id": "test_123",
    "status": "completed",
    "scenario": "web_app",
    "results": {
      "total_requests": 15000,
      "successful_requests": 14950,
      "failed_requests": 50,
      "avg_response_time": 245,
      "p95_response_time": 450,
      "p99_response_time": 800,
      "requests_per_second": 50
    },
    "started_at": "2025-01-10T10:30:00Z",
    "completed_at": "2025-01-10T10:35:00Z"
  }
}
```

## 🔌 WebSocket APIs

### Real-time Updates
```http
WebSocket: ws://localhost:3002/ws
```

**Connection Parameters:**
- `token`: JWT authentication token

**Event Types:**

#### Container Status Update
```json
{
  "type": "container_status_update",
  "data": {
    "container_id": "container_123",
    "status": "running",
    "timestamp": "2025-01-10T10:30:00Z"
  }
}
```

#### Metrics Update
```json
{
  "type": "metrics_update",
  "data": {
    "container_id": "container_123",
    "metrics": {
      "cpu_usage": 25.5,
      "memory_usage": 45.2,
      "network_io": "1.2MB/s"
    },
    "timestamp": "2025-01-10T10:30:00Z"
  }
}
```

#### Billing Update
```json
{
  "type": "billing_update",
  "data": {
    "user_id": "user_123",
    "container_id": "container_123",
    "cost": 0.15,
    "timestamp": "2025-01-10T10:30:00Z"
  }
}
```

## 📝 Error Codes

### Common Error Codes
- `VALIDATION_ERROR` - Invalid input parameters
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication required
- `FORBIDDEN` - Insufficient permissions
- `RESOURCE_EXHAUSTED` - Resource limits exceeded
- `SERVICE_UNAVAILABLE` - Service temporarily unavailable
- `INTERNAL_ERROR` - Internal server error

### Error Response Examples

#### Validation Error
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "email": "Invalid email format",
      "password": "Password must be at least 8 characters"
    }
  }
}
```

#### Resource Not Found
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Container not found",
    "details": {
      "container_id": "container_123"
    }
  }
}
```

## 🔒 Rate Limiting

### Rate Limits
- **Authentication APIs**: 10 requests per minute
- **Container APIs**: 100 requests per minute
- **Monitoring APIs**: 60 requests per minute
- **Billing APIs**: 30 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641816000
```

## 📚 SDK Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:3002',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Create container
const createContainer = async (containerData) => {
  try {
    const response = await api.post('/api/containers', containerData);
    return response.data;
  } catch (error) {
    console.error('Error creating container:', error.response.data);
    throw error;
  }
};
```

### Python
```python
import requests

class NvidiaCloudAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_container(self, container_data):
        response = requests.post(
            f'{self.base_url}/api/containers',
            json=container_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

### cURL Examples

#### Create Container
```bash
curl -X POST http://localhost:3002/api/containers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-app",
    "image": "nginx:alpine",
    "ports": ["80:80"],
    "resources": {
      "cpu": "1.0",
      "memory": "512m"
    }
  }'
```

#### Get Container Metrics
```bash
curl -X GET http://localhost:3002/api/containers/container_123/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 API Versioning

### Version Header
```http
Accept: application/vnd.nvidia-cloud.v1+json
```

### Version in URL (Alternative)
```http
GET /api/v1/containers
```

### Deprecation Notice
When APIs are deprecated, they will include a deprecation header:
```http
Deprecation: true
Sunset: 2025-12-31T23:59:59Z
```

## 📊 API Analytics

### Request Logging
All API requests are logged with the following information:
- Request method and path
- Response status code
- Response time
- User ID (if authenticated)
- IP address
- User agent

### Metrics Available
- Request volume by endpoint
- Response time percentiles
- Error rates by endpoint
- User activity patterns
- API usage trends 