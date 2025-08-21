#!/usr/bin/env python3
"""
Test script for the Intelligent Load Balancer API
This script demonstrates how the load balancer routes requests to different services
based on the URL path pattern.
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

async def test_system_services():
    """Test system services endpoint"""
    print("Testing system services...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/system-services")
        print(f"System services: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

async def test_orchestrator_routing():
    """Test routing to orchestrator service"""
    print("Testing orchestrator routing...")
    async with httpx.AsyncClient() as client:
        # Test auth endpoint (should go to orchestrator)
        try:
            response = await client.get(f"{BASE_URL}/auth/login")
            print(f"Auth endpoint response status: {response.status_code}")
        except Exception as e:
            print(f"Auth endpoint failed (expected if orchestrator not running): {e}")
        
        # Test images endpoint (should go to orchestrator)
        try:
            response = await client.get(f"{BASE_URL}/images")
            print(f"Images endpoint response status: {response.status_code}")
        except Exception as e:
            print(f"Images endpoint failed (expected if orchestrator not running): {e}")
        
        # Test containers endpoint (should go to orchestrator)
        try:
            response = await client.get(f"{BASE_URL}/containers")
            print(f"Containers endpoint response status: {response.status_code}")
        except Exception as e:
            print(f"Containers endpoint failed (expected if orchestrator not running): {e}")

async def test_billing_routing():
    """Test routing to billing service"""
    print("Testing billing routing...")
    async with httpx.AsyncClient() as client:
        # Test users endpoint (should go to billing)
        try:
            response = await client.get(f"{BASE_URL}/users")
            print(f"Users endpoint response status: {response.status_code}")
        except Exception as e:
            print(f"Users endpoint failed (expected if billing not running): {e}")
        
        # Test billing endpoint (should go to billing)
        try:
            response = await client.get(f"{BASE_URL}/billing")
            print(f"Billing endpoint response status: {response.status_code}")
        except Exception as e:
            print(f"Billing endpoint failed (expected if billing not running): {e}")

async def register_sample_user_service():
    """Register a sample user service with containers"""
    print("Registering sample user service...")
    
    # Sample container data
    containers = [
        {
            "container_id": "user-app-1",
            "name": "user-web-app-1",
            "port": 4001,
            "image_id": 1,
            "status": "healthy",
            "active_connections": 0
        },
        {
            "container_id": "user-app-2", 
            "name": "user-web-app-2",
            "port": 4002,
            "image_id": 1,
            "status": "healthy",
            "active_connections": 0
        }
    ]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/services/1/register",
            params={"image_name": "user-web-app"},
            json=containers
        )
        print(f"User service registration response: {response.json()}")
        return response.status_code == 200

async def test_user_container_routing():
    """Test routing to user containers"""
    print("Testing user container routing...")
    async with httpx.AsyncClient() as client:
        # Test user container endpoint (should go to user container)
        try:
            response = await client.get(f"{BASE_URL}/api/v1/proxy/1/api/users")
            print(f"User container proxy response status: {response.status_code}")
        except Exception as e:
            print(f"User container proxy failed (expected if containers not running): {e}")
        
        # Test another user container endpoint
        try:
            response = await client.get(f"{BASE_URL}/api/v1/proxy/1/dashboard")
            print(f"User container dashboard response status: {response.status_code}")
        except Exception as e:
            print(f"User container dashboard failed (expected if containers not running): {e}")

async def test_unknown_routing():
    """Test routing for unknown paths"""
    print("Testing unknown path routing...")
    async with httpx.AsyncClient() as client:
        # Test unknown endpoint (should default to orchestrator)
        try:
            response = await client.get(f"{BASE_URL}/unknown/endpoint")
            print(f"Unknown endpoint response status: {response.status_code}")
        except Exception as e:
            print(f"Unknown endpoint failed (expected if orchestrator not running): {e}")

async def test_stats():
    """Test load balancer statistics"""
    print("Testing load balancer stats...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/stats")
        print(f"Load balancer stats: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

async def test_health_checks():
    """Test health check functionality"""
    print("Testing health checks...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/health-check")
        print(f"Health check trigger response: {response.json()}")
        return response.status_code == 200

async def main():
    """Run all tests"""
    print("Starting Intelligent Load Balancer API tests...")
    print("=" * 60)
    
    # Test basic functionality
    await test_health_check()
    print()
    
    # Test system services
    await test_system_services()
    print()
    
    # Test routing to orchestrator
    await test_orchestrator_routing()
    print()
    
    # Test routing to billing
    await test_billing_routing()
    print()
    
    # Register user service
    await register_sample_user_service()
    print()
    
    # Test routing to user containers
    await test_user_container_routing()
    print()
    
    # Test unknown path routing
    await test_unknown_routing()
    print()
    
    # Test statistics
    await test_stats()
    print()
    
    # Test health checks
    await test_health_checks()
    print()
    
    print("Intelligent routing tests completed!")
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("- Auth, Images, Containers → Orchestrator (port 3003)")
    print("- Users, Billing → Billing Service (port 8000)")
    print("- /proxy/{image_id}/{path} → User Containers (ports 4000+)")
    print("- Unknown paths → Orchestrator (default)")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
