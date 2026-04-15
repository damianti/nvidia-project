"""Redis-backed JWT blocklist for token revocation on logout."""

import hashlib
import logging
from typing import Optional

import redis as redis_lib

from app.utils.config import REDIS_URL

logger = logging.getLogger("auth-service")

_client: Optional[redis_lib.Redis] = None

BLOCKLIST_PREFIX = "auth:blocklist:"


def init_redis() -> None:
    """Initialize the Redis connection. Called on app startup."""
    global _client
    try:
        _client = redis_lib.from_url(REDIS_URL, decode_responses=True)
        _client.ping()
        logger.info("token_blocklist.redis_connected", extra={"url": REDIS_URL})
    except Exception as e:
        logger.warning(
            "token_blocklist.redis_unavailable",
            extra={"error": str(e)},
        )
        _client = None


def close_redis() -> None:
    """Close the Redis connection. Called on app shutdown."""
    global _client
    if _client:
        _client.close()
        _client = None


def _token_key(token: str) -> str:
    """Hash the token before storing so we never persist the raw JWT in Redis."""
    digest = hashlib.sha256(token.encode()).hexdigest()
    return f"{BLOCKLIST_PREFIX}{digest}"


def block_token(token: str, ttl_seconds: int) -> None:
    """Add a token to the blocklist with a TTL matching its remaining lifetime.

    If Redis is unavailable the call is a no-op — the token stays valid until
    expiry, which is an acceptable degradation.
    """
    if _client is None:
        logger.warning("token_blocklist.block_skipped_no_redis")
        return
    try:
        key = _token_key(token)
        _client.setex(key, ttl_seconds, "1")
        logger.info("token_blocklist.blocked", extra={"ttl": ttl_seconds})
    except Exception as e:
        logger.error("token_blocklist.block_failed", extra={"error": str(e)})


def is_blocked(token: str) -> bool:
    """Return True if the token has been revoked (is in the blocklist)."""
    if _client is None:
        return False
    try:
        return _client.exists(_token_key(token)) == 1
    except Exception as e:
        logger.error("token_blocklist.check_failed", extra={"error": str(e)})
        return False
