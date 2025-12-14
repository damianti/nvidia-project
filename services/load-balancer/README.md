# Load Balancer

Intelligent load balancing service that routes HTTP requests to healthy container instances using Service Discovery.

## Overview

The Load Balancer distributes incoming requests across multiple healthy container instances, providing:
- Round Robin request distribution
- Circuit Breaker pattern for resilience
- Fallback cache for service discovery failures
- Integration with Service Discovery for real-time health monitoring

## Features

- **Round Robin Selection**: Distributes requests evenly across healthy containers
- **Circuit Breaker**: Opens after 3 consecutive failures, retries after 15s
- **Fallback Cache**: Maintains last successful routing for 10 seconds when Service Discovery is unavailable
- **Service Discovery Integration**: Uses async client to query healthy services
- **Health Monitoring**: Automatic detection of unhealthy containers

## Endpoints

- `POST /route` - Route HTTP request to healthy container instance
- `GET /health` - Health check endpoint

## How It Works

1. Receives HTTP request with `website_url` in body or Host header
2. Queries Service Discovery for healthy containers matching the URL
3. Selects a container using Round Robin algorithm
4. Checks Circuit Breaker state (CLOSED, OPEN, HALF_OPEN)
5. Routes request to selected container
6. Falls back to cache if Service Discovery is unavailable

## Configuration

- Port: `3004`
- Circuit Breaker failure threshold: `3`
- Circuit Breaker reset timeout: `15 seconds`
- Fallback cache TTL: `10 seconds`

## Dependencies

- Service Discovery: For healthy container information
- Consul: Service registry and health monitoring
