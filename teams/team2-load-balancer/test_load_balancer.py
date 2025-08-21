#!/usr/bin/env python3
"""
Test script for the Load Balancer API
This script demonstrates how to register services and test the load balancer
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

# Load balancer API base URL
BASE_URL = "http://localhost:3001"

async def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Health check response: {response.json()}")
        return response.status_code == 200

async def register_sample_service():
    """Register a sample service with containers"""
    print("Registering sample service...")
    
    # Sample container data
    containers = [
        {
            "container_id": "container-1",
            "name": "sample-app-1",
            "port": 4001,
            "image_id": 1,
            "status": "healthy",
            "active_connections": 0
        },
        {
            "container_id": "container-2", 
            "name": "sample-app-2",
            "port": 4002,
            "image_id": 1,
            "status": "healthy",
            "active_connections": 0
        }
    ]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/services/1/register",
            params={"image_name": "sample-app"},
            json=containers
        )
        print(f"Service registration response: {response.json()}")
        return response.status_code == 200

async def get_service_info():
    """Get information about the registered service"""
    print("Getting service info...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/services/1")
        print(f"Service info: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

async def get_all_services():
    """Get all registered services"""
    print("Getting all services...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/services")
        print(f"All services: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

async def get_port_mappings():
    """Get port mappings"""
    print("Getting port mappings...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/port-mappings")
        print(f"Port mappings: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

async def get_stats():
    """Get load balancer statistics"""
    print("Getting load balancer stats...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/stats")
        print(f"Load balancer stats: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

async def test_proxy_request():
    """Test proxy request (this will fail if no actual containers are running)"""
    print("Testing proxy request...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/proxy/1/test")
            print(f"Proxy response status: {response.status_code}")
        except Exception as e:
            print(f"Proxy request failed (expected if no containers running): {e}")

async def main():
    """Run all tests"""
    print("Starting Load Balancer API tests...")
    print("=" * 50)
    
    # Test health check
    await test_health_check()
    print()
    
    # Register sample service
    await register_sample_service()
    print()
    
    # Get service information
    await get_service_info()
    print()
    
    # Get all services
    await get_all_services()
    print()
    
    # Get port mappings
    await get_port_mappings()
    print()
    
    # Get statistics
    await get_stats()
    print()
    
    # Test proxy (will fail without running containers)
    await test_proxy_request()
    print()
    
    print("Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
