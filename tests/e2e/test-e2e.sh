#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_GATEWAY_URL="${API_GATEWAY_URL:-http://localhost:8080}"
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"
TEST_PASSWORD="${TEST_PASSWORD:-testpass123}"
APP_HOSTNAME="${APP_HOSTNAME:-testapp.localhost}"

echo -e "${YELLOW}=== End-to-End Test Script ===${NC}"
echo "API Gateway: $API_GATEWAY_URL"
echo "App Hostname: $APP_HOSTNAME"
echo ""

# Step 1: Register/Login user
echo -e "${YELLOW}[1/6] Authenticating user...${NC}"

# Try login first
LOGIN_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_GATEWAY_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}" \
  -c /tmp/test_cookies.txt)

if [ "$LOGIN_HTTP_CODE" != "200" ]; then
  # Try to register first if login fails
  echo "Login failed, attempting registration..."
  REGISTER_RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/auth/signup" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\", \"username\": \"testuser\"}")
  
  # Check if registration was successful
  if echo "$REGISTER_RESPONSE" | grep -q "error\|detail"; then
    echo -e "${RED}Registration failed. Response: $REGISTER_RESPONSE${NC}"
    exit 1
  fi
  
  # After signup, login to get the token
  echo "Registration successful, logging in..."
  LOGIN_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_GATEWAY_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}" \
    -c /tmp/test_cookies.txt)
  
  if [ "$LOGIN_HTTP_CODE" != "200" ]; then
    echo -e "${RED}Failed to login after registration. HTTP Code: $LOGIN_HTTP_CODE${NC}"
    exit 1
  fi
fi

# Verify cookies were set
if [ ! -f /tmp/test_cookies.txt ] || ! grep -q "access_token" /tmp/test_cookies.txt; then
  echo -e "${RED}Failed to get authentication cookie${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Authentication successful${NC}"
echo ""

# Step 2: Create test app archive
echo -e "${YELLOW}[2/6] Creating test app archive...${NC}"
TEST_APP_DIR="$(dirname "$0")/test-app"
ARCHIVE_PATH="/tmp/test-app.tar.gz"

cd "$TEST_APP_DIR" || exit 1
tar -czf "$ARCHIVE_PATH" Dockerfile app.py requirements.txt
cd - > /dev/null

if [ ! -f "$ARCHIVE_PATH" ]; then
  echo -e "${RED}Failed to create archive${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Archive created: $ARCHIVE_PATH${NC}"
echo ""

# Step 3: Upload image and build
echo -e "${YELLOW}[3/6] Uploading image and building...${NC}"

# Verify archive exists
if [ ! -f "$ARCHIVE_PATH" ]; then
  echo -e "${RED}Archive file not found: $ARCHIVE_PATH${NC}"
  exit 1
fi

UPLOAD_RESPONSE=$(curl -s -L -X POST "$API_GATEWAY_URL/api/images" \
  -b /tmp/test_cookies.txt \
  -F "name=test-app" \
  -F "tag=latest" \
  -F "app_hostname=$APP_HOSTNAME" \
  -F "container_port=8080" \
  -F "min_instances=1" \
  -F "max_instances=2" \
  -F "cpu_limit=0.5" \
  -F "memory_limit=512m" \
  -F "file=@$ARCHIVE_PATH" \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | grep -oE 'HTTP_CODE:[0-9]+' | grep -oE '[0-9]+' || echo "")
UPLOAD_BODY=$(echo "$UPLOAD_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" != "200" ]; then
  echo -e "${RED}Failed to upload image. HTTP Code: $HTTP_CODE${NC}"
  echo "Response: $UPLOAD_BODY"
  exit 1
fi

IMAGE_ID=$(echo "$UPLOAD_BODY" | grep -oE '"id"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1 || echo "")

if [ -z "$IMAGE_ID" ]; then
  echo -e "${RED}Failed to extract image ID from response. Response: $UPLOAD_BODY${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Image uploaded. ID: $IMAGE_ID${NC}"

# Wait for build to complete (poll build status)
echo "Waiting for build to complete..."
MAX_WAIT=120
WAIT_COUNT=0
BUILD_STATUS="building"

while [ "$BUILD_STATUS" = "building" ] && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  sleep 2
  WAIT_COUNT=$((WAIT_COUNT + 2))
  
  IMAGE_INFO=$(curl -s -X GET "$API_GATEWAY_URL/api/images/$IMAGE_ID" \
    -b /tmp/test_cookies.txt)
  
  BUILD_STATUS=$(echo "$IMAGE_INFO" | grep -oE '"status"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "building")
  
  if [ "$BUILD_STATUS" = "ready" ]; then
    echo -e "${GREEN}✓ Build completed successfully${NC}"
    break
  elif [ "$BUILD_STATUS" = "build_failed" ]; then
    echo -e "${RED}Build failed!${NC}"
    echo "Build logs:"
    curl -s -X GET "$API_GATEWAY_URL/api/images/$IMAGE_ID/build-logs" \
      -b /tmp/test_cookies.txt | jq -r '.build_logs' || echo "Could not retrieve logs"
    exit 1
  fi
  
  echo -n "."
done

if [ "$BUILD_STATUS" != "ready" ]; then
  echo -e "${RED}Build timeout after ${MAX_WAIT}s${NC}"
  exit 1
fi

echo ""

# Step 4: Create containers
echo -e "${YELLOW}[4/6] Creating containers...${NC}"
CONTAINER_RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/containers/$IMAGE_ID" \
  -b /tmp/test_cookies.txt \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"test-container\", \"image_id\": $IMAGE_ID, \"count\": 1}")

CONTAINER_ID=$(echo "$CONTAINER_RESPONSE" | grep -oE '"id"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1 || echo "")

if [ -z "$CONTAINER_ID" ]; then
  echo -e "${RED}Failed to create containers. Response: $CONTAINER_RESPONSE${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Container created. ID: $CONTAINER_ID${NC}"

# Wait a bit for container to be fully started
echo "Waiting for container to start..."
sleep 5

echo ""

# Step 5: Test routing via API Gateway
echo -e "${YELLOW}[5/6] Testing routing via API Gateway...${NC}"

# Test path-based routing
ROUTE_RESPONSE=$(curl -s -X GET "$API_GATEWAY_URL/apps/$APP_HOSTNAME/" \
  -H "Host: $APP_HOSTNAME")

if echo "$ROUTE_RESPONSE" | grep -q "Hello from Cloud Run-style app"; then
  echo -e "${GREEN}✓ Path-based routing works!${NC}"
else
  echo -e "${RED}Path-based routing failed${NC}"
  echo "Response: $ROUTE_RESPONSE"
  exit 1
fi

# Test nested path
ROUTE_RESPONSE2=$(curl -s -X GET "$API_GATEWAY_URL/apps/$APP_HOSTNAME/test/hello" \
  -H "Host: $APP_HOSTNAME")

if echo "$ROUTE_RESPONSE2" | grep -q "Path-based routing works"; then
  echo -e "${GREEN}✓ Nested path routing works!${NC}"
else
  echo -e "${RED}Nested path routing failed${NC}"
  echo "Response: $ROUTE_RESPONSE2"
  exit 1
fi

echo ""

# Step 6: Cleanup (optional)
echo -e "${YELLOW}[6/6] Cleanup...${NC}"
read -p "Delete test image and containers? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Delete containers
  curl -s -X DELETE "$API_GATEWAY_URL/api/containers/$CONTAINER_ID" \
    -b /tmp/test_cookies.txt > /dev/null
  
  # Delete image
  curl -s -X DELETE "$API_GATEWAY_URL/api/images/$IMAGE_ID" \
    -b /tmp/test_cookies.txt > /dev/null
  
  echo -e "${GREEN}✓ Cleanup completed${NC}"
else
  echo "Skipping cleanup"
fi

# Cleanup temp files
rm -f "$ARCHIVE_PATH" /tmp/test_cookies.txt

echo ""
echo -e "${GREEN}=== All tests passed! ===${NC}"
