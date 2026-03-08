#!/bin/bash
# API Endpoint Test Script
# Run this after starting the API server

echo "=========================================="
echo "API Endpoint Test Suite"
echo "=========================================="
echo ""

API_BASE="http://localhost:8000"
AUTH_HEADER="Authorization: Bearer dev-token-123"

echo "1. Testing Health Endpoint..."
curl -s "$API_BASE/health" | python3 -m json.tool 2>/dev/null || curl -s "$API_BASE/health"
echo ""
echo ""

echo "2. Testing Auth Endpoint (/api/v1/auth/me)..."
curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/auth/me" | python3 -m json.tool 2>/dev/null || curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/auth/me"
echo ""
echo ""

echo "3. Testing Access Roles Endpoint..."
curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/access/users/00000000-0000-0000-0000-000000000001/roles" | python3 -m json.tool 2>/dev/null || curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/access/users/00000000-0000-0000-0000-000000000001/roles"
echo ""
echo ""

echo "4. Testing Policies Endpoint..."
POLICIES_RESPONSE=$(curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/policies")
echo "$POLICIES_RESPONSE" | python3 -m json.tool 2>/dev/null | head -50 || echo "$POLICIES_RESPONSE" | head -200
POLICY_COUNT=$(echo "$POLICIES_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 'N/A')" 2>/dev/null || echo "N/A")
echo ""
echo "Policies found: $POLICY_COUNT"
echo ""

echo "5. Testing Dashboard Summary..."
curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/dashboard/summary" | python3 -m json.tool 2>/dev/null | head -40 || curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/dashboard/summary" | head -200
echo ""
echo ""

echo "6. Testing Policy Performance..."
curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/dashboard/policy-performance?limit=5" | python3 -m json.tool 2>/dev/null | head -30 || curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/dashboard/policy-performance?limit=5" | head -200
echo ""
echo ""

echo "7. Testing Observations..."
curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/observations" | python3 -m json.tool 2>/dev/null | head -30 || curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/observations" | head -200
echo ""
echo ""

echo "8. Testing Baseline Analyses..."
curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/analyses?analysis_type=BASELINE&limit=5" | python3 -m json.tool 2>/dev/null | head -30 || curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/analyses?analysis_type=BASELINE&limit=5" | head -200
echo ""
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
