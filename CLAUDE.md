# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NVIDIA Cloud Platform — a production-ready microservices platform for deploying containerized applications with automatic load balancing, service discovery, and real-time billing. All services run via Docker Compose.

## Commands

### Running the Platform

```bash
cp .env.example .env
docker compose up -d --build        # Start all services
docker compose down                 # Stop all services
docker compose logs -f <service>    # Tail logs for a service
./scripts/check-services.sh        # Verify all services are healthy
```

**Default credentials**: `example@gmail.com` / `example123`

**Key URLs**: UI → http://localhost:3000 | API Gateway → http://localhost:8080 | Grafana → http://localhost:3001 | Consul → http://localhost:8500 | Kafka UI → http://localhost:8081

### Testing

```bash
# Single Python service (from service directory):
cd services/<service-name>
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
pytest tests/                               # All tests
pytest tests/unit/                          # Unit tests only
pytest tests/ --cov=app --cov-report=xml   # With coverage

# All services:
./scripts/run-all-tests.sh

# Frontend:
cd services/ui
npm ci && npm test
```

### Linting & Formatting (Python services)

```bash
cd services/<service-name>
ruff check app/          # Lint
black app/               # Format
black --check app/       # Check formatting (CI mode)
```

A pre-push git hook (`scripts/pre-push-checks.sh`) automatically runs ruff, black, and pytest for all Python services before push.

### Frontend (UI service)

```bash
cd services/ui
npm ci
npm run dev     # Dev server (port 3000)
npm run build   # Production build
npm test        # Jest tests
```

## Architecture

### Service Map

| Service | Port | Language | Purpose |
|---------|------|----------|---------|
| `ui` | 3000 | Next.js 15 / TypeScript | Web dashboard |
| `api-gateway` | 8080 | Python / FastAPI | Single entry point, proxies all requests |
| `auth-service` | 3005 | Python / FastAPI | JWT authentication, user management |
| `orchestrator` | 3003 | Python / FastAPI | Docker image builds, container lifecycle |
| `load-balancer` | 3004 | Python / FastAPI | Round-robin routing with circuit breaker |
| `service-discovery` | 3006 | Python / FastAPI | Consul watch integration, container registry |
| `billing` | 3007 | Python / FastAPI | Real-time cost calculation |
| `client-workload` | 3008 | Python / FastAPI | Synthetic traffic generator |

### Data Flow

1. **Container deployment**: UI → API Gateway → Orchestrator (builds image, starts container) → Kafka event → Service Discovery (registers with Consul) + Billing (starts tracking)
2. **Traffic routing**: Client → API Gateway → Load Balancer → queries Consul for healthy instances → forwards to container
3. **Service discovery**: Consul Watch API maintains an in-memory cache in the Load Balancer, indexed by `image_id` and `app_hostname`

### Key Design Patterns

**Event-Driven**: Orchestrator publishes container lifecycle events to Kafka; Service Discovery and Billing are consumers.

**Load Balancer**: Round-robin with circuit breaker (3 failures → open, 15s retry window, 10s fallback cache TTL).

**Three separate PostgreSQL instances**: Orchestrator DB, Auth DB, Billing DB — each service owns its own database.

**Docker-in-Docker**: Orchestrator uses Docker SDK with DinD for container isolation.

### Python Service Structure

All Python services share this layout:
```
app/
├── main.py              # Entry point with lifespan manager
├── core/
│   ├── lifespan.py     # Startup/shutdown logic (DB init, Kafka consumers, etc.)
│   ├── config.py       # Service metadata
│   ├── middleware.py   # CORS, logging, error handling
│   └── routers.py      # Router registration
├── routes/             # FastAPI route handlers
├── services/           # Business logic
├── database/           # SQLAlchemy models & session config
├── repositories/       # Data access layer
├── schemas/            # Pydantic models
├── utils/              # logger.py, config.py (env vars), auth helpers
└── middleware/         # Custom middleware
```

### Shared Utilities

`/shared/common/` contains standardized logging, config management, DB utilities, validators, and constants used across services.

### Frontend Architecture

Next.js 14 App Router with React 19. Authentication uses HttpOnly JWT cookies. API calls go through the Next.js server to the API Gateway at port 8080. Key pages: `/login`, `/signup`, `/dashboard`.

## Environment

Copy `.env.example` to `.env`. Key variables: PostgreSQL connection strings (3 instances), `SECRET_KEY` for JWT, service URLs, Kafka and Consul config.

## CI/CD

GitHub Actions (`.github/workflows/test-all-services.yml`) runs on push/PR to main: ruff lint, black format check, pytest with coverage for all Python services, plus Next.js build and Jest tests for the UI.

---

## Progress Log

> This section is maintained by Claude across conversations. Update it at the end of every session.
> Branch: `v2/scale-with-claude`

### Completed

- **Load Balancer → Redis migration**: Migrated in-memory LB state (round-robin counters, circuit breakers, fallback cache) to Redis so the LB can scale horizontally. (`services/load-balancer/`)
- **LB metrics pipeline**: Load Balancer exposes Prometheus-format metrics; API Gateway proxies them at `GET /api/lb/metrics`; Prometheus scrapes that endpoint; Grafana visualizes them.
- **LB metrics in UI dashboard**: Dashboard polls `GET /api/lb/metrics` and displays per-image request counts, latency, and circuit-breaker status in real time.
- **UI API proxy routes for LB** ✅ committed `0e5eebf`: Next.js server-side proxy routes:
  - `services/ui/app/api/lb/metrics/route.ts` → proxies to `/api/lb/metrics`
  - `services/ui/app/api/lb/metrics/mappings/route.ts` → proxies to `/api/lb/metrics/mappings`
- **Service Discovery — `image.deleted` handler**: Handler `_on_image_deleted()` in `kafka_consumer.py` deregisters all Consul services tagged `image-{id}`.
- **Tests: MetricsCollector** ✅ committed `6039914`: 18 unit tests in `services/load-balancer/tests/unit/test_metrics_collector.py` covering `record_request`, `update_mapping`, `get_metrics`, `get_active_mappings`, `reset`.
- **Tests: LB metrics endpoints** ✅ committed `6039914`: 4 integration tests added to `services/load-balancer/tests/integration/test_lb_routes.py` for `GET /metrics` and `GET /metrics/mappings`. Used `fakeredis.FakeServer` shared between sync/async clients to avoid event-loop conflicts.
- **Tests: service-discovery `image.deleted`** ✅ committed `bcff8c8`: 3 unit tests in `services/service-discovery/tests/unit/test_kafka_consumer.py` covering the `_on_image_deleted()` handler directly.
- **UI — upload form UX**: Improved upload form; renamed "hostname" field to "URL Slug" for clarity.
- **CI — pre-push hook**: Hook now tolerates pip build failures gracefully and shows better error output.
- **Billing polling**: UI dashboard polls billing data in real time.
- **Auth fixes**: Resolved authentication and metrics rendering issues in the UI.

- **Step 5 — Billing `image.deleted` handler** ✅ committed `f2b50cf`:
  - Created `ImageEventData` schema in service-discovery and billing (separate from `ContainerEventData`)
  - Fixed `process_message` in both services to route `image.*` events through the new schema
  - Orchestrator `delete_image()` now publishes `image.deleted` to Kafka after DB delete
  - Added `get_active_by_image_id()` to `usage_repository`
  - Added `process_image_deleted()` to `billing_service` — closes ACTIVE records with cost/duration
  - Added `_on_image_deleted` handler to billing kafka consumer
  - 3 unit tests for `process_image_deleted`; billing suite at 95% coverage (90 tests passing)

- **Step 6 — Active Routes panel in UI dashboard** ✅: Added "Active Routes" table to `services/ui/app/dashboard/page.tsx`. Polls `/api/lb/metrics/mappings` every 10s and renders `app_hostname → external_port` pairs. State, fetch callback, and refresh interval all wired up.

### In Progress / Pending

- **Step 7 — Feature: Horizontal scaling demo**: Configure docker-compose to run multiple LB replicas; API Gateway discovers LB via Consul instead of hardcoded URL.

### Next Suggested Step

Step 7: horizontal scaling demo — multiple LB replicas + Consul-based LB discovery in the API Gateway.
