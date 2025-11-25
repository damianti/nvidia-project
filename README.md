# NVIDIA Cloud Platform (Tel-Hai Summer 2025)

_Last updated: **25 Nov 2025**_

## 🚀 Overview

This repository hosts a production-style cloud platform where users upload container images, spawn containers, and route traffic through an API Gateway + Load Balancer stack. The system now reflects the real implementation: Service Discovery owns the website mapping and health state, the Load Balancer consumes that data via HTTP and relies on a Circuit Breaker + fallback cache, and the Orchestrator manages container lifecycles via Docker-in-Docker.

## 🧩 Services & Status

| Service | Description | Status |
| --- | --- | --- |
| `ui` | Next.js dashboard for images, containers, and auth flows | ✅ |
| `api-gateway` | Public entrypoint, forwards requests to the Load Balancer | ✅ |
| `auth-service` | FastAPI service with automatic default user seeding | ✅ |
| `orchestrator` | Builds images, creates/stops containers, emits Kafka events | ✅ |
| `service-discovery` | Consul watcher + cache, exposes `/services/healthy` | ✅ |
| `load-balancer` | FastAPI service that routes by `website_url` using Service Discovery | ✅ |
| `billing-service` | Cost calculation & reporting | 🚧 In implementation |
| `client-workload` | Synthetic traffic generator | 🚧 In implementation |

Supporting infrastructure: PostgreSQL, Kafka, Zookeeper, Consul, Docker-in-Docker.

## 🏗️ Architecture Highlights

```
UI → API Gateway → Load Balancer → Service Discovery → Consul → Containers
                                ↘︎ Kafka events (from Orchestrator)
```

- **Service Discovery as source of truth**: Consul Watch API feeds an in-memory cache (`ServiceCache`) that indexes healthy containers by `image_id` and `website_url`.
- **Load Balancer integration**: Uses an async `ServiceDiscoveryClient`, Round Robin selector, and a new Circuit Breaker with fallback cache to keep routing even if Service Discovery is temporarily down.
- **Event-driven orchestration**: Orchestrator publishes container lifecycle events to Kafka; Service Discovery consumes them to maintain metadata (e.g., website mapping).
- **Authentication**: `auth-service` seeds a default user (`example/example123`) on startup if the database is empty.

## ✨ Key Features

- URL-based routing with normalization (protocol stripping, lowercase, trailing slash removal).
- Auto-healing registration: Service Discovery registers containers with Consul, including host TCP health checks through `docker-dind`.
- Load Balancer resilience:
  - Circuit Breaker opens after 3 consecutive Service Discovery failures.
  - Half-open retry after 15s, auto-close on success.
  - Fallback cache keeps the last successful response per `website_url` for 10s.
- Structured logging with correlation IDs across services.

## 🧪 Manual Validation Recipes

1. **Standard routing**
   ```bash
   docker exec nvidia-load-balancer curl -s -X POST http://localhost:3004/route \
     -H "Content-Type: application/json" \
     -d '{"website_url":"https://youtube.com"}'
   ```

2. **Circuit Breaker & fallback cache**
   ```bash
   # Warm the cache
   docker exec nvidia-load-balancer curl -s -X POST http://localhost:3004/route \
     -H "Content-Type: application/json" -d '{"website_url":"https://youtube.com"}'

   # Stop Service Discovery and send multiple requests
   docker-compose stop service-discovery
   for i in {1..4}; do
     docker exec nvidia-load-balancer curl -s -X POST http://localhost:3004/route \
       -H "Content-Type: application/json" -d '{"website_url":"https://youtube.com"}'
   done

   # Restart Service Discovery to observe HALF_OPEN → CLOSED transition
   docker-compose start service-discovery
   ```

3. **Service Discovery cache inspection**
   ```bash
   docker exec nvidia-service-discovery curl -s http://localhost:3006/services/cache/status | jq
   docker exec nvidia-service-discovery curl -s \
     "http://localhost:3006/services/healthy?website_url=https://youtube.com" | jq
   ```

## 🛠️ Development

### Prerequisites
- Docker 24+
- Docker Compose V2
- Python 3.11 (for local service runs)

### Quick start
```bash
git clone <repo>
cd nvidia-project

cp .env.example .env
docker compose up -d --build

docker compose ps            # verify services
docker compose logs -f load-balancer
```

### Default credentials
- UI/Auth default user is auto-created if the `users` table is empty:
  - Email: `example@gmail.com`
  - Password: `example123`

### Useful endpoints
| Service | URL |
| --- | --- |
| UI | http://localhost:3000 |
| API Gateway | http://localhost:8080 |
| Load Balancer | http://localhost:3004 |
| Service Discovery | http://localhost:3006 |
| Orchestrator | http://localhost:3003 |

## 🚧 Work in Progress
- **Billing Service**: ingest orchestrator usage events, persist cost snapshots, expose API/UI.
- **Client Workload Generator**: configurable traffic generator for stress/regression testing.
- **Metrics & Monitoring**: Prometheus exporters + Grafana dashboards (design finalized, implementation queued).

## 🧱 Testing Roadmap
- Unit tests for `CircuitBreaker`, `FallbackCache`, and `_pick_service`.
- Integration tests covering Service Discovery cache updates + Load Balancer routing.
- End-to-end flows from UI to containers (auth → image → container → route).

## 🤝 Contribution Guidelines
- Python services follow `ruff` + `black` formatting.
- Prefer async FastAPI patterns (lifespan managers for background tasks).
- When editing documentation/comments, keep everything in **English**.
- Use short git commit messages (<72 chars) and favor single-purpose commits.

---
For any questions about the architecture or the current implementation status, reach out via the project Slack channel. Let's keep building! 💪