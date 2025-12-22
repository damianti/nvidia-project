# Comprehensive Testing Plan

## Overview

This document outlines a comprehensive testing strategy for the NVIDIA Cloud Platform project. The plan follows the **Testing Pyramid** approach, emphasizing unit tests at the base, integration tests in the middle, and end-to-end tests at the top.

## Testing Pyramid Strategy

```
        /\
       /E2E\          (Few, Critical User Flows)
      /------\
     /Integration\   (Service-to-Service Communication)
    /------------\
   /    Unit      \   (Many, Fast, Isolated)
  /----------------\
```

### Goals
- **Unit Tests**: 70% of total tests - Fast, isolated, mock external dependencies
- **Integration Tests**: 20% of total tests - Test service interactions
- **E2E Tests**: 10% of total tests - Complete user flows

### Coverage Target
- **Overall Code Coverage**: 80%+
- **Critical Paths**: 95%+
- **Business Logic**: 90%+

---

## 1. Unit Tests

### 1.1 Orchestrator Service

#### Image Service (`image_service.py`)
**Current Coverage**: Basic tests exist for `create_image_from_upload`, `get_image_by_id`, `delete_image`

**Missing Tests**:
- [ ] `create_image_from_upload`:
  - [ ] Build failure scenarios (Docker build errors)
  - [ ] Invalid file formats (non-zip, corrupted archives)
  - [ ] Missing Dockerfile in uploaded archive
  - [ ] Disk space exhaustion during extraction
  - [ ] Concurrent uploads with same `app_hostname`
  - [ ] Build logs collection and storage
  - [ ] Build status transitions (`building` → `ready` / `build_failed`)
  - [ ] Large file uploads (>100MB)
  - [ ] Invalid `app_hostname` formats
  - [ ] Container port validation (valid port ranges)
  - [ ] Resource limit validation (CPU, memory formats)
  - [ ] `prepare_context` edge cases (permission errors, path traversal attempts)

- [ ] `get_image_by_id`:
  - [ ] Unauthorized access (user_id mismatch)
  - [ ] Database connection failures
  - [ ] Concurrent access scenarios

- [ ] `delete_image`:
  - [ ] Image with stopped containers
  - [ ] Image with multiple containers in different states
  - [ ] Database transaction rollback on failure
  - [ ] Docker image cleanup failures

- [ ] `prepare_context`:
  - [ ] Archive extraction failures
  - [ ] Missing Dockerfile detection
  - [ ] Path traversal prevention
  - [ ] File permission handling
  - [ ] Disk quota exceeded

- [ ] `_collect_build_logs`:
  - [ ] Various Docker log chunk formats (bytes, strings, nested dicts)
  - [ ] Truncated logs
  - [ ] Unicode handling
  - [ ] Large log outputs

#### Container Service (`container_service.py`)
**Current Coverage**: Basic tests exist for `create_containers`, `start_container`, `stop_container`, `delete_container`

**Missing Tests**:
- [ ] `create_containers`:
  - [ ] Container name sanitization (special characters, length limits)
  - [ ] Port conflict handling
  - [ ] Docker daemon unavailable
  - [ ] Resource limit enforcement (CPU, memory)
  - [ ] Network configuration errors
  - [ ] Concurrent container creation
  - [ ] Kafka event publishing failures
  - [ ] Database transaction rollback on Docker failure
  - [ ] Container IP assignment conflicts
  - [ ] External port allocation conflicts

- [ ] `start_container`:
  - [ ] Container already running
  - [ ] Container not found in Docker
  - [ ] Container health check failures
  - [ ] Port binding failures
  - [ ] Network connectivity issues
  - [ ] Resource exhaustion (memory, CPU)

- [ ] `stop_container`:
  - [ ] Container already stopped
  - [ ] Force stop scenarios
  - [ ] Graceful shutdown timeout
  - [ ] Container not found in Docker

- [ ] `delete_container`:
  - [ ] Container still running (should fail)
  - [ ] Container not found in Docker
  - [ ] Volume cleanup
  - [ ] Network cleanup

#### Docker Service (`docker_service.py`)
**Missing Tests**:
- [ ] `build_image_from_context`:
  - [ ] Build timeout
  - [ ] Build context not found
  - [ ] Dockerfile syntax errors
  - [ ] Base image pull failures
  - [ ] Build cache invalidation
  - [ ] Multi-stage build support

- [ ] `run_container`:
  - [ ] Image not found
  - [ ] Port conflicts
  - [ ] Resource limit enforcement
  - [ ] Environment variable injection
  - [ ] Volume mounting
  - [ ] Network mode configuration

- [ ] `get_container_status`:
  - [ ] Container not found
  - [ ] Docker daemon errors
  - [ ] Status transition detection

#### Repository Layer
**Missing Tests**:
- [ ] `ImagesRepository`:
  - [ ] Database connection pooling
  - [ ] Query optimization
  - [ ] Transaction handling
  - [ ] Concurrent updates

- [ ] `ContainersRepository`:
  - [ ] Bulk operations
  - [ ] Filtering and pagination
  - [ ] Status updates race conditions

### 1.2 API Gateway Service

**Missing Tests**:
- [ ] Authentication middleware:
  - [ ] JWT token validation
  - [ ] Expired tokens
  - [ ] Invalid token signatures
  - [ ] Missing tokens
  - [ ] Token refresh logic
  - [ ] Cookie parsing and validation

- [ ] Multipart file upload proxying:
  - [ ] Large file handling (>100MB)
  - [ ] Corrupted multipart data
  - [ ] Missing boundary
  - [ ] Concurrent uploads
  - [ ] Memory limits
  - [ ] Timeout handling

- [ ] Request routing:
  - [ ] Path-based routing
  - [ ] Hostname-based routing
  - [ ] 404 handling for unknown routes
  - [ ] Method not allowed (405)

- [ ] Error handling:
  - [ ] Service unavailable (503)
  - [ ] Gateway timeout (504)
  - [ ] Invalid JSON responses from services
  - [ ] Non-JSON responses (HTML errors)

- [ ] Rate limiting:
  - [ ] Per-user rate limits
  - [ ] Per-endpoint rate limits
  - [ ] Rate limit headers

### 1.3 Load Balancer Service

**Current Coverage**: Circuit breaker and fallback cache tests exist

**Missing Tests**:
- [ ] Round Robin algorithm:
  - [ ] Even distribution across containers
  - [ ] Container removal from pool
  - [ ] Container addition to pool
  - [ ] Empty pool handling

- [ ] Health checks:
  - [ ] Unhealthy container detection
  - [ ] Health check timeout
  - [ ] Health check interval configuration
  - [ ] Container recovery detection

- [ ] Circuit breaker:
  - [ ] Open state transitions
  - [ ] Half-open state testing
  - [ ] Failure threshold configuration
  - [ ] Recovery timeout

- [ ] Fallback cache:
  - [ ] Cache expiration
  - [ ] Cache invalidation
  - [ ] Cache size limits
  - [ ] Cache hit/miss scenarios

- [ ] Request forwarding:
  - [ ] Request timeout handling
  - [ ] Connection errors
  - [ ] Response streaming
  - [ ] Large response handling

### 1.4 Service Discovery Service

**Current Coverage**: Basic Consul client tests exist

**Missing Tests**:
- [ ] Service registration:
  - [ ] Duplicate registration handling
  - [ ] Registration failure recovery
  - [ ] TTL expiration
  - [ ] Service metadata updates

- [ ] Service discovery:
  - [ ] Service not found scenarios
  - [ ] Multiple instances handling
  - [ ] Service filtering by tags
  - [ ] Consul connection failures

- [ ] Health check integration:
  - [ ] Health check registration
  - [ ] Health status updates
  - [ ] Unhealthy service removal

### 1.5 Auth Service

**Current Coverage**: Login, signup, authentication logic tests exist

**Missing Tests**:
- [ ] Password hashing:
  - [ ] Salt generation
  - [ ] Hash verification
  - [ ] Password strength validation

- [ ] JWT token generation:
  - [ ] Token expiration
  - [ ] Token refresh
  - [ ] Token revocation
  - [ ] Custom claims

- [ ] User management:
  - [ ] User creation validation
  - [ ] Email uniqueness
  - [ ] Username uniqueness
  - [ ] User deletion

- [ ] Security:
  - [ ] SQL injection prevention
  - [ ] XSS prevention
  - [ ] CSRF protection
  - [ ] Brute force protection

### 1.6 Billing Service

**Current Coverage**: Usage calculator functions (duration, cost calculation) tests exist

**Missing Tests**:
- [ ] Cost calculation:
  - [ ] Edge cases (zero usage, negative values)
  - [ ] Currency conversion
  - [ ] Discount application
  - [ ] Tax calculation

- [ ] Usage tracking:
  - [ ] Concurrent usage updates
  - [ ] Usage aggregation
  - [ ] Billing period boundaries

### 1.7 UI (Next.js/TypeScript)

**Current Coverage**: Billing service tests exist

**Missing Tests**:
- [ ] Component tests:
  - [ ] Image upload form
  - [ ] Container management UI
  - [ ] Build logs viewer
  - [ ] Error message display
  - [ ] Loading states
  - [ ] Form validation

- [ ] Service layer tests:
  - [ ] API client error handling
  - [ ] Request retries
  - [ ] Authentication state management
  - [ ] Local storage handling

- [ ] Integration tests:
  - [ ] User flows (login → upload → deploy)
  - [ ] Error recovery flows
  - [ ] State persistence

---

## 2. Integration Tests

### 2.1 Service-to-Service Communication

#### Orchestrator ↔ Service Discovery
- [ ] Container registration on creation
- [ ] Container deregistration on deletion
- [ ] Health check updates
- [ ] Service discovery failure handling

#### Orchestrator ↔ Kafka
- [ ] Event publishing on container lifecycle
- [ ] Event consumption by Load Balancer
- [ ] Kafka connection failures
- [ ] Message serialization/deserialization

#### API Gateway ↔ Auth Service
- [ ] Token validation flow
- [ ] User authentication flow
- [ ] Auth service unavailable handling

#### API Gateway ↔ Orchestrator
- [ ] Multipart file upload forwarding
- [ ] Request authentication header injection
- [ ] Error response handling

#### Load Balancer ↔ Service Discovery
- [ ] Service list retrieval
- [ ] Service updates (add/remove instances)
- [ ] Service Discovery unavailable fallback

#### Load Balancer ↔ User Containers
- [ ] Request forwarding
- [ ] Health check integration
- [ ] Response aggregation

### 2.2 Database Integration

#### Orchestrator Database
- [ ] Image CRUD operations
- [ ] Container CRUD operations
- [ ] Transaction rollback scenarios
- [ ] Concurrent database access
- [ ] Database connection pooling

#### Auth Service Database
- [ ] User CRUD operations
- [ ] Session management
- [ ] Password reset flow

### 2.3 Docker Integration

#### Docker-in-Docker (DinD)
- [ ] Image build from context
- [ ] Container lifecycle (create, start, stop, delete)
- [ ] Network isolation
- [ ] Volume management
- [ ] Resource limits enforcement

---

## 3. End-to-End (E2E) Tests

### 3.1 Complete User Flows

#### Happy Path: Upload → Build → Deploy → Access
1. [ ] User logs in via UI
2. [ ] User uploads Dockerfile + source code (zip)
3. [ ] System builds Docker image
4. [ ] Build logs are displayed
5. [ ] User creates container(s)
6. [ ] Container(s) start successfully
7. [ ] Service Discovery registers containers
8. [ ] Load Balancer routes requests to containers
9. [ ] User accesses application via `app_hostname`
10. [ ] Application responds correctly

#### Container Lifecycle
1. [ ] Create multiple containers for same image
2. [ ] Stop one container
3. [ ] Verify Load Balancer removes stopped container
4. [ ] Restart stopped container
5. [ ] Verify Load Balancer adds container back
6. [ ] Delete container
7. [ ] Verify cleanup (Docker, Service Discovery, Database)

#### Build Failure Flow
1. [ ] Upload invalid Dockerfile
2. [ ] Build fails
3. [ ] Build logs show error
4. [ ] Build status is `build_failed`
5. [ ] User can retry build with fixed Dockerfile

#### Image Management
1. [ ] Create image with duplicate `app_hostname` (should fail)
2. [ ] Delete image with running containers (should fail)
3. [ ] Stop all containers
4. [ ] Delete image successfully
5. [ ] Verify Docker image cleanup

#### Load Balancing
1. [ ] Deploy 3 containers for same image
2. [ ] Send 30 requests
3. [ ] Verify requests are distributed evenly (~10 per container)
4. [ ] Stop one container
5. [ ] Send 20 more requests
6. [ ] Verify requests go to remaining 2 containers (~10 each)

#### Authentication Flow
1. [ ] Unauthenticated request to protected endpoint (should fail)
2. [ ] User logs in
3. [ ] Authenticated request succeeds
4. [ ] Token expires
5. [ ] Request fails with 401
6. [ ] User refreshes token
7. [ ] Request succeeds again

### 3.2 Error Scenarios

#### Service Failures
- [ ] Service Discovery unavailable → Load Balancer uses fallback cache
- [ ] Orchestrator database connection lost → Graceful error handling
- [ ] Docker daemon unavailable → Build fails gracefully
- [ ] Kafka unavailable → Events are queued or logged

#### Edge Cases
- [ ] Concurrent uploads with same `app_hostname`
- [ ] Rapid container start/stop cycles
- [ ] Container crashes → Health check detects → Removed from pool
- [ ] Network partition → Service Discovery updates delayed

### 3.3 Performance Scenarios

- [ ] Upload and build 10 images concurrently
- [ ] Deploy 50 containers simultaneously
- [ ] Handle 1000 requests/second through Load Balancer
- [ ] Database connection pool exhaustion handling

---

## 4. Performance & Load Tests

### 4.1 Load Tests

#### API Gateway
- [ ] 1000 concurrent requests
- [ ] Request latency under load
- [ ] Memory usage under load
- [ ] Connection pool limits

#### Load Balancer
- [ ] 5000 requests/second routing
- [ ] Health check overhead
- [ ] Circuit breaker performance impact
- [ ] Fallback cache hit rate

#### Orchestrator
- [ ] Concurrent image builds (5 simultaneous)
- [ ] Container creation throughput
- [ ] Database query performance
- [ ] Docker API call latency

### 4.2 Stress Tests

- [ ] Maximum containers per image (test `max_instances` limit)
- [ ] Maximum images per user
- [ ] Database connection limits
- [ ] Docker daemon resource limits

### 4.3 Endurance Tests

- [ ] System running for 24 hours
- [ ] Memory leaks detection
- [ ] Connection pool exhaustion
- [ ] Disk space monitoring (build contexts)

---

## 5. Security Tests

### 5.1 Authentication & Authorization

- [ ] JWT token tampering detection
- [ ] Token expiration enforcement
- [ ] User isolation (user A cannot access user B's resources)
- [ ] Role-based access control (if implemented)

### 5.2 Input Validation

- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Path traversal prevention (`../` in file paths)
- [ ] Command injection prevention (Dockerfile, container names)
- [ ] Container name sanitization

### 5.3 Network Security

- [ ] Container network isolation
- [ ] Port scanning prevention
- [ ] DDoS protection (rate limiting)

### 5.4 Data Security

- [ ] Sensitive data in logs (passwords, tokens)
- [ ] Build context cleanup after build
- [ ] Database encryption at rest
- [ ] Secure file upload handling

---

## 6. Test Infrastructure

### 6.1 Test Environment Setup

- [ ] Docker Compose test environment
- [ ] Test database setup/teardown
- [ ] Mock external services (if needed)
- [ ] Test data fixtures

### 6.2 Test Data Management

- [ ] Test user accounts
- [ ] Test Docker images
- [ ] Test containers
- [ ] Cleanup procedures

### 6.3 CI/CD Integration

- [ ] Automated test execution on PR
- [ ] Test result reporting
- [ ] Coverage reporting
- [ ] Test failure notifications

---

## 7. Implementation Plan

### Phase 1: Unit Tests (Weeks 1-2)
1. Complete Orchestrator unit tests (Image, Container, Docker services)
2. Complete API Gateway unit tests
3. Complete Load Balancer unit tests
4. Complete Auth Service unit tests
5. Complete UI component tests

### Phase 2: Integration Tests (Week 3)
1. Service-to-service communication tests
2. Database integration tests
3. Docker integration tests

### Phase 3: E2E Tests (Week 4)
1. Complete user flow tests
2. Error scenario tests
3. Performance baseline tests

### Phase 4: Performance & Security (Week 5)
1. Load tests
2. Stress tests
3. Security tests

### Phase 5: CI/CD Integration (Week 6)
1. Automated test execution
2. Coverage reporting
3. Test documentation

---

## 8. Test Tools & Frameworks

### Backend (Python)
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **httpx**: HTTP client for integration tests
- **docker**: Docker API client for Docker tests

### Frontend (TypeScript/JavaScript)
- **Jest**: Test framework
- **@testing-library/react**: React component testing
- **@testing-library/jest-dom**: DOM matchers
- **MSW (Mock Service Worker)**: API mocking

### E2E
- **Playwright** or **Cypress**: Browser automation
- **Python requests/httpx**: API E2E tests

### Performance
- **locust**: Load testing
- **k6**: Performance testing
- **pytest-benchmark**: Benchmarking

---

## 9. Success Criteria

### Coverage Goals
- [ ] Overall code coverage ≥ 80%
- [ ] Critical paths coverage ≥ 95%
- [ ] Business logic coverage ≥ 90%

### Test Execution
- [ ] All unit tests run in < 30 seconds
- [ ] All integration tests run in < 5 minutes
- [ ] All E2E tests run in < 15 minutes

### Quality Metrics
- [ ] Zero critical bugs in production
- [ ] < 5% test flakiness rate
- [ ] All tests pass consistently in CI

---

## 10. Maintenance

### Regular Updates
- [ ] Update tests when adding new features
- [ ] Refactor tests when refactoring code
- [ ] Remove obsolete tests
- [ ] Update test data as needed

### Test Review
- [ ] Review test coverage quarterly
- [ ] Identify and fix flaky tests
- [ ] Optimize slow tests
- [ ] Document test patterns and best practices

---

## Appendix: Test Examples

### Example Unit Test (Orchestrator)
```python
def test_create_image_from_upload_build_failure():
    """Test image creation when Docker build fails."""
    mock_repo.get_by_app_hostname.return_value = None
    mock_prepare.return_value = ("/tmp/root", "/tmp/root/context")
    mock_build.side_effect = DockerBuildError("Build failed: syntax error")
    
    with pytest.raises(HTTPException) as exc_info:
        create_image_from_upload(db=db, data=data, file=file)
    
    assert exc_info.value.status_code == 500
    assert "build" in str(exc_info.value.detail).lower()
    # Verify build logs were collected
    # Verify image status is 'build_failed'
```

### Example Integration Test
```python
async def test_container_creation_registers_with_service_discovery():
    """Test that creating a container registers it with Service Discovery."""
    # Create container via Orchestrator API
    response = await client.post("/containers", json=container_data)
    assert response.status_code == 201
    
    # Verify container is registered in Service Discovery
    services = consul_client.get_services("myapp")
    assert len(services) == 1
    assert services[0]["ID"] == f"container-{container_id}"
```

### Example E2E Test
```python
async def test_complete_deployment_flow():
    """Test complete flow: upload → build → deploy → access."""
    # 1. Login
    login_response = await client.post("/auth/login", json=credentials)
    assert login_response.status_code == 200
    
    # 2. Upload image
    with open("test-app.zip", "rb") as f:
        upload_response = await client.post("/images", files={"file": f}, data=image_data)
    assert upload_response.status_code == 201
    image_id = upload_response.json()["id"]
    
    # 3. Wait for build
    await wait_for_build_completion(image_id)
    
    # 4. Create container
    container_response = await client.post(f"/images/{image_id}/containers", json={"count": 1})
    assert container_response.status_code == 201
    
    # 5. Access application
    app_response = await client.get(f"http://{app_hostname}/")
    assert app_response.status_code == 200
```

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Maintainer**: Development Team
