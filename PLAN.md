# PLAN.md — nvidia-project

> Single source of truth for next steps. Updated at the end of every session.
> Progress history lives in `CLAUDE.md`.

---

## Immediate — Security improvements (code written, not committed)

These were implemented but interrupted before committing. Code is already on disk.
Run `ruff check` + `black --check` on `auth-service` and `orchestrator`, then commit.
Also create `SECURITY.md` at project root explaining each concept (same style as `CONCEPTS.md`).

| # | What | Files |
|---|------|-------|
| 1 | Rate limiting: 5/min on `/login`, 3/min on `/signup` | `auth-service/requirements.txt`, `main.py`, `api/auth.py` |
| 2 | File upload size limit: 100 MB | `orchestrator/app/services/build_context.py` |
| 3 | Password validation: min 8 chars, must have letter + digit | `auth-service/app/schemas/user.py` |
| 4 | Token revocation: Redis blocklist on logout | `auth-service/requirements.txt`, `utils/config.py`, new `services/token_blocklist.py`, `api/auth.py`, `utils/security.py`, `core/lifespan.py`, `docker-compose.yml` |
| 5 | Pagination on `GET /api/images` and `GET /api/containers` | `orchestrator/repositories/*`, `api/images.py`, `api/containers.py` |
| 6 | `SECURE_COOKIES` env var (false in dev, true in prod) | `auth-service/utils/config.py`, `api/auth.py` |
| 7 | Dockerfile content validation: blocks `--network=host`, `--privileged`, `ADD http://` | `orchestrator/app/services/build_context.py` |

---

## Step 7 — Horizontal scaling demo

Run 2 LB replicas in Docker Compose. API Gateway discovers LB instances via Consul
instead of a hardcoded `LOAD_BALANCER_URL`. Validates the Redis-backed distributed
state work (round-robin counter + circuit breaker shared across replicas).

Key files: `docker-compose.yml`, `services/api-gateway/app/clients/lb_client.py`

---

## Microservices Patterns (from Top 12 image)

### Already implemented

| Pattern | Where |
|---------|-------|
| API Gateway | `services/api-gateway/` |
| Service Discovery | `services/service-discovery/` + Consul |
| Circuit Breaker | `services/load-balancer/app/services/circuit_breaker.py` |
| Database per Service | 3 separate PostgreSQL instances in `docker-compose.yml` |
| Retry | `services/orchestrator/app/services/docker_service.py` |
| API Composition | Partial — metrics forwarding exists, no true cross-service join |
| Strangler Fig | N/A — greenfield project |

### To implement (in order)

#### A — Bulkhead
Isolate concurrency per user so one heavy client can't starve others.
Add a per-`user_id` `asyncio.Semaphore` in the API Gateway (cap: 10 concurrent requests per user).
Requests beyond the cap get an immediate 429.
Files: new `services/api-gateway/app/services/bulkhead.py`, modify `gateway_service.py`.

#### B — API Composition (upgrade partial → done)
Single `GET /api/dashboard/summary` endpoint that fans out with `asyncio.gather` to:
Orchestrator (images/containers count) + Billing (running cost) + Metrics (request rate).
Returns one merged JSON. Client makes 1 call instead of 3.
Files: new `services/api-gateway/app/routes/composition_routes.py` + `composition_service.py`.

#### C — CQRS
Separate read model from write model in the Billing service.
- **Write model** (already exists): `usage_records` updated by Kafka events.
- **Read model** (new): `billing_summary` table — one row per `(user_id, image_id)` with
  pre-aggregated totals. Kafka consumer updates it on every container event.
  Dashboard queries `billing_summary` instead of `GROUP BY` on `usage_records`.

Files: `services/billing/app/database/models.py`, `repositories/`, `billing_service.py`, `kafka_consumer.py`.

#### D — Saga
Manage the container deployment transaction with compensating actions.
Today, if Billing fails after a container starts, the container runs but is never billed (orphaned).

Saga flow:
1. Orchestrator starts container → publishes `container.started`
2. Billing creates record → on failure, publishes `saga.billing.failed`
3. Orchestrator hears `saga.billing.failed` → stops + deletes the container (compensation)

Files: new `services/orchestrator/app/services/saga_coordinator.py`, new Kafka topic `saga-events`.

#### E — Event Sourcing
Append-only `event_store` table written by every Kafka consumer before processing:
`(id, topic, event_type, payload JSON, created_at)`.
Add `GET /api/events` to view the log and `POST /api/events/replay?from=<timestamp>` to replay.
Files: new `services/event-store/` service or extend billing service, `docker-compose.yml`.

#### F — Sidecar
Deploy Fluent Bit alongside every service to collect logs from the `./logs/<service>`
volumes already mounted. Adds structured metadata without touching business code.
Files: new `services/sidecar/fluent-bit.conf`, updates to `docker-compose.yml`.

---

## Feature Backlog

Lower priority, but worth implementing eventually:

### Load Balancer
- **Advanced algorithms**: Least Connections, Weighted Round Robin. Selectable via env var.
- **Auto-scaling**: Monitor request rate → create/delete containers automatically when above/below thresholds.

### Platform
- **WebSocket support**: Detect upgrade requests in API Gateway, proxy to containers.
- **GitHub webhook deployment**: Trigger image build automatically on push to a branch.
- **Multi-tenancy**: Isolate data/resources per user more strictly (separate DB schemas or row-level security).

### Infrastructure
- **CI/CD pipeline**: GitHub Actions — lint + test on every PR, block merge on failure.
- **Kubernetes migration**: Convert `docker-compose.yml` to K8s manifests. Long-term goal.

---

## Testing gaps (priority order)

### High priority
- Orchestrator: build failure scenarios, invalid Dockerfile handling, concurrent uploads with same `app_hostname`
- API Gateway: multipart upload proxying edge cases, JWT middleware (expired/invalid tokens)
- E2E: complete deploy flow (upload → build → run → route → access), container lifecycle with LB updates

### Medium priority
- Load Balancer: round-robin distribution verification, container add/remove from pool
- Billing: concurrent usage updates, billing period boundaries

### Low priority
- Performance: 1000 req/s through LB, 5 concurrent image builds
- Security: path traversal in archive extraction, container name injection

---

## Documentation rule

After each step, update:
- `CONCEPTS.md` — add the new pattern (what, why, how it's implemented here, key facts for a fullstack engineer).
- `SECURITY.md` — update if the step has security implications.
- `CLAUDE.md` progress log — move completed items, update In Progress.
