# Billing Service

Automated billing and cost tracking service that calculates costs based on container usage time.

## Overview

The Billing service tracks container usage and calculates costs in real-time:
- Processes container lifecycle events from Kafka
- Calculates costs based on container runtime
- Provides billing summaries and detailed reports
- Tracks usage at per-container granularity

## Features

- **Real-time Calculation**: Estimates costs for active containers on-demand
- **Event-driven**: Processes container lifecycle events from Kafka
- **Per-container Tracking**: Tracks usage at individual container level
- **Billing Summaries**: Aggregated costs per image and user
- **Fixed Rate**: $0.01 per minute per container

## Endpoints

- `GET /images` - Get billing summaries for all user images
- `GET /images/{image_id}` - Get detailed billing for a specific image
- `GET /health` - Health check endpoint
- `GET /metrics` - Service metrics (messages processed, success/failure counts)

## How It Works

1. **Kafka Consumer**: Listens to `container-lifecycle` topic
2. **Event Processing**: Processes `container.created`, `container.started`, `container.stopped`, `container.deleted` events
3. **Usage Tracking**: Records container start/stop times in database
4. **Cost Calculation**: Calculates costs based on runtime duration
5. **API Queries**: Provides billing summaries and detailed reports

## Configuration

- Port: `3007`
- Database: PostgreSQL for usage records
- Kafka: Consumes from `container-lifecycle` topic
- Rate: $0.01 per minute per container

## Dependencies

- PostgreSQL: For usage records storage
- Kafka: For container lifecycle events
- Orchestrator: Source of container lifecycle events
