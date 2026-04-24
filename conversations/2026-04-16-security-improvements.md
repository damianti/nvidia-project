# Security Improvements — Session 2026-04-16

This document explains the 7 security features added to the project. For each one: what the concept is, why it matters, how it's implemented here, and what a fullstack engineer should know.

---

## 1. Rate Limiting

### What it is

Rate limiting controls how many requests a client can make to an endpoint within a time window. When the limit is exceeded, the server returns `429 Too Many Requests` instead of processing the request.

### Why it matters

Without rate limiting, the `/login` endpoint is vulnerable to **brute-force attacks** — an attacker can try millions of password combinations automatically until one works. It's one of the most basic protections any auth system needs.

### How it's implemented here

**Library:** `slowapi` — a FastAPI-compatible wrapper around `limits`, which is the same engine used by Flask-Limiter.

**File:** `services/auth-service/app/api/auth.py`

```python
limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...

@router.post("/signup")
@limiter.limit("3/minute")
async def signup(request: Request, ...):
    ...
```

The limiter is registered on the FastAPI app in `main.py`:
```python
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

`key_func=get_remote_address` uses the client's IP address as the rate limit key — each IP gets its own counter.

### Important facts

- **In production behind a proxy** (nginx, AWS ALB), the real client IP is in the `X-Forwarded-For` header, not `request.client.host`. If you don't handle this, every client looks like the same IP (the proxy's IP) and they all share one limit. `get_remote_address` in slowapi reads `X-Forwarded-For` automatically.
- **5/minute on login** is quite tight. Production systems typically use per-account limits too (e.g., lock the account after 10 failed attempts regardless of IP) to also protect against distributed attacks from many IPs.
- Rate limiting state is **in-memory by default** in slowapi. This means limits reset if the service restarts, and they don't work across multiple instances. For distributed rate limiting, you'd point slowapi at a Redis backend.

---

## 2. Token Revocation

### What it is

JWT tokens are **stateless** — the server issues them and never stores them. This means there's no built-in way to "cancel" a token before its expiry. Token revocation adds that capability by maintaining a **blocklist** of tokens that should no longer be accepted, even if they're cryptographically valid.

### Why it matters

When a user logs out, just deleting the cookie on the client side isn't enough. The token itself is still valid until it expires. If someone steals the token (from a log, a network sniff, or XSS) before the user logs out, they can use it for the remaining lifetime. Revocation closes this window.

### How it's implemented here

**New file:** `services/auth-service/app/services/token_blocklist.py`

The blocklist uses **Redis** as the store. The token is never stored raw — it's hashed with SHA-256 first:

```python
def _token_key(token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()
    return f"auth:blocklist:{digest}"
```

**On logout** (`api/auth.py`):
1. Extract the token from the cookie.
2. Decode it (without signature verification) to read the `exp` claim.
3. Calculate how many seconds remain until expiry.
4. Store `SHA256(token)` in Redis with that TTL.

```python
exp_claim = token_utils._get_exp_from_token(token)
remaining = int(exp_claim - datetime.now(timezone.utc).timestamp())
token_blocklist.block_token(token, ttl_seconds=remaining)
```

Redis **automatically deletes the key when the TTL expires** — so the blocklist never accumulates stale entries.

**On every request** (`utils/security.py`):
```python
if token_blocklist.is_blocked(token):
    raise HTTPException(status_code=401, detail="Token has been revoked")
```

**Graceful degradation:** If Redis is unavailable, `is_blocked()` returns `False` and the app keeps working — users just can't revoke tokens until Redis comes back.

### Important facts

- **TTL = remaining lifetime** is the key insight. You don't need to store the blocklist entry forever, only until the token would have expired anyway. After that, the token is invalid by its `exp` claim regardless.
- **Hashing before storing** prevents the blocklist from leaking valid tokens if Redis is compromised. An attacker who reads the hash can't reconstruct the original JWT.
- This pattern is sometimes called a **"denylist"** or **"revocation list"**. An alternative is **short-lived tokens + refresh tokens**: access tokens expire in 5 minutes, so revocation isn't needed — you just don't issue a new refresh token on logout. Both approaches are valid.
- The auth service uses **Redis DB 1** (`redis://redis:6379/1`) while the Load Balancer uses DB 0. Separating DB indexes keeps the namespaces clean even on a shared Redis instance.

---

## 3. Pagination

### What it is

Pagination limits how many records are returned by a list endpoint in a single response. Instead of returning all 10,000 containers at once, the client requests page 1 (items 1–50), page 2 (items 51–100), etc.

### Why it matters

An unbounded `SELECT * FROM containers WHERE user_id = X` will scan the entire table and load all rows into memory. As data grows, this query gets slower and uses more memory — it's a classic scalability problem that brings down databases under load.

### How it's implemented here

**Query params** added to `GET /api/images` and `GET /api/containers`:

```
GET /api/images?page=1&page_size=50
GET /api/containers?page=2&page_size=20
```

**Repository layer** (`repositories/images_repository.py`):
```python
def get_all_images(db, user_id, offset=0, limit=50):
    base = db.query(Image).filter(Image.user_id == user_id)
    total = base.count()
    items = base.order_by(Image.id.desc()).offset(offset).limit(limit).all()
    return items, total
```

SQLAlchemy translates this to:
```sql
SELECT COUNT(*) FROM images WHERE user_id = ?;
SELECT * FROM images WHERE user_id = ? ORDER BY id DESC LIMIT 50 OFFSET 0;
```

**Response headers** carry pagination metadata without changing the response body (no breaking change for existing clients):
```
X-Total-Count: 143
X-Page: 1
X-Page-Size: 50
```

### Important facts

- **OFFSET pagination has a hidden cost**: `OFFSET 1000 LIMIT 50` still reads 1050 rows internally and discards the first 1000. For very large datasets, **cursor-based pagination** (e.g., `WHERE id < last_seen_id LIMIT 50`) is more efficient because it uses an index seek instead of a full scan.
- **`ORDER BY` is required for consistent pagination**. Without it, the database can return rows in any order, and the same row might appear on two different pages or be skipped.
- **Returning total count is expensive** for large tables — `COUNT(*)` scans every row. Some APIs skip the total and only tell you if there's a next page (`has_next: true`). We keep it here because the dataset is small enough that it doesn't matter.
- The **response body stays `List[T]`** (no wrapper object), which means existing frontend code doesn't need to change. The metadata lives in headers instead.

---

## 4. Password Validation

### What it is

Password validation enforces minimum quality requirements before a password is accepted at registration time. If the password is too weak, the request is rejected with a `422 Unprocessable Entity` and a clear error message.

### Why it matters

`password: str` in Pydantic accepts any string, including an empty one. Users who set `password=""` or `password="a"` have effectively no protection. Enforcing a minimum standard at the schema level means the rule is applied everywhere that schema is used, not just in one route.

### How it's implemented here

**File:** `services/auth-service/app/schemas/user.py`

```python
class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v
```

Pydantic runs this validator before the route handler is ever called. The error is serialized as a standard `422` response with the message.

### Important facts

- **`@field_validator` is Pydantic v2 syntax**. In Pydantic v1 the equivalent is `@validator`. This project uses Pydantic v2.
- **Where to validate matters**. Validating at the Pydantic schema level means the rule applies everywhere the schema is used (REST endpoint, CLI script, tests). Validating inside the route handler means it only runs for that route.
- **These rules are minimal**. Production systems typically also enforce: no common passwords (checking against a dictionary), max length (to prevent DoS via bcrypt on very long inputs — bcrypt truncates at 72 bytes anyway), and optionally complexity rules (uppercase + special char). The right balance depends on your threat model.
- **bcrypt has a 72-byte input limit**. Any password longer than 72 bytes is silently truncated before hashing. This is a known bcrypt limitation — if your users might use very long passwords, pre-hash with SHA-256 before passing to bcrypt.

---

## 5. File Upload Size Limit

### What it is

An upload size limit rejects files that exceed a maximum byte threshold before they're fully written to disk, returning `413 Request Entity Too Large`.

### Why it matters

Without a size limit, a user can upload a 10 GB file and:
1. Exhaust disk space on the server (build contexts accumulate).
2. Exhaust memory if the file is read into a buffer before being written.
3. Cause the Docker build to fail after wasting time and resources.

### How it's implemented here

**File:** `services/orchestrator/app/services/build_context.py`

```python
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB

content = await file.read()  # reads the full upload into memory

if len(content) > MAX_UPLOAD_BYTES:
    raise HTTPException(
        status_code=413,
        detail=f"Upload too large: {len(content) / (1024*1024):.1f} MB (max 100 MB)"
    )
```

The check happens immediately after reading, before writing anything to disk.

### Important facts

- **Reading the whole file to check the size is not ideal for large uploads** — it loads everything into memory first. A better approach is streaming the upload and counting bytes as they arrive, aborting as soon as the limit is exceeded. FastAPI/Starlette support streaming via `request.stream()`. For the scale of this project, reading fully is fine.
- **The real first line of defense is the web server** (nginx, caddy). Configuring `client_max_body_size 100m;` in nginx rejects oversized requests at the network layer before they even reach the Python process. Python-level checks are a second line of defense.
- A **100 MB Dockerfile build context is already quite large**. A typical production limit is 50 MB. The right value depends on what users are expected to upload.

---

## 6. Dockerfile Content Validation

### What it is

Dockerfile validation scans the content of the uploaded Dockerfile for instructions that could be dangerous in a shared build environment, and rejects the upload before the build even starts.

### Why it matters

Users upload arbitrary Dockerfiles that the Orchestrator builds inside Docker-in-Docker. While DinD isolates the runtime, certain Dockerfile instructions can affect the build environment itself:

- `--network=host` exposes the host network stack during `docker build`, potentially allowing the build to reach internal services.
- `--privileged` gives the build elevated capabilities.
- `ADD http://...` downloads arbitrary files from the internet during the build, which can be used to exfiltrate secrets from build environment variables.

Catching these at upload time gives the user an immediate, clear error message instead of a cryptic build failure.

### How it's implemented here

**File:** `services/orchestrator/app/services/build_context.py`

```python
_DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"--network\s*=\s*host", "host network access (--network=host)"),
    (r"--privileged", "privileged mode (--privileged)"),
    (r"^ADD\s+https?://", "remote URL in ADD instruction — use COPY + curl instead"),
    (r"--security-opt", "custom security options (--security-opt)"),
]

def validate_dockerfile_content(dockerfile_path: Path) -> None:
    content = dockerfile_path.read_text(encoding="utf-8", errors="replace")
    for pattern, description in _DANGEROUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            raise HTTPException(
                status_code=400,
                detail=f"Dockerfile contains a forbidden instruction: {description}",
            )
```

This is called from `validate_context()`, which runs after the archive is extracted but before `docker build` is invoked.

### Important facts

- **Regex-based checks can be bypassed** by a determined attacker (e.g., splitting a flag across a line continuation `\`). This is a best-effort guardrail, not a security boundary. A proper solution is to parse the Dockerfile AST using a library like `dockerfile-parse`.
- **The real sandbox is DinD itself**. Docker-in-Docker limits what the built container can do at runtime. The Dockerfile validation is an extra layer to catch obvious mistakes or misuse early.
- In production platforms (like Google Cloud Build, AWS CodeBuild), user-provided Dockerfiles run in fully isolated VMs or sandboxed environments with stripped capabilities. The validation here is appropriate for a learning project but would need to be more rigorous in a real multi-tenant system.

---

## 7. Secure Cookie via Environment Variable

### What it is

The `Secure` flag on a cookie tells the browser to **only send the cookie over HTTPS connections**. If the flag is absent, the cookie is sent over plain HTTP too, meaning it can be intercepted by a network observer (man-in-the-middle attack).

### Why it matters

The auth token is stored in an HTTP-only cookie. HTTP-only prevents JavaScript from reading it (XSS protection). But without `Secure=True`, a browser on a coffee-shop WiFi will send the cookie over plain HTTP — and the token can be captured by anyone watching the network.

In development, services run on `localhost` over HTTP, so `Secure=True` would break local login (cookies would never be sent). The solution is to make it configurable per environment.

### How it's implemented here

**File:** `services/auth-service/app/utils/config.py`
```python
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"
```

**File:** `services/auth-service/app/api/auth.py`
```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=SECURE_COOKIES,   # False in dev, True in prod
    samesite="lax",
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/",
)
```

**`docker-compose.yml`** passes `SECURE_COOKIES=${SECURE_COOKIES:-false}` — defaults to `false` for local development. A production deployment sets `SECURE_COOKIES=true` in its environment.

### Important facts

- **`HttpOnly` and `Secure` are complementary, not alternatives**:
  - `HttpOnly` — JavaScript can't read the cookie → protects against XSS.
  - `Secure` — browser only sends the cookie over HTTPS → protects against network interception.
  - You want both in production.
- **`SameSite=Lax`** is also set here. It means the cookie is sent on same-site requests and on top-level cross-site navigations (e.g., clicking a link), but not on cross-site background requests. This protects against **CSRF** (Cross-Site Request Forgery) attacks where a malicious page tries to make background requests to your API.
- `SameSite=Strict` would be even more protective but breaks the UX in some OAuth flows. `Lax` is the standard production default.
- On `localhost`, `Secure=True` works in some browsers but not all. Chrome treats `localhost` as a secure origin and sends secure cookies there; Firefox does not. Using `SECURE_COOKIES=false` in development avoids this inconsistency.
