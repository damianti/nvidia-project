# Concepts Used in This Project

This document explains the key distributed systems and software engineering concepts implemented in this platform. Each section covers **what** the concept is, **why** it's needed, and **how this project implements it**.

---

## Table of Contents

1. [Event-Driven Architecture with Kafka](#1-event-driven-architecture-with-kafka)
2. [Service Discovery with Consul](#2-service-discovery-with-consul)
3. [Load Balancing: Round-Robin + Circuit Breaker](#3-load-balancing-round-robin--circuit-breaker)
4. [Distributed State with Redis](#4-distributed-state-with-redis)
5. [JWT Authentication](#5-jwt-authentication)
6. [Docker-in-Docker (DinD) Orchestration](#6-docker-in-docker-dind-orchestration)
7. [API Gateway Pattern](#7-api-gateway-pattern)
8. [Event-Sourced Billing](#8-event-sourced-billing)
9. [Server-Side Proxy in Next.js](#9-server-side-proxy-in-nextjs)
10. [Async I/O and Thread Bridging in Python](#10-async-io-and-thread-bridging-in-python)

---

## 1. Event-Driven Architecture with Kafka

### What it is

In a microservices system, services need to react to things that happen in other services. You could have them call each other directly (synchronous), but that creates tight coupling — if the billing service is down, the orchestrator can't even deploy a container.

**Event-driven architecture** decouples services by having producers publish events to a shared message broker. Consumers subscribe to those events and react independently. Neither side needs to know the other exists.

**Apache Kafka** is a distributed event streaming platform. It stores events as an ordered, immutable log in **topics** (similar to queues). Multiple consumers can read from the same topic independently, and messages are retained even after being read.

### Why this project uses it

When a container starts, three things need to happen:
1. Service Discovery must register it in Consul.
2. Billing must start tracking its usage.
3. Neither of those is the Orchestrator's concern.

If the Orchestrator called each service directly, it would be responsible for the downstream chain. If billing was slow, the deploy would be slow. With Kafka, the Orchestrator just publishes `container.started` and moves on. The other services react on their own.

### How it's implemented here

**Producer** (`services/orchestrator/app/services/kafka_producer.py`):
- Uses the `confluent-kafka` library with `enable.idempotence=True` — this means Kafka guarantees a message is written exactly once even if the producer retries.
- Batches messages (64KB batch size, 10ms linger) for efficiency before sending.
- Compression: LZ4, which is fast with good throughput.

**Consumers** (`services/service-discovery/` and `services/billing/`):
- Both subscribe to the `container-lifecycle` topic.
- Dispatch events via a handler dictionary:
  ```python
  self._event_handlers = {
      "container.started": self._on_container_started,
      "container.stopped": self._on_container_stopped,
      "image.deleted": self._on_image_deleted,
  }
  handler = self._event_handlers.get(event_type)
  if handler:
      await handler(data)
  ```
- `auto_offset_reset = "earliest"` — if a consumer restarts, it re-reads from where it left off, so no events are missed.

**Event schema** (Pydantic validation):
- `ContainerEventData` for container lifecycle events.
- `ImageEventData` for image-level events (e.g., `image.deleted`).

**Key insight**: The `image.deleted` event flows like this:
```
User deletes image (UI)
  → Orchestrator publishes image.deleted to Kafka
    → Service Discovery deregisters all Consul services tagged with that image
    → Billing closes all open billing records for containers of that image
```
Neither consumer had to be called directly. They just listened.

---

## 2. Service Discovery with Consul

### What it is

In a dynamic container environment, you can't hardcode IP addresses. Containers start and stop constantly, and each gets a different port or IP. **Service discovery** is the mechanism by which services find each other at runtime.

**Consul** is a service mesh tool from HashiCorp. It provides:
- A **service registry**: services register themselves with a name, address, port, and tags.
- **Health checking**: Consul periodically pings registered services; unhealthy ones are removed.
- A **KV store** and **HTTP API** for querying the registry.

### Why this project uses it

When a user's container starts, the Load Balancer needs to know where it is. The container's external port is dynamic (assigned by Docker). Consul acts as the "phone book" — the Orchestrator registers the container, and the Load Balancer looks it up by name.

### How it's implemented here

**Registration** (`services/service-discovery/app/services/consul_client.py`):

When a `container.started` Kafka event arrives, Service Discovery registers the container with Consul via `PUT /v1/agent/service/register`:
```json
{
  "Name": "webapp-service",
  "ID": "container-myapp-12345",
  "Address": "docker-dind",
  "Port": 32789,
  "Tags": ["image-42", "external-port-32789", "app-hostname-myapp"]
}
```

All containers share the service name `webapp-service`. They're differentiated by **tags**. This is intentional — the LB queries by tag, not by service name.

**Health checks** use TCP on `docker-dind:{external_port}` because Consul runs outside the container network and cannot reach container-internal IPs directly.

**Long-polling watcher** (`services/service-discovery/app/services/consul_watcher.py`):

Instead of polling Consul every second (expensive), the watcher uses Consul's **blocking query** feature:
```
GET /v1/health/service/webapp-service?passing=true&index=42&wait=60s
```
- `index=42` is the last known state version (the `X-Consul-Index` header from the previous response).
- Consul holds the connection open for up to 60 seconds. It only responds when something changes, or when the timeout expires.
- If nothing changed in 60s, the response returns with the same index — this is expected and handled gracefully.

This means the Load Balancer's service cache updates within milliseconds of a container registering, without constant polling overhead.

---

## 3. Load Balancing: Round-Robin + Circuit Breaker

### What it is

A **load balancer** distributes incoming requests across multiple instances of a service so no single instance gets overwhelmed.

**Round-robin** is the simplest strategy: give request 1 to instance A, request 2 to instance B, request 3 to instance C, then back to A. It's fair and requires no knowledge of instance load.

A **circuit breaker** is a resilience pattern (named after electrical circuit breakers). If a downstream service fails repeatedly, the circuit "opens" and stops sending requests to it — giving it time to recover instead of hammering a broken service. After a timeout, the circuit enters a "half-open" state and lets one request through to test recovery.

### Why this project uses it

Multiple containers of the same image can be running simultaneously. The LB distributes traffic across them. But the LB also depends on Service Discovery — if Service Discovery is slow or down, the LB shouldn't fail completely. The circuit breaker protects the LB from cascading failures.

### How it's implemented here

**Round-robin** (`services/load-balancer/app/services/service_selector.py`):
```python
index = await self._redis.incr(f"lb:rr:index:{image_id}")
selected = services[(index - 1) % len(services)]
```
Redis's `INCR` is an atomic operation — even with multiple LB instances running, there's no race condition. Each request gets a unique index.

**Circuit breaker** (`services/load-balancer/app/services/circuit_breaker.py`):

Three states:
- **CLOSED**: Normal. Requests pass through. Failures are counted.
- **OPEN**: Too many failures (`failure_count >= 3`). All requests are blocked immediately.
- **HALF-OPEN**: After 15 seconds in OPEN state, one test request is allowed through. Success → CLOSED. Failure → back to OPEN.

All state (failure count, current state, timestamp of last failure) is stored in Redis so all LB instances share the same breaker state.

**Fallback cache** (`services/load-balancer/app/services/fallback_cache.py`):

When the circuit is open or Service Discovery fails, the LB tries to use the last known good list of services, stored in Redis with a 10-second TTL:
```python
key = f"lb:fallback:{normalized_hostname}"
await redis.setex(key, ttl=10, value=json.dumps(services))
```

**Full request flow** in `lb_service.py`:
```
Incoming request for "myapp"
  → Try Service Discovery (protected by circuit breaker)
    ├── Success: update fallback cache, pick a service with round-robin
    └── Failure / OPEN circuit:
          → Try fallback cache
            ├── Cache hit: pick a service (potentially stale, but available)
            └── Cache miss: return 503 Service Unavailable
```

---

## 4. Distributed State with Redis

### What it is

**Redis** is an in-memory data store with optional persistence. Its operations are single-threaded and atomic, making it ideal for shared counters, distributed locks, and caches across multiple processes.

### Why this project uses it

The Load Balancer needs to scale horizontally (multiple instances). If the round-robin counter and circuit breaker state were stored in memory, each LB instance would have its own counter and they'd all route to instance A independently. Redis gives all LB instances a single shared state.

### How it's implemented here

| Key pattern | Data | TTL |
|---|---|---|
| `lb:rr:index:{image_id}` | Round-robin counter (integer) | None |
| `lb:cb:state:{name}` | Circuit breaker state | None |
| `lb:cb:failures:{name}` | Failure count | None |
| `lb:cb:last_failure:{name}` | Timestamp | None |
| `lb:fallback:{hostname}` | Last known services (JSON) | 10s |

**Atomic INCR**: Redis's `INCR` command increments a key and returns the new value as a single atomic operation. No two requests can get the same index, even under high concurrency.

**TTL-based expiry**: The fallback cache uses `SETEX` (set with expiry). When a container goes down, the stale entry expires automatically without needing explicit cleanup logic.

---

## 5. JWT Authentication

### What it is

**JSON Web Tokens (JWT)** are a compact, URL-safe way to represent claims between two parties. A token is a base64-encoded string with three parts: `header.payload.signature`.

The server creates a token by signing a payload (e.g., `{"sub": "user@example.com", "exp": 1712345678}`) with a secret key. The client stores this token and sends it with every request. The server validates the signature — no database lookup needed.

**HS256** is the signing algorithm: HMAC-SHA256. It uses the same secret key to sign and verify (symmetric).

### Why this project uses it

Stateless authentication. The Auth service creates a token on login. Every other service (API Gateway, Orchestrator, Billing) can verify that token independently using the shared `SECRET_KEY`, without calling the Auth service on every request.

### How it's implemented here

**Token creation** (`services/auth-service/app/utils/tokens.py`):
```python
payload = {
    "sub": username,
    "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Token decoding and validation**:
```python
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
username = payload.get("sub")
```
If the signature is invalid or the token is expired, `jwt.decode` raises an exception. The API Gateway catches these and returns 401.

**Password hashing**: Passwords are never stored in plaintext. They're hashed with **bcrypt**, a slow hash function deliberately designed to resist brute-force attacks. `bcrypt.verify(password, hashed)` compares safely without exposing the hash.

**Cookie delivery**: The token is set as an HTTP-only cookie — JavaScript cannot read it, protecting against XSS attacks.

---

## 6. Docker-in-Docker (DinD) Orchestration

### What it is

**Docker-in-Docker (DinD)** means running a Docker daemon inside a Docker container. The outer container has access to a full Docker environment, so it can build images and start containers as if it were on the host machine.

The alternative is mounting the host's Docker socket (`/var/run/docker.sock`) into the container — but that gives the container root-level access to the host, which is a major security risk.

### Why this project uses it

The Orchestrator service needs to build Docker images and run containers on behalf of users. Since the Orchestrator itself runs in Docker Compose, DinD gives it a sandboxed Docker environment without exposing the host socket.

### How it's implemented here

**`docker_service.py`** in the Orchestrator uses the Docker Python SDK pointed at the DinD daemon:

**Image building**:
```python
image, logs = docker_client.images.build(
    path=context_dir,
    dockerfile="Dockerfile",
    tag=image_ref,
    rm=True,
)
```
The build context (user's Dockerfile + source) is passed as a directory. `rm=True` removes intermediate containers after the build.

**Running containers**:
```python
container = docker_client.containers.run(
    image=ref,
    name=container_name,
    ports={"8080/tcp": None},  # None = allocate a random external port
    detach=True,
    network="nvidia-network",
)
```
`ports={"8080/tcp": None}` tells Docker to map the container's internal port 8080 to a randomly chosen external port. After the container starts, the Orchestrator reads the assigned port:
```python
external_port = container.attrs["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"]
```

**Retry logic**: Some Docker operations can fail transiently (e.g., port conflicts → 409 Conflict). The service retries up to 3 times with exponential backoff (1s, 2s, 4s).

After a successful operation, a Kafka event is published with the container's metadata (container_id, image_id, user_id, external_port, hostname).

---

## 7. API Gateway Pattern

### What it is

An **API Gateway** is a single entry point for all client requests. Instead of clients calling each microservice directly (which would mean clients need to know about every service's URL, port, and auth scheme), the gateway routes all requests and handles cross-cutting concerns like authentication, logging, and rate limiting.

### Why this project uses it

Without a gateway:
- The UI would need to call the Auth service, Orchestrator, Billing, and Load Balancer directly.
- Each service would need its own CORS config, auth middleware, and external port.
- Adding a new service would require UI changes.

With a gateway:
- The UI calls one place: `http://localhost:8080`.
- The gateway forwards requests to the right service.
- Auth is enforced in one place.

### How it's implemented here

The API Gateway (`services/api-gateway/`) routes:
- `/auth/*` → Auth service
- `/api/containers/*` → Orchestrator
- `/api/billing/*` → Billing service
- `/api/lb/*` → Load Balancer
- `/apps/{app_hostname}/{path}` → User's deployed containers (via LB)

**Request routing to user containers** (`gateway_service.py`):

The gateway maintains an in-memory **routing cache** per `(client_ip, app_hostname)`:
```python
cache_key = f"{client_ip}:{app_hostname}"
entry = self._cache.get(cache_key)
if entry and not entry.is_expired():
    # Use cached target
else:
    # Ask Load Balancer which container to use
    route = await lb_client.resolve(app_hostname)
    self._cache[cache_key] = CacheEntry(route, expires_in=10s)
```

This gives sticky sessions (same client → same container for 10 seconds) without requiring server-side session state.

**Proxying**: `httpx.AsyncClient` forwards the request body and headers to the target container. On 5xx responses, the cache entry is invalidated so the next request gets a fresh LB decision.

**Metrics**: The gateway records latency, status code, user_id, and app_hostname for every proxied request. These are exposed as Prometheus metrics.

---

## 8. Event-Sourced Billing

### What it is

**Event sourcing** is a pattern where the state of the system is derived from a sequence of events, not from the current value of a mutable field. Instead of storing "container X has been running for 47 minutes", you store the events `container.started at T1` and later `container.stopped at T2` and compute the duration from those.

In this project, billing is a simplified version: usage records have a status (`ACTIVE` or `COMPLETED`) that transitions based on events.

### Why this project uses it

Billing correctness requires knowing exactly when a container started and stopped. If the billing service stored only "total minutes used", any bug or restart could corrupt that counter. By storing immutable start/end timestamps and computing cost at query time, the system is auditable and self-correcting.

### How it's implemented here

**`UsageRecord`** schema (in the Billing DB):
```
id, user_id, image_id, container_id, status, start_time, end_time, duration_minutes, cost
```

**On `container.started`** (`billing_service.py`):
```python
record = UsageRecord(
    container_id=container_id,
    user_id=user_id,
    image_id=image_id,
    status="ACTIVE",
    start_time=now(),
)
db.save(record)
```

**On `container.stopped`**:
```python
record = db.get_active_by_container_id(container_id)
end_time = now()
duration = (end_time - record.start_time).total_seconds() / 60
cost = round(duration * RATE_PER_MINUTE, 2)
record.update(status="COMPLETED", end_time=end_time, duration_minutes=duration, cost=cost)
```

**On `image.deleted`**: All ACTIVE records for that `image_id` are closed immediately with the current timestamp. This prevents "orphaned" records for containers that were destroyed alongside their image.

**Billing summary aggregation**: For the dashboard, the billing service groups records by `image_id`, sums costs, and for ACTIVE records, estimates the running cost up to `now()`.

---

## 9. Server-Side Proxy in Next.js

### What it is

In a Next.js application, **API routes** (`/app/api/...`) are server-side endpoints that run in Node.js, not in the browser. A **server-side proxy** is an API route that receives a request from the browser and forwards it to a backend service, then returns the response.

### Why this project uses it

Two reasons:
1. **CORS**: The browser blocks requests from `localhost:3000` (the UI) to `localhost:8080` (the API Gateway) unless the API Gateway explicitly allows it. By routing through Next.js, the browser only talks to `localhost:3000`, and CORS is not an issue.
2. **Cookie security**: The auth token is an HTTP-only cookie. The browser automatically includes it on same-origin requests. A server-side proxy can read and forward that cookie to the backend without exposing it to JavaScript.

### How it's implemented here

Example: `services/ui/app/api/containers/route.ts`

```typescript
export async function GET(request: NextRequest) {
    const cookieHeader = request.headers.get("cookie") ?? "";
    const response = await fetch(`${API_GATEWAY_URL}/api/containers`, {
        headers: { Cookie: cookieHeader },
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
}
```

The cookie from the browser is forwarded to the API Gateway. The gateway validates the JWT inside that cookie and returns the appropriate data.

For auth endpoints, the `Set-Cookie` header from the backend is forwarded back to the browser:
```typescript
const setCookie = backendResponse.headers.get("set-cookie");
if (setCookie) {
    nextResponse.headers.set("set-cookie", setCookie);
}
```

The API Gateway URL is configured via the environment variable `API_GATEWAY_EXTERNAL_URL`, defaulting to `http://localhost:8080`.

---

## 10. Async I/O and Thread Bridging in Python

### What it is

Python's `asyncio` allows concurrent I/O without threads: when a coroutine `await`s a network call, other coroutines can run while waiting for the response. FastAPI is built on `asyncio`.

However, some libraries — like `confluent-kafka` — are **blocking**. Their `poll()` method blocks the calling thread until a message arrives. Calling a blocking function directly in an `async` function would freeze the entire event loop, blocking all other requests.

**`asyncio.to_thread()`** solves this: it runs a blocking function in a separate thread pool thread, while the event loop stays free to handle other coroutines.

### Why this project uses it

The Kafka consumers need to poll for new messages in a loop. But the services are FastAPI apps — their entire lifecycle runs on an asyncio event loop. Blocking the loop would make the service unresponsive to HTTP requests while waiting for Kafka messages.

### How it's implemented here

In both the Service Discovery and Billing consumers:
```python
async def _consume_loop(self) -> None:
    while self._running:
        # Run blocking poll() in a thread, without blocking the event loop
        msg = await asyncio.to_thread(self.consumer.poll, 1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error("Kafka error: %s", msg.error())
            continue
        await self._dispatch(msg)
```

`asyncio.to_thread(self.consumer.poll, 1.0)` runs `consumer.poll(1.0)` in a thread. While that thread blocks for up to 1 second waiting for a message, the asyncio event loop is free to serve HTTP requests, run other tasks, etc.

**`_dispatch`** is itself `async` — once a message arrives, the handler (e.g., `_on_container_started`) is awaited normally in the event loop.

---

## Summary: How the Concepts Fit Together

```
User deploys a container
│
├── UI sends POST /api/containers to Next.js proxy
│     └── Next.js forwards to API Gateway (with JWT cookie)
│           └── API Gateway validates JWT (no Auth service call needed)
│                 └── Orchestrator builds image + runs container (DinD)
│                       └── Publishes container.started to Kafka
│                             ├── Service Discovery registers container in Consul
│                             │     └── LB's watcher detects change, updates cache
│                             └── Billing creates ACTIVE usage record
│
User sends request to their app
│
├── UI calls /apps/myapp/some/path
│     └── API Gateway checks routing cache
│           └── Cache miss → asks Load Balancer
│                 ├── LB queries Service Discovery (via circuit breaker)
│                 │     └── Returns list of healthy containers for "myapp"
│                 └── LB picks one with round-robin (atomic Redis INCR)
│                       └── API Gateway proxies request to container
│                             └── Records metrics (latency, status)
│
User deletes image
│
└── Orchestrator publishes image.deleted to Kafka
      ├── Service Discovery deregisters all Consul entries for that image
      └── Billing closes all ACTIVE records, calculates final cost
```

Every concept in this codebase solves a specific distributed systems problem: Kafka decouples services, Consul locates them, the circuit breaker protects them, Redis coordinates them, and JWT authenticates users across all of them.
