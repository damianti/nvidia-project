# Auth Service

Authentication and user management service with JWT token generation and user registration.

## Overview

The Auth service handles:
- User authentication with JWT tokens
- User registration and account creation
- Password hashing and security
- Default user seeding on startup

## Features

- **JWT Authentication**: Generates secure JWT tokens
- **HttpOnly Cookies**: Stores tokens in secure HttpOnly cookies
- **Password Security**: Bcrypt password hashing
- **Default User**: Auto-creates default user if database is empty
- **User Management**: CRUD operations for users

## Endpoints

- `POST /auth/login` - Authenticate user and get JWT token
- `POST /auth/signup` - Register a new user
- `POST /auth/logout` - Logout user and discard token
- `GET /auth/me` - Get current user information
- `GET /health` - Health check endpoint

## Default Credentials

On first startup, if no users exist, a default user is created:
- Email: `example@gmail.com`
- Password: `example123`

## Configuration

- Port: `3001`
- Database: PostgreSQL
- JWT Secret: Configured via environment variables
- Token Expiration: 1 hour (configurable)

## Dependencies

- PostgreSQL: For user data storage
- API Gateway: Primary consumer for authentication
