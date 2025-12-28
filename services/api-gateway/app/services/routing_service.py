# Routing Service - Business logic for routing requests
from typing import Optional
from datetime import datetime, timedelta

from app.services.routing_cache import Cache, CacheEntry
from app.models.routing import RoutingInfo
from app.clients.lb_client import LoadBalancerClient
from app.utils.config import DEFAULT_CACHE_TTL
from app.services.user_id_cache import UserIdCache


def create_cache_entry_from_routing_info(
    routing_info: RoutingInfo,
    app_hostname: str,
    user_id_cache: UserIdCache,
) -> CacheEntry:
    """Creates CacheEntry from load balancer response"""
    ttl = routing_info.ttl if routing_info.ttl else DEFAULT_CACHE_TTL
    expires_at = datetime.now() + timedelta(seconds=ttl)
    user_id = user_id_cache.get(app_hostname)
    return CacheEntry(
        target_host=routing_info.target_host,
        target_port=routing_info.target_port,
        container_id=routing_info.container_id,
        image_id=routing_info.image_id,
        expires_at=expires_at,
        user_id=user_id,
    )


async def get_routing_info(
    app_hostname: str,
    lb_client: LoadBalancerClient,
) -> Optional[RoutingInfo]:
    """
    Query Load Balancer for routing information for a given app_hostname.
    """
    result = await lb_client.route(app_hostname)

    if result.ok and result.data:
        return result.data

    return None


async def resolve_route(
    app_hostname: str,
    client_ip: str,
    cached_memory: Cache,
    lb_client: LoadBalancerClient,
    user_id_cache: UserIdCache,
) -> Optional[CacheEntry]:
    """
    Resolve route for a user app.
    Checks cache first, then queries Load Balancer if needed.
    """
    # 1) Check cache first
    cached_entry = cached_memory.get(app_hostname, client_ip)
    if cached_entry:
        return cached_entry

    # 2) Cache miss: query Load Balancer
    routing_info = await get_routing_info(app_hostname, lb_client)
    if not routing_info:
        return None

    # 3) Create cache entry and store it
    entry = create_cache_entry_from_routing_info(
        routing_info, app_hostname, user_id_cache
    )
    cached_memory.set(app_hostname, client_ip, entry)

    return entry
