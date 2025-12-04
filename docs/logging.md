# Logging Standards and Guidelines

This document describes the logging standards used across all services in the NVIDIA Cloud Platform.

## Overview

All services use structured logging with:
- **Console output**: Human-readable format for development
- **File output**: JSON format for production and log aggregation
- **Correlation IDs**: Track requests across services
- **Structured data**: Contextual information in `extra` parameter

## Log Levels

### INFO
Use for normal operational events:
- Service startup/shutdown
- Successful operations (create, update, delete)
- Important state changes
- Health check responses

### WARNING
Use for potentially problematic situations:
- Retry attempts
- Degraded performance
- Missing optional data
- Deprecated feature usage

### ERROR
Use for error conditions that don't stop the service:
- Failed operations (with retry capability)
- External service failures
- Validation errors
- Non-critical exceptions

### DEBUG
Use for detailed diagnostic information:
- Request/response details
- Internal state transitions
- Performance metrics
- Detailed execution flow

## Log Format

### Structured Logging Pattern

Always use structured logging with the `extra` parameter:

```python
logger.info(
    "operation.event_name",
    extra={
        "key1": "value1",
        "key2": 123,
        "key3": {"nested": "data"}
    }
)
```

### Event Naming Convention

Use dot-separated hierarchical names: `service.operation.action`

Examples:
- `auth.login.success`
- `auth.login.failed`
- `container.create.started`
- `container.create.completed`
- `kafka.message.received`
- `service_discovery.registration.success`

### Console Format

Console logs use human-readable format:
```
2024-12-04T16:30:45.123456 [INFO] auth-service: auth.login.success (correlation_id=abc-123)
```

### JSON Format (File)

File logs use JSON format for easy parsing:
```json
{
  "timestamp": "2024-12-04T16:30:45.123456",
  "level": "INFO",
  "logger": "auth-service",
  "message": "auth.login.success",
  "correlation_id": "abc-123",
  "user_id": 1,
  "email": "user@example.com"
}
```

## Correlation IDs

Correlation IDs track requests across services. They are:
- Generated at API Gateway entry point
- Passed via HTTP headers (`X-Correlation-ID`)
- Stored in context variables
- Included in all log entries automatically

## Best Practices

### 1. Include Relevant Context

Always include relevant identifiers and context:

```python
# Good
logger.info(
    "container.create.success",
    extra={
        "container_id": container.id,
        "image_id": image_id,
        "user_id": user_id,
        "container_name": container.name
    }
)

# Bad
logger.info(f"Container {container.id} created")
```

### 2. Use Appropriate Log Levels

```python
# INFO: Normal operation
logger.info("container.start.success", extra={"container_id": container_id})

# WARNING: Recoverable issue
logger.warning("container.health_check.degraded", extra={"container_id": container_id, "response_time_ms": 5000})

# ERROR: Failed operation
logger.error(
    "container.start.failed",
    extra={
        "container_id": container_id,
        "error": str(e),
        "error_type": type(e).__name__
    },
    exc_info=True  # Include stack trace for errors
)
```

### 3. Don't Log Sensitive Information

Never log:
- Passwords or password hashes
- API keys or tokens
- Personal identifiable information (PII) unless necessary
- Full request/response bodies with sensitive data

```python
# Good
logger.info("auth.login.attempt", extra={"email": email, "user_id": user_id})

# Bad
logger.info("auth.login.attempt", extra={"email": email, "password": password})
```

### 4. Use exc_info for Errors

Always include `exc_info=True` for exceptions:

```python
try:
    # operation
except Exception as e:
    logger.error(
        "operation.failed",
        extra={
            "error": str(e),
            "error_type": type(e).__name__
        },
        exc_info=True  # Includes full stack trace
    )
```

### 5. Avoid Verbose Logging in Loops

For high-frequency operations, log at appropriate intervals:

```python
# Good: Log summary
processed_count = 0
for item in items:
    process(item)
    processed_count += 1
logger.info("batch.process.completed", extra={"processed_count": processed_count})

# Bad: Log every iteration
for item in items:
    logger.info("item.processed", extra={"item_id": item.id})  # Too verbose
```

## Service-Specific Guidelines

### API Gateway
- Log all incoming requests (method, path, correlation_id)
- Log routing decisions
- Log authentication results
- Don't log request/response bodies

### Orchestrator
- Log container lifecycle events
- Log Docker operations
- Log Kafka message publishing
- Include container_id, image_id, user_id

### Load Balancer
- Log routing decisions
- Log circuit breaker state changes
- Log fallback cache hits/misses
- Include website_url, target_service

### Service Discovery
- Log service registration/deregistration
- Log health check results
- Log cache updates
- Include service_type, service_id

### Billing
- Log usage record creation/updates
- Log cost calculations
- Include user_id, container_id, cost

### Auth Service
- Log login/signup attempts (without passwords)
- Log token generation
- Include user_id, email (not password)

## Configuration

Log level can be configured via environment variable:

```bash
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

Default: `INFO`

## Log Files

Logs are written to:
- **Console**: Standard output (human-readable)
- **File**: `logs/app.log` (JSON format, rotated daily, kept for 7 days)

## Examples

### Successful Operation
```python
logger.info(
    "image.create.success",
    extra={
        "image_id": image.id,
        "name": image.name,
        "tag": image.tag,
        "user_id": user_id
    }
)
```

### Failed Operation
```python
try:
    result = operation()
except Exception as e:
    logger.error(
        "operation.failed",
        extra={
            "operation": "create_container",
            "error": str(e),
            "error_type": type(e).__name__,
            "container_id": container_id
        },
        exc_info=True
    )
    raise
```

### Warning
```python
logger.warning(
    "service.health_check.slow",
    extra={
        "service_id": service_id,
        "response_time_ms": response_time,
        "threshold_ms": 1000
    }
)
```

## Monitoring and Alerting

Logs can be aggregated and monitored using:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki + Grafana**
- **CloudWatch** (AWS)
- **Datadog**
- **Splunk**

The JSON format makes it easy to parse and query logs for:
- Error rates
- Performance metrics
- User activity
- System health

## Troubleshooting

### Finding Logs for a Specific Request

Use correlation_id to trace a request across services:

```bash
grep "correlation_id=abc-123" logs/app.log
```

### Finding Errors

```bash
grep '"level":"ERROR"' logs/app.log | jq
```

### Finding Slow Operations

```bash
grep "response_time_ms" logs/app.log | jq 'select(.response_time_ms > 1000)'
```

## Log File Storage and Access

### Docker Volumes Mapped

All Python services have persistent log storage configured via Docker volumes. Logs are written to `/app/logs` inside the container and mapped to the host filesystem.

**Volume Mappings:**

- `./logs/auth-service:/app/logs` - Auth service logs
- `./logs/orchestrator:/app/logs` - Orchestrator service logs
- `./logs/api-gateway:/app/logs` - API Gateway logs
- `./logs/load-balancer:/app/logs` - Load Balancer logs
- `./logs/service-discovery:/app/logs` - Service Discovery logs
- `./logs/billing:/app/logs` - Billing service logs
- `./logs/client-workload:/app/logs` - Client Workload logs

### Accessing Logs from Host

Logs are accessible from the host machine at the project root:

```bash
# View auth service logs
tail -f logs/auth-service/app.log

# View orchestrator logs
tail -f logs/orchestrator/app.log

# View all service logs
find logs/ -name "*.log" -exec tail -f {} \;

# Search across all logs
grep -r "error" logs/
```

### Log File Location

- **Inside container**: `/app/logs/app.log` (JSON format)
- **On host**: `./logs/<service-name>/app.log`

The log files are automatically rotated daily and kept for 7 days (configurable in each service's logging configuration).

## Real-time Logging in Terminal

### Using LOG_LEVEL Environment Variable

You can control the verbosity of logs in real-time by setting the `LOG_LEVEL` environment variable. This is particularly useful for debugging and development.

**Available Log Levels:**
- `DEBUG` - Most verbose, includes detailed diagnostic information
- `INFO` - Normal operational events (default)
- `WARNING` - Potentially problematic situations
- `ERROR` - Error conditions only

### Examples

**Run with DEBUG logging:**
```bash
LOG_LEVEL=DEBUG docker-compose up
```

**Run specific service with DEBUG logging:**
```bash
LOG_LEVEL=DEBUG docker-compose up auth-service orchestrator
```

**Set in .env file:**
```bash
# .env
LOG_LEVEL=DEBUG
```

### PYTHONUNBUFFERED=1

All Python services have `PYTHONUNBUFFERED=1` configured, which ensures that:
- Python output is not buffered
- Logs appear immediately in the terminal
- Real-time debugging is possible
- No log delays when troubleshooting

This is essential for seeing logs in real-time when using `docker-compose logs -f` or when running services interactively.

### Viewing Real-time Logs

```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f auth-service

# View logs with timestamps
docker-compose logs -f --timestamps

# View last 100 lines and follow
docker-compose logs -f --tail=100 orchestrator
```

### Combining LOG_LEVEL with Log Viewing

```bash
# Start services with DEBUG logging and follow logs
LOG_LEVEL=DEBUG docker-compose up -d
docker-compose logs -f

# Or in one command
LOG_LEVEL=DEBUG docker-compose up
```

