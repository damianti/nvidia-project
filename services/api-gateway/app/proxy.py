from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, Depends, HTTPException
import os
import httpx
from urllib.parse import urlencode
import logging
import json
from typing import Optional
from datetime import datetime, timedelta


from app.routing_cache import Cache, CacheEntry

client = httpx.AsyncClient(follow_redirects=True)

logger = logging.getLogger(__name__)
load_dotenv()
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:3003")
LOAD_BALANCER_URL = os.getenv("LOAD_BALANCER_URL", "http://load-balancer:3004")
TARGET_HOST = os.getenv("TARGET_HOST", "docker-dind")
router = APIRouter(tags=["proxy"])


def get_cached_memory(request: Request)-> Cache:
    website_cache = getattr(request.app.state, "cached_memory", None)
    if not website_cache:
        raise HTTPException(status_code=500, detail="Cached memory not initialized")
    return website_cache

def extract_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
        return client_ip
    
    return request.client.host if request.client.host is not None else ""

async def proxy_to_target(
    request: Request,
    target_url: str,
    target_headers: dict,
    body: bytes)-> Response:
    """
    Does proxy from request to target URL.
    Returns: Response with content, status_code, headers
    """
    try:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=target_headers,
            content=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to {target_url}: {e}")
        return Response(
            content=f"Proxy error: {str(e)}",
            status_code=502
        )

def prepare_proxy_headers(request:Request) -> dict:
    """Prepares headers for proxy, removing host and content-length"""
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    return headers

async def query_load_balancer(website_url: str) -> Optional[dict]:
    base_url = f"{LOAD_BALANCER_URL}/route"
    try:
        response = await client.post(
                url=base_url,
                json={"website_url": website_url},
                timeout=0.5
            )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"Website not found: {website_url}")
            return None
        elif response.status_code == 503:
            logger.warning(f"No containers available for: {website_url}")
            return None
        else:
            logger.error(f"LB returned {response.status_code}: {response.text}")
            return None

    except httpx.TimeoutException:
        logger.error("LB timeout")
        return None
    except Exception as e:
        logger.error(f"Error consulting LB: {e}")
        return None

def create_cache_entry_from_routing_info(routing_info: dict)-> CacheEntry:                
    """ Creates CacheEntry from load balancer response"""
    ttl = routing_info.get("ttl", 1800)
    expires_at = datetime.now() + timedelta(seconds=ttl)

    return CacheEntry (
        target_host = routing_info["target_host"],
        target_port = routing_info["target_port"],
        container_id=routing_info["container_id"],
        image_id=routing_info["image_id"],
        expires_at=expires_at
)

async def proxy_to_container(
    request: Request,
    cached_entry: CacheEntry,
    cached_memory: Cache,
    website_url: str,
    client_ip: str ) -> Response:
    
    target_url = f"http://{cached_entry.target_host}:{cached_entry.target_port}"
    headers = prepare_proxy_headers(request)
    body = await request.body()

    response = await proxy_to_target(request, target_url, headers, body)

    if response.status_code >= 500:
        logger.warning(f"Container {target_url} failed, invalidating cache ")
        cached_memory.invalidate(website_url, client_ip)
    
    return response


def normalize_website_url(url: str) -> str:
    """Normaliza website_url: lowercase, strip, quita protocolo y puerto"""
    if not url:
        return ""
    normalized = url.strip().lower()
    # Quitar protocolo si existe
    if normalized.startswith("https://"):
        normalized = normalized[8:]  # len("https://") = 8
    elif normalized.startswith("http://"):
        normalized = normalized[7:]  # len("http://") = 7
    # Quitar puerto si existe (ej: localhost:8080 -> localhost)
    if ":" in normalized:
        normalized = normalized.split(":")[0]
    # Quitar trailing slash opcional
    normalized = normalized.rstrip("/")
    return normalized

@router.api_route("/route", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
async def post_route(
    request: Request,
    cached_memory: Cache = Depends(get_cached_memory)
    ):
    
    host_header = request.headers.get("Host", "").strip().lower()
    if not host_header:
        return Response(content="Missing Host header", status_code=400)
    
    website_url = normalize_website_url(host_header)
    if not website_url:
        return Response(content="Invalid Host header", status_code=400)
    
    client_ip = extract_client_ip(request)
    cached_entry = cached_memory.get(website_url, client_ip)
    
    if cached_entry:
        return await proxy_to_container(
            request, cached_entry, cached_memory, website_url, client_ip
        )

    routing_info = await query_load_balancer(website_url)

    if not routing_info:
        return Response(
            content="Website not found or no containers available",
            status_code=503
        )

    entry = create_cache_entry_from_routing_info(routing_info)
    cached_memory.set(website_url, client_ip, entry)

    return await proxy_to_container(
        request, entry, cached_memory, website_url, client_ip
    )
    

@router.api_route("/api/{path:path}", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
async def proxy_api(path:str, request: Request):

    base_url = f"{ORCHESTRATOR_URL}/api/{path}"
    if request.query_params:
        query_string = urlencode(request.query_params)
        URL_destiny = f"{base_url}?{query_string}"
    else:
        URL_destiny = base_url
    
    headers = prepare_proxy_headers(request)
    body = await request.body()

    return await proxy_to_target(request, URL_destiny, headers, body)
