# API Gateway

Single entry point for all API requests. Handles authentication, request routing, and proxying to backend services.

## Overview

The API Gateway serves as the public-facing entry point for the platform, providing:
- Authentication proxy to auth-service
- Request routing to containers via Load Balancer
- API proxying to Orchestrator service
- Request caching for improved performance

## Features

- **Authentication**: Proxies login, signup, logout, and user info requests to auth-service
- **Container Routing**: Routes HTTP requests to containers via path-based routing (`/apps/{app_hostname}/...`)
- **Image Upload**: Handles multipart/form-data uploads for Docker images with Dockerfiles
- **Orchestrator Proxy**: Proxies authenticated API requests for container and image management
- **Caching**: Maintains routing cache with automatic cleanup of expired entries
- **CORS**: Configured for frontend origin

## Endpoints

### Authentication (proxied to auth-service)
- `POST /auth/login` - Authenticate user and get JWT token
- `POST /auth/logout` - Logout user and invalidate session
- `POST /auth/signup` - Register a new user
- `GET /auth/me` - Get current authenticated user information

### Container Routing
- `GET /apps/{app_hostname}/{remaining_path:path}` - **Path-based routing**. Routes requests to user applications via Load Balancer

### Orchestrator API Proxy
- `POST /api/images` - **Upload Docker image** with multipart/form-data (Dockerfile + context). Requires authentication.
- `GET /api/{path:path}` - Proxy API requests to Orchestrator service
- `POST /api/{path:path}` - Proxy API requests to Orchestrator service (except `/api/images` which has dedicated endpoint)
- `DELETE /api/{path:path}` - Proxy API requests to Orchestrator service
- `PUT /api/{path:path}` - Proxy API requests to Orchestrator service
- `PATCH /api/{path:path}` - Proxy API requests to Orchestrator service

## Configuration

- Port: `8080`
- Frontend URL: Configured via `FRONTEND_URL` environment variable
- Cache cleanup interval: Configurable via `CACHE_CLEANUP_INTERVAL`

## Dependencies

- Auth Service: For user authentication
- Load Balancer: For container routing
- Orchestrator: For container and image management
