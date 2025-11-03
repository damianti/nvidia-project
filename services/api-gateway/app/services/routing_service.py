# Routing Service - Business logic for routing requests
from typing import Optional
from datetime import datetime, timedelta

from app.services.routing_cache import Cache, CacheEntry
from app.models.routing import RoutingInfo
from app.clients.lb_client import LoadBalancerClient
from app.utils.config import DEFAULT_CACHE_TTL


def create_cache_entry_from_routing_info(routing_info: RoutingInfo) -> CacheEntry:
    """Creates CacheEntry from load balancer response"""
    ttl = routing_info.ttl if routing_info.ttl else DEFAULT_CACHE_TTL
    expires_at = datetime.now() + timedelta(seconds=ttl)

    return CacheEntry(
        target_host=routing_info.target_host,
        target_port=routing_info.target_port,
        container_id=routing_info.container_id,
        image_id=routing_info.image_id,
        expires_at=expires_at
    )


async def get_routing_info(
    website_url: str,
    lb_client: LoadBalancerClient
) -> Optional[RoutingInfo]:
    """
    Query Load Balancer for routing information.
    
    Args:
        website_url: Website URL to route
        lb_client: Load Balancer client instance
        
    Returns:
        RoutingInfo if found, None otherwise
    """
    result = await lb_client.route(website_url)
    
    if result.ok and result.data:
        return result.data
    
    return None


async def resolve_route(
    website_url: str,
    client_ip: str,
    cached_memory: Cache,
    lb_client: LoadBalancerClient
) -> Optional[CacheEntry]:
    """
    Resolve route for a website URL.
    Checks cache first, then queries Load Balancer if needed.
    
    Args:
        website_url: Normalized website URL
        client_ip: Client IP address
        cached_memory: Cache instance
        lb_client: Load Balancer client
        
    Returns:
        CacheEntry if route found, None otherwise
    """
    # Check cache first
    cached_entry = cached_memory.get(website_url, client_ip)
    if cached_entry:
        return cached_entry
    
    # Cache miss: query Load Balancer
    routing_info = await get_routing_info(website_url, lb_client)
    if not routing_info:
        return None
    
    # Create cache entry and store it
    entry = create_cache_entry_from_routing_info(routing_info)
    cached_memory.set(website_url, client_ip, entry)
    
    return entry
