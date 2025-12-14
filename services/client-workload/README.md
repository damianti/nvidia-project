# Client Workload Generator

Synthetic traffic generator for stress testing and performance evaluation of the platform.

## Overview

The Client Workload service generates synthetic HTTP traffic to test the platform's load balancing, service discovery, and container routing capabilities.

## Features

- **Configurable Workloads**: Define request rate, duration, and target URLs
- **Multiple Concurrent Tests**: Run multiple workload tests simultaneously
- **Real-time Metrics**: Track request counts, success rates, and latency
- **Service Discovery Integration**: Automatically discovers available services
- **Test Management**: Start, stop, and monitor workload tests

## Endpoints

- `POST /workload/start` - Start a new workload test
- `POST /workload/stop/{test_id}` - Stop a running test
- `GET /workload/status/{test_id}` - Get test status and metrics
- `GET /workload/list` - List all test IDs
- `GET /workload/metrics/{test_id}` - Get detailed metrics for a test
- `GET /workload/available-services` - Get available website URLs from Service Discovery

## Usage

### Start a Workload Test

```json
POST /workload/start
{
  "website_url": "https://example.com",
  "requests_per_second": 10,
  "duration_seconds": 60
}
```

### Check Test Status

```bash
GET /workload/status/{test_id}
```

### Stop a Test

```bash
POST /workload/stop/{test_id}
```

## Configuration

- Port: `3008`
- Default request rate: Configurable per test
- Default duration: Configurable per test

## Dependencies

- Service Discovery: For discovering available services
- Load Balancer: Target for generated traffic
