#!/bin/bash
# Test Docker image locally before deploying

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Testing Docker Image Locally ==="
echo ""

cd "$SCRIPT_DIR"

echo "1. Building Docker image..."
docker build -t uepi-api-test -f apps/api/Dockerfile . || {
    echo "   ❌ Docker build failed"
    exit 1
}

echo "   ✅ Docker image built"
echo ""

echo "2. Testing if image runs..."
echo "   (This will start the container, wait 10 seconds, then check if it's running)"
echo ""

docker run -d \
    --name uepi-api-test \
    -p 8001:8000 \
    -e PORT=8000 \
    -e PYTHONPATH=/app/src:/app/packages/common/src \
    uepi-api-test

sleep 10

echo ""
echo "3. Checking container status..."
docker ps | grep uepi-api-test

echo ""
echo "4. Checking container logs..."
docker logs uepi-api-test 2>&1 | tail -30

echo ""
echo "5. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Container is working locally!"
    curl -s http://localhost:8001/health | head -5
else
    echo "   ⚠️  Container returned HTTP $HTTP_CODE"
    echo "   Check logs above for errors"
fi

echo ""
echo "6. Stopping test container..."
docker stop uepi-api-test >/dev/null 2>&1
docker rm uepi-api-test >/dev/null 2>&1

echo ""
echo "=== Test Complete ==="
echo ""
echo "If the container works locally, the issue is with Azure configuration."
echo "If it fails locally, we need to fix the Dockerfile."
