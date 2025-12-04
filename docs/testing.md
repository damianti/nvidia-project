# Testing Guide

This document describes how to run tests for all services in the NVIDIA Cloud Platform project.

## Overview

The project includes tests for:
- **Backend Services** (Python/FastAPI): Unit tests and integration tests using `pytest`
- **Frontend** (Next.js/TypeScript): Component and service tests using `Jest`

## Running All Tests

To run all tests across all services:

```bash
./scripts/run-all-tests.sh
```

This script will:
1. Run tests for each Python service
2. Run tests for the Next.js UI
3. Display a summary of passed/failed tests

## Running Tests for Individual Services

### Python Services

Each Python service has its own test suite. To run tests for a specific service:

```bash
cd services/<service-name>
pytest tests/ -v
```

For example:
```bash
# Test Auth Service
cd services/auth-service
pytest tests/ -v

# Test Billing Service
cd services/billing
pytest tests/ -v

# Test Orchestrator
cd services/orchestrator
pytest tests/ -v
```

### Frontend (UI)

To run tests for the Next.js UI:

```bash
cd services/ui
npm test
```

For watch mode:
```bash
npm run test:watch
```

For coverage:
```bash
npm run test:coverage
```

## Test Structure

### Backend Tests

Each Python service follows this structure:

```
services/<service-name>/
  tests/
    __init__.py
    test_*.py          # Unit tests
    conftest.py       # Pytest fixtures (if needed)
  pytest.ini          # Pytest configuration
```

### Frontend Tests

The UI tests are located in:

```
services/ui/
  app/
    __tests__/
      *.test.ts       # Test files
  jest.config.js      # Jest configuration
  jest.setup.js       # Jest setup file
```

## Test Coverage

### Current Test Coverage

- **Billing Service**: Usage calculator functions (duration, cost calculation)
- **Auth Service**: Login, signup, authentication logic
- **Orchestrator**: Image service (create, get, delete)
- **Load Balancer**: Circuit breaker, fallback cache (existing tests)
- **Service Discovery**: Basic Consul client tests
- **API Gateway**: Gateway service validation tests
- **Client Workload**: Basic workload generator tests
- **UI**: Billing service tests

### Adding New Tests

When adding new functionality:

1. **Backend**: Create test files in `services/<service>/tests/test_*.py`
2. **Frontend**: Create test files in `services/ui/app/__tests__/*.test.ts`

Follow the existing test patterns and use mocks for external dependencies.

## Dependencies

### Python Testing Dependencies

All Python services include:
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support

### Frontend Testing Dependencies

The UI includes:
- `jest` - Testing framework
- `jest-environment-jsdom` - DOM environment for React
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - DOM matchers

## Continuous Integration

Tests can be integrated into CI/CD pipelines by running:

```bash
./scripts/run-all-tests.sh
```

The script exits with code 0 if all tests pass, or 1 if any tests fail.

## Troubleshooting

### Python Tests

If tests fail due to missing dependencies:
```bash
cd services/<service-name>
pip install -r requirements.txt
```

### Frontend Tests

If Jest tests fail:
```bash
cd services/ui
npm install
```

### Import Errors

Make sure you're running tests from the service directory, as `pytest.ini` configures the Python path relative to the service root.

## Best Practices

1. **Use Mocks**: Mock external dependencies (Docker, Kafka, databases) in unit tests
2. **Test Critical Paths**: Focus on business logic and critical endpoints
3. **Keep Tests Fast**: Unit tests should run quickly; use mocks to avoid slow operations
4. **Clear Test Names**: Use descriptive test function names that explain what is being tested
5. **Isolate Tests**: Each test should be independent and not rely on other tests

## Future Improvements

- [ ] Add integration tests that use Docker Compose
- [ ] Increase test coverage to 80%+
- [ ] Add E2E tests for complete user flows
- [ ] Add performance/load tests
- [ ] Add visual regression tests for UI

