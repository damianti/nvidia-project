# Shared Common Components

## 🎯 Purpose
This directory contains shared components, utilities, and configurations that can be used across all teams to ensure consistency and reduce code duplication.

## 📁 Structure

```
shared/common/
├── README.md
├── models/
│   ├── user.py
│   ├── container.py
│   ├── service.py
│   └── metrics.py
├── utils/
│   ├── logger.py
│   ├── config.py
│   ├── database.py
│   └── validators.py
├── constants/
│   ├── api_endpoints.py
│   ├── error_codes.py
│   └── status_codes.py
└── schemas/
    ├── requests.py
    ├── responses.py
    └── events.py
```

## 🔧 Common Models

### User Model
```python
class User:
    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
    status: UserStatus
```

### Container Model
```python
class Container:
    id: str
    user_id: str
    image: str
    status: ContainerStatus
    resources: ResourceLimits
    created_at: datetime
    updated_at: datetime
```

### Service Model
```python
class Service:
    id: str
    name: str
    version: str
    endpoint: str
    health_check: str
    metadata: dict
    status: ServiceStatus
```

## 🛠️ Common Utilities

### Logger
Standardized logging across all services:
```python
from shared.common.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Service started successfully")
logger.error("Failed to process request", exc_info=True)
```

### Configuration
Centralized configuration management:
```python
from shared.common.utils.config import get_config

config = get_config()
database_url = config.get("database.url")
redis_url = config.get("redis.url")
```

### Database
Shared database connection utilities:
```python
from shared.common.utils.database import get_db_connection

async with get_db_connection() as conn:
    result = await conn.execute("SELECT * FROM users")
```

## 📋 Common Constants

### API Endpoints
```python
# shared/common/constants/api_endpoints.py
class APIEndpoints:
    HEALTH = "/health"
    METRICS = "/metrics"
    USERS = "/api/users"
    CONTAINERS = "/api/containers"
    SERVICES = "/api/services"
    BILLING = "/api/billing"
```

### Error Codes
```python
# shared/common/constants/error_codes.py
class ErrorCodes:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
```

## 📊 Common Schemas

### Request Schemas
```python
# shared/common/schemas/requests.py
class CreateContainerRequest:
    image: str
    resources: ResourceLimits
    environment: dict = {}
    ports: list = []

class ScaleContainerRequest:
    replicas: int
    strategy: ScalingStrategy = ScalingStrategy.ROLLING
```

### Response Schemas
```python
# shared/common/schemas/responses.py
class APIResponse:
    success: bool
    data: Any = None
    error: str = None
    timestamp: datetime

class HealthResponse:
    status: str
    services: dict
    timestamp: datetime
```

## 🔄 Usage Guidelines

### Importing Shared Components
```python
# Import models
from shared.common.models import User, Container, Service

# Import utilities
from shared.common.utils import logger, config, database

# Import constants
from shared.common.constants import APIEndpoints, ErrorCodes

# Import schemas
from shared.common.schemas import APIResponse, HealthResponse
```

### Adding New Shared Components
1. Create the component in the appropriate directory
2. Add proper documentation and type hints
3. Include unit tests
4. Update this README with usage examples
5. Notify all teams of the new component

### Versioning
- Use semantic versioning for shared components
- Maintain backward compatibility when possible
- Document breaking changes clearly
- Provide migration guides for major changes

## 🧪 Testing

### Unit Tests
```bash
# Run tests for shared components
pytest shared/common/tests/

# Run specific test file
pytest shared/common/tests/test_models.py
```

### Integration Tests
```bash
# Test shared components with other services
pytest tests/integration/test_shared_components.py
```

## 📝 Documentation

### Code Documentation
- All shared components must have docstrings
- Include usage examples in docstrings
- Document all public methods and classes

### API Documentation
- Use OpenAPI/Swagger for API schemas
- Include request/response examples
- Document error codes and messages

## 🔒 Security

### Input Validation
- All shared components should validate inputs
- Use common validation utilities
- Sanitize data to prevent injection attacks

### Authentication
- Shared authentication utilities
- JWT token validation
- Role-based access control helpers

## 🚀 Deployment

### Docker Integration
```dockerfile
# Copy shared components to all service containers
COPY shared/common /app/shared/common
```

### Environment Variables
```bash
# Common environment variables for all services
LOG_LEVEL=info
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

## 🤝 Contributing

### Guidelines
1. Follow the established coding standards
2. Add comprehensive tests for new components
3. Update documentation for any changes
4. Ensure backward compatibility
5. Get approval from team leads for major changes

### Review Process
1. Create a pull request for shared component changes
2. Require approval from at least two team leads
3. Run all tests before merging
4. Update version numbers for releases

## 📞 Support

For questions about shared components or to propose new additions, contact the project leads or create an issue in the repository. 