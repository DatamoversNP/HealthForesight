#!/bin/bash
# Test API endpoints locally before deployment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8000}"
POLICY_ID="${POLICY_ID:-ST_BIOLOGIC_006}"

echo -e "${BLUE}🧪 Testing API Endpoints${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "API URL: $API_URL"
echo "Test Policy ID: $POLICY_ID"
echo ""

# Check if API is running
echo -e "${BLUE}1️⃣  Checking if API is running...${NC}"
if curl -s -f "$API_URL/health" > /dev/null 2>&1 || curl -s -f "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ API is running${NC}"
else
    echo -e "   ${RED}❌ API is not running${NC}"
    echo -e "   ${YELLOW}💡 Start the API with:${NC}"
    echo -e "      cd apps/api && python3 -m uvicorn uepi_api.main:app --reload --port 8000"
    exit 1
fi

echo ""
echo -e "${BLUE}2️⃣  Testing Policy Workspace Endpoint${NC}"
echo "   GET /api/v1/policies/$POLICY_ID/workspace"
echo ""

WORKSPACE_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/policies/$POLICY_ID/workspace" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$WORKSPACE_RESPONSE" | tail -n1)
BODY=$(echo "$WORKSPACE_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Status: $HTTP_CODE${NC}"
    
    # Parse response
    ASSUMPTIONS=$(echo "$BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('assumptions', [])))" 2>/dev/null || echo "0")
    GUARDRAILS=$(echo "$BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('guardrails', [])))" 2>/dev/null || echo "0")
    VERSIONS=$(echo "$BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('versions', [])))" 2>/dev/null || echo "0")
    CHANGELOG=$(echo "$BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('changelog', [])))" 2>/dev/null || echo "0")
    
    echo -e "   ${GREEN}✅ Assumptions: $ASSUMPTIONS${NC}"
    echo -e "   ${GREEN}✅ Guardrails: $GUARDRAILS${NC}"
    echo -e "   ${GREEN}✅ Versions: $VERSIONS${NC}"
    echo -e "   ${GREEN}✅ Changelog: $CHANGELOG${NC}"
    
    if [ "$ASSUMPTIONS" = "0" ] && [ "$GUARDRAILS" = "0" ] && [ "$VERSIONS" = "0" ]; then
        echo -e "   ${YELLOW}⚠️  Warning: No workspace data found${NC}"
    fi
    
    echo ""
    echo "   Response preview:"
    echo "$BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps({'policy_id': d.get('policy', {}).get('policy_id'), 'assumptions': len(d.get('assumptions', [])), 'guardrails': len(d.get('guardrails', [])), 'versions': len(d.get('versions', []))}, indent=2))" 2>/dev/null || echo "   (Could not parse response)"
else
    echo -e "   ${RED}❌ Status: $HTTP_CODE${NC}"
    echo "   Response:"
    echo "$BODY" | head -20
fi

echo ""
echo -e "${BLUE}3️⃣  Testing Policy List Endpoint${NC}"
echo "   GET /api/v1/policies"
echo ""

POLICIES_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/policies" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$POLICIES_RESPONSE" | tail -n1)
BODY=$(echo "$POLICIES_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Status: $HTTP_CODE${NC}"
    POLICY_COUNT=$(echo "$BODY" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(len(d) if isinstance(d, list) else len(d.get('items', [])) if isinstance(d, dict) else 0)" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}✅ Policies found: $POLICY_COUNT${NC}"
else
    echo -e "   ${RED}❌ Status: $HTTP_CODE${NC}"
fi

echo ""
echo -e "${BLUE}4️⃣  Testing Predicted Impact Endpoint${NC}"
echo "   GET /api/v1/policies/$POLICY_ID/predicted-impact"
echo ""

IMPACT_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/policies/$POLICY_ID/predicted-impact" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$IMPACT_RESPONSE" | tail -n1)
BODY=$(echo "$IMPACT_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ Status: $HTTP_CODE${NC}"
    if [ -n "$BODY" ] && [ "$BODY" != "{}" ]; then
        echo -e "   ${GREEN}✅ Predicted impact data found${NC}"
    else
        echo -e "   ${YELLOW}⚠️  No predicted impact data (empty response)${NC}"
    fi
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "   ${YELLOW}⚠️  Status: $HTTP_CODE (No predicted impact - this is OK)${NC}"
else
    echo -e "   ${RED}❌ Status: $HTTP_CODE${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ API Testing Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "If all tests passed, you can proceed with deployment:"
echo "  ./START_PRODUCTION_BUILD.sh"

