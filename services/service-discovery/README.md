# Service Discovery

Service discovery and health monitoring service that maintains a real-time cache of healthy containers using Consul.

## Overview

The Service Discovery service provides:
- Real-time container health monitoring via Consul Watch API
- In-memory cache of healthy containers indexed by `image_id` and `app_hostname`
- Kafka event consumption for container lifecycle updates
- Fast lookup API for Load Balancer integration

## Features

- **Consul Integration**: Uses Consul Watch API for real-time updates
- **In-Memory Cache**: Fast lookup of healthy containers
- **Kafka Consumer**: Listens to container lifecycle events
- **Health Monitoring**: Tracks container health status via Consul
- **App Indexing**: Indexes containers by `app_hostname` for fast routing

## Endpoints

- `GET /services/healthy` - Get healthy services from cache (supports `app_hostname` filter)
- `GET /services/cache/status` - Get cache status and statistics
- `GET /health` - Health check endpoint
- `GET /metrics` - Service metrics (messages processed, success/failure counts)

## How It Works

1. **Consul Watcher**: Long-polling Watch API monitors Consul for service changes
2. **Kafka Consumer**: Consumes container lifecycle events for registration
3. **Cache Update**: Updates in-memory cache when containers are created/stopped
4. **Health Filtering**: Only includes healthy containers in cache
5. **Fast Lookup**: Provides sub-millisecond lookups for Load Balancer

## Configuration

- Port: `3006`
- Consul: Service registry and health monitoring
- Kafka: Consumes from `container-lifecycle` topic
- Cache: In-memory with automatic updates

## Dependencies

- Consul: Service registry and health checks
- Kafka: For container lifecycle events
- Load Balancer: Primary consumer of service information
