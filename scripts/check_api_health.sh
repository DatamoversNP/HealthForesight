#!/bin/bash
# Script to check API server health and diagnose timeout issues

echo "=== API Health Check ==="
echo ""

# Check if API server is running
echo "1. Checking if API server is running on port 8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ✅ API server is running on port 8000"
else
    echo "   ❌ API server is NOT running on port 8000"
    echo "   → Start the API server with: cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

# Check basic health endpoint
echo ""
echo "2. Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s -m 5 http://localhost:8000/health 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ Health endpoint responding: $HEALTH_RESPONSE"
else
    echo "   ❌ Health endpoint not responding: $HEALTH_RESPONSE"
    exit 1
fi

# Check database connection
echo ""
echo "3. Testing database connection via API..."
DB_RESPONSE=$(curl -s -m 10 http://localhost:8000/api/v1/health/detailed 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ Database health check: $DB_RESPONSE"
else
    echo "   ❌ Database health check failed: $DB_RESPONSE"
    echo "   → Check DATABASE_URL in .env file"
fi

# Check auth endpoint
echo ""
echo "4. Testing /auth/me endpoint..."
AUTH_RESPONSE=$(curl -s -m 10 -H "Authorization: Bearer demo-token" http://localhost:8000/api/v1/auth/me 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ Auth endpoint responding"
    echo "   Response: $(echo $AUTH_RESPONSE | head -c 200)"
else
    echo "   ❌ Auth endpoint not responding: $AUTH_RESPONSE"
fi

# Check policies endpoint
echo ""
echo "5. Testing /policies endpoint..."
POLICIES_RESPONSE=$(curl -s -m 10 -H "Authorization: Bearer demo-token" http://localhost:8000/api/v1/policies 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ Policies endpoint responding"
    POLICY_COUNT=$(echo $POLICIES_RESPONSE | grep -o '"id"' | wc -l)
    echo "   Found $POLICY_COUNT policies"
else
    echo "   ❌ Policies endpoint not responding: $POLICIES_RESPONSE"
fi

echo ""
echo "=== Health Check Complete ==="
