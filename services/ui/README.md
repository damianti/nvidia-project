# UI Service

Next.js web dashboard for managing images, containers, authentication, and billing.

## Overview

The UI service provides a modern web interface for:
- User authentication (login/signup)
- Image management (upload, view, delete)
- Container management (create, start, stop, delete)
- Billing visualization (costs and usage)
- Real-time updates and status monitoring

## Features

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Modern styling
- **Authentication**: JWT-based with HttpOnly cookies
- **API Integration**: Communicates with API Gateway

## Pages

- `/login` - User authentication
- `/signup` - User registration
- `/dashboard` - Main dashboard
- `/images` - Image management
- `/containers` - Container management
- `/billing` - Billing and cost tracking

## Development

```bash
npm install
npm run dev
```

## Configuration

- Port: `3000`
- API Gateway: `http://localhost:8080`
- Environment: Development and production builds

## Dependencies

- API Gateway: For all backend API calls
- Next.js: React framework
- TypeScript: Type safety
