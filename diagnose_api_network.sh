#!/bin/bash
# Diagnose API network errors and data loading issues

echo "═══════════════════════════════════════════════════════════════"
echo "🔍 API Network & Data Loading Diagnostics"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if API is running
echo "1️⃣ Checking if API is running..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   ✅ API is running on port 8000"
    API_PID=$(lsof -ti:8000 | head -1)
    echo "   Process ID: $API_PID"
else
    echo "   ❌ API is NOT running on port 8000"
    echo "   💡 Start it with: ./start_api_local.sh"
    exit 1
fi

echo ""

# Check API health endpoint
echo "2️⃣ Testing API health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/health 2>&1)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Health check passed (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
else
    echo "   ❌ Health check failed (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
fi

echo ""

# Check API policies endpoint
echo "3️⃣ Testing API policies endpoint..."
POLICIES_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/policies 2>&1)
POLICIES_HTTP_CODE=$(echo "$POLICIES_RESPONSE" | tail -1)
POLICIES_BODY=$(echo "$POLICIES_RESPONSE" | head -n -1)

if [ "$POLICIES_HTTP_CODE" = "200" ]; then
    echo "   ✅ Policies endpoint working (HTTP $POLICIES_HTTP_CODE)"
    # Count policies
    POLICY_COUNT=$(echo "$POLICIES_BODY" | grep -o '"policy_id"' | wc -l | tr -d ' ')
    echo "   Found $POLICY_COUNT policies"
else
    echo "   ❌ Policies endpoint failed (HTTP $POLICIES_HTTP_CODE)"
    echo "   Response: $POLICIES_BODY"
fi

echo ""

# Check logs for errors
echo "4️⃣ Checking recent API errors..."
if [ -f "logs/errors.log" ]; then
    ERROR_COUNT=$(tail -100 logs/errors.log 2>/dev/null | wc -l | tr -d ' ')
    echo "   Found $ERROR_COUNT recent log entries in errors.log"
    echo "   Recent errors:"
    tail -5 logs/errors.log 2>/dev/null | head -3 || echo "   (No recent errors)"
else
    echo "   ⚠️  No errors.log file found (API may not have logging enabled)"
fi

echo ""

# Check API logs
echo "5️⃣ Checking API logs..."
if [ -f "logs/api.log" ]; then
    echo "   ✅ api.log exists"
    RECENT_LOGS=$(tail -10 logs/api.log 2>/dev/null | wc -l | tr -d ' ')
    echo "   Recent log entries: $RECENT_LOGS"
else
    echo "   ⚠️  No api.log file found"
    echo "   💡 Restart API to enable logging: ./start_api_local.sh"
fi

echo ""

# Check STORAGE_PATH
echo "6️⃣ Checking data storage configuration..."
if [ -n "$STORAGE_PATH" ]; then
    echo "   ✅ STORAGE_PATH is set: $STORAGE_PATH"
    if [ -d "$STORAGE_PATH" ]; then
        echo "   ✅ Data directory exists"
        POLICY_FILES=$(find "$STORAGE_PATH" -name "*.json" -path "*/policies/*" 2>/dev/null | wc -l | tr -d ' ')
        echo "   Found $POLICY_FILES policy JSON files"
    else
        echo "   ❌ Data directory does not exist: $STORAGE_PATH"
    fi
else
    echo "   ⚠️  STORAGE_PATH is not set"
    echo "   💡 Set it to: export STORAGE_PATH=\"$PWD/data\""
fi

echo ""

# Check web server
echo "7️⃣ Checking web server..."
if lsof -ti:3050 > /dev/null 2>&1; then
    echo "   ✅ Web server is running on port 3050"
else
    echo "   ❌ Web server is NOT running on port 3050"
    echo "   💡 Start it with: ./START_WEB_SERVER.sh"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Summary
if lsof -ti:8000 > /dev/null 2>&1 && [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API Status: Running and healthy"
else
    echo "❌ API Status: Not running or unhealthy"
fi

if [ "$POLICIES_HTTP_CODE" = "200" ]; then
    echo "✅ Data Loading: Policies endpoint working"
else
    echo "❌ Data Loading: Policies endpoint failing"
fi

if lsof -ti:3050 > /dev/null 2>&1; then
    echo "✅ Web Server: Running"
else
    echo "❌ Web Server: Not running"
fi

echo ""
echo "💡 Next Steps:"
if ! lsof -ti:8000 > /dev/null 2>&1; then
    echo "   1. Start API: ./start_api_local.sh"
fi
if ! lsof -ti:3050 > /dev/null 2>&1; then
    echo "   2. Start Web: ./START_WEB_SERVER.sh"
fi
if [ "$POLICIES_HTTP_CODE" != "200" ]; then
    echo "   3. Check API logs: tail -f logs/api.log"
    echo "   4. Check errors: tail -f logs/errors.log"
fi

echo ""

