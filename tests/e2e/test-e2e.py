#!/usr/bin/env python3
"""
End-to-end test script for Cloud Run-style image upload and deployment.
Tests the complete flow: upload -> build -> deploy -> route requests.
"""
import os
import sys
import time
import json
import tarfile
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:3002")
TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "testpass123")
APP_HOSTNAME = os.getenv("APP_HOSTNAME", "testapp.localhost")

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

def print_step(step_num: int, total: int, message: str):
    """Print a step message"""
    print(f"{Colors.YELLOW}[{step_num}/{total}] {message}{Colors.NC}")

def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.NC}")

def authenticate() -> Optional[str]:
    """Authenticate and return JWT token"""
    print_step(1, 6, "Authenticating user...")
    
    session = requests.Session()
    
    # Try login first
    login_url = f"{API_GATEWAY_URL}/auth/login"
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = session.post(login_url, json=login_data, timeout=10)
        if response.status_code == 200:
            # Token is in cookie, session will handle it
            print_success("Authentication successful (login)")
            return session
    except requests.RequestException as e:
        print(f"Login failed: {e}")
    
    # Try registration if login fails
    print("Login failed, attempting registration...")
    signup_url = f"{API_GATEWAY_URL}/auth/signup"
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": "testuser"
    }
    
    try:
        response = session.post(signup_url, json=signup_data, timeout=10)
        if response.status_code in (200, 201):
            print("Registration successful, logging in...")
            # After signup, login to get the token
            login_response = session.post(login_url, json=login_data, timeout=10)
            if login_response.status_code == 200:
                print_success("Authentication successful (registration + login)")
                return session
            else:
                print_error(f"Login after registration failed: {login_response.status_code} - {login_response.text}")
                return None
        else:
            print_error(f"Registration failed: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print_error(f"Registration failed: {e}")
        return None

def create_test_archive() -> Optional[str]:
    """Create a tar.gz archive of the test app"""
    print_step(2, 6, "Creating test app archive...")
    
    test_app_dir = Path(__file__).parent / "test-app"
    if not test_app_dir.exists():
        print_error(f"Test app directory not found: {test_app_dir}")
        return None
    
    # Create temporary archive
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
    archive_path = temp_file.name
    temp_file.close()
    
    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_app_dir / "Dockerfile", arcname="Dockerfile")
            tar.add(test_app_dir / "app.py", arcname="app.py")
            tar.add(test_app_dir / "requirements.txt", arcname="requirements.txt")
        
        print_success(f"Archive created: {archive_path}")
        return archive_path
    except Exception as e:
        print_error(f"Failed to create archive: {e}")
        return None

def upload_and_build_image(session: requests.Session, archive_path: str) -> Optional[int]:
    """Upload image and wait for build to complete"""
    print_step(3, 6, "Uploading image and building...")
    
    upload_url = f"{ORCHESTRATOR_URL}/api/images"
    
    with open(archive_path, "rb") as f:
        files = {
            "file": ("test-app.tar.gz", f, "application/gzip")
        }
        data = {
            "name": "test-app",
            "tag": "latest",
            "app_hostname": APP_HOSTNAME,
            "container_port": "8080",
            "min_instances": "1",
            "max_instances": "2",
            "cpu_limit": "0.5",
            "memory_limit": "512m"
        }
        
        # Get token from session cookies
        cookies = session.cookies.get_dict()
        headers = {}
        if "access_token" in cookies:
            headers["Authorization"] = f"Bearer {cookies['access_token']}"
        
        try:
            response = session.post(upload_url, files=files, data=data, headers=headers, timeout=60)
            if response.status_code != 200:
                print_error(f"Upload failed: {response.status_code} - {response.text}")
                return None
            
            image_data = response.json()
            image_id = image_data.get("id")
            
            if not image_id:
                print_error(f"No image ID in response: {image_data}")
                return None
            
            print_success(f"Image uploaded. ID: {image_id}")
            
            # Wait for build to complete
            print("Waiting for build to complete...")
            max_wait = 120
            wait_count = 0
            
            while wait_count < max_wait:
                time.sleep(2)
                wait_count += 2
                
                image_url = f"{ORCHESTRATOR_URL}/api/images/{image_id}"
                response = session.get(image_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    image_info = response.json()
                    status = image_info.get("status", "building")
                    
                    if status == "ready":
                        print_success("Build completed successfully")
                        return image_id
                    elif status == "build_failed":
                        print_error("Build failed!")
                        # Get build logs
                        logs_url = f"{ORCHESTRATOR_URL}/api/images/{image_id}/build-logs"
                        logs_response = session.get(logs_url, headers=headers, timeout=10)
                        if logs_response.status_code == 200:
                            logs_data = logs_response.json()
                            print("Build logs:")
                            print(logs_data.get("build_logs", "No logs available"))
                        return None
                
                print(".", end="", flush=True)
            
            print_error(f"Build timeout after {max_wait}s")
            return None
            
        except requests.RequestException as e:
            print_error(f"Upload failed: {e}")
            return None

def create_containers(session: requests.Session, image_id: int) -> Optional[int]:
    """Create containers from the image"""
    print_step(4, 6, "Creating containers...")
    
    create_url = f"{ORCHESTRATOR_URL}/api/containers/{image_id}"
    
    cookies = session.cookies.get_dict()
    headers = {"Content-Type": "application/json"}
    if "access_token" in cookies:
        headers["Authorization"] = f"Bearer {cookies['access_token']}"
    
    data = {
        "name": "test-container",
        "image_id": image_id,
        "count": 1
    }
    
    try:
        response = session.post(create_url, json=data, headers=headers, timeout=30)
        if response.status_code != 200:
            print_error(f"Failed to create containers: {response.status_code} - {response.text}")
            return None
        
        containers = response.json()
        if not containers or len(containers) == 0:
            print_error("No containers created")
            return None
        
        container_id = containers[0].get("id")
        if not container_id:
            print_error(f"No container ID in response: {containers}")
            return None
        
        print_success(f"Container created. ID: {container_id}")
        
        # Wait for container to start
        print("Waiting for container to start...")
        time.sleep(5)
        
        return container_id
        
    except requests.RequestException as e:
        print_error(f"Failed to create containers: {e}")
        return None

def test_routing() -> bool:
    """Test routing via API Gateway"""
    print_step(5, 6, "Testing routing via API Gateway...")
    
    # Test path-based routing
    route_url = f"{API_GATEWAY_URL}/apps/{APP_HOSTNAME}/"
    headers = {"Host": APP_HOSTNAME}
    
    try:
        response = requests.get(route_url, headers=headers, timeout=10)
        if response.status_code == 200:
            if "Hello from Cloud Run-style app" in response.text:
                print_success("Path-based routing works!")
            else:
                print_error(f"Unexpected response: {response.text}")
                return False
        else:
            print_error(f"Routing failed: {response.status_code} - {response.text}")
            return False
        
        # Test nested path
        nested_url = f"{API_GATEWAY_URL}/apps/{APP_HOSTNAME}/test/hello"
        response = requests.get(nested_url, headers=headers, timeout=10)
        if response.status_code == 200:
            if "Path-based routing works" in response.text:
                print_success("Nested path routing works!")
                return True
            else:
                print_error(f"Unexpected nested path response: {response.text}")
                return False
        else:
            print_error(f"Nested path routing failed: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print_error(f"Routing test failed: {e}")
        return False

def cleanup(session: requests.Session, image_id: int, container_id: int):
    """Cleanup test resources"""
    print_step(6, 6, "Cleanup...")
    
    response = input("Delete test image and containers? (y/N): ")
    if response.lower() != 'y':
        print("Skipping cleanup")
        return
    
    cookies = session.cookies.get_dict()
    headers = {}
    if "access_token" in cookies:
        headers["Authorization"] = f"Bearer {cookies['access_token']}"
    
    # Delete container
    delete_container_url = f"{ORCHESTRATOR_URL}/api/containers/{container_id}"
    try:
        session.delete(delete_container_url, headers=headers, timeout=10)
    except:
        pass
    
    # Delete image
    delete_image_url = f"{ORCHESTRATOR_URL}/api/images/{image_id}"
    try:
        session.delete(delete_image_url, headers=headers, timeout=10)
    except:
        pass
    
    print_success("Cleanup completed")

def main():
    """Main test flow"""
    print(f"{Colors.YELLOW}=== End-to-End Test Script ==={Colors.NC}")
    print(f"API Gateway: {API_GATEWAY_URL}")
    print(f"Orchestrator: {ORCHESTRATOR_URL}")
    print(f"App Hostname: {APP_HOSTNAME}")
    print()
    
    # Step 1: Authenticate
    session = authenticate()
    if not session:
        print_error("Authentication failed")
        sys.exit(1)
    
    # Step 2: Create archive
    archive_path = create_test_archive()
    if not archive_path:
        sys.exit(1)
    
    try:
        # Step 3: Upload and build
        image_id = upload_and_build_image(session, archive_path)
        if not image_id:
            sys.exit(1)
        
        # Step 4: Create containers
        container_id = create_containers(session, image_id)
        if not container_id:
            sys.exit(1)
        
        # Step 5: Test routing
        if not test_routing():
            sys.exit(1)
        
        # Step 6: Cleanup
        cleanup(session, image_id, container_id)
        
        print()
        print(f"{Colors.GREEN}=== All tests passed! ==={Colors.NC}")
        
    finally:
        # Cleanup archive
        if archive_path and os.path.exists(archive_path):
            os.unlink(archive_path)

if __name__ == "__main__":
    main()
