#!/bin/bash
# Comprehensive Validation Script for All API Endpoints and Functionalities
# Tests all pages/functionalities to ensure data is loading correctly

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"
API_URL="https://${API_APP_NAME}.azurewebsites.net"
TEST_POLICY_ID="ST_BIOLOGIC_006"  # Known policy ID for testing

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 Comprehensive API Validation - All Endpoints${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -e "${BLUE}Testing: $name${NC}"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "ERROR")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        if command -v jq &> /dev/null && echo "$BODY" | jq . >/dev/null 2>&1; then
            # Try to extract useful info
            if echo "$BODY" | jq -e '. | length' >/dev/null 2>&1; then
                COUNT=$(echo "$BODY" | jq '. | length' 2>/dev/null || echo "N/A")
                echo -e "  ${GREEN}✅ $name (HTTP $HTTP_CODE, $COUNT items)${NC}"
            elif echo "$BODY" | jq -e '.assumptions' >/dev/null 2>&1; then
                ASSUMPTIONS=$(echo "$BODY" | jq '.assumptions | length' 2>/dev/null || echo "0")
                GUARDRAILS=$(echo "$BODY" | jq '.guardrails | length' 2>/dev/null || echo "0")
                VERSIONS=$(echo "$BODY" | jq '.versions | length' 2>/dev/null || echo "0")
                echo -e "  ${GREEN}✅ $name (HTTP $HTTP_CODE, Assumptions: $ASSUMPTIONS, Guardrails: $GUARDRAILS, Versions: $VERSIONS)${NC}"
            else
                echo -e "  ${GREEN}✅ $name (HTTP $HTTP_CODE)${NC}"
            fi
        else
            echo -e "  ${GREEN}✅ $name (HTTP $HTTP_CODE)${NC}"
        fi
        return 0
    else
        echo -e "  ${RED}❌ $name (HTTP $HTTP_CODE, expected $expected_status)${NC}"
        if [ ${#BODY} -lt 200 ]; then
            echo "    Response: $BODY"
        fi
        return 1
    fi
}

# Track results
PASSED=0
FAILED=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}1. Core API Health${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "API Health" "${API_URL}/health" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}2. Policies Endpoints${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "List All Policies" "${API_URL}/api/v1/policies" && ((PASSED++)) || ((FAILED++))
test_endpoint "Get Policy by ID" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}3. Policy Workspace (Metadata)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Policy Workspace (Assumptions/Guardrails/Versions)" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/workspace" && ((PASSED++)) || ((FAILED++))
test_endpoint "Policy Assumptions" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/assumptions" && ((PASSED++)) || ((FAILED++))
test_endpoint "Policy Guardrails" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/guardrails" && ((PASSED++)) || ((FAILED++))
test_endpoint "Policy Versions" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/versions" && ((PASSED++)) || ((FAILED++))
test_endpoint "Policy Changelog" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/changelog" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}4. Predicted Impact${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Policy Predicted Impact" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/predicted-impact" "404" && ((PASSED++)) || ((FAILED++))
# 404 is OK for predicted impact if not generated
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}5. Decisions${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Policy Decisions" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/decisions" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}6. Risks & Risk Register${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Risk Register for Policy" "${API_URL}/api/v1/risks/policy/${TEST_POLICY_ID}" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}7. Alert Events${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Alert Events for Policy" "${API_URL}/api/v1/alert-events?policy_id=${TEST_POLICY_ID}" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}8. Comments & Activity${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Comments for Policy" "${API_URL}/api/v1/comments?resource_id=${TEST_POLICY_ID}" && ((PASSED++)) || ((FAILED++))
test_endpoint "Activity Events for Policy" "${API_URL}/api/v1/activity?resource_id=${TEST_POLICY_ID}" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}9. Narratives${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Narratives for Policy" "${API_URL}/api/v1/narratives?resource_id=${TEST_POLICY_ID}" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}10. Baselines${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "List Baselines" "${API_URL}/api/v1/baselines" && ((PASSED++)) || ((FAILED++))
test_endpoint "Latest Baseline" "${API_URL}/api/v1/baselines/latest" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}11. Observations${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "List Observations" "${API_URL}/api/v1/observations" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}12. Scenarios (What-If)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "List Scenarios" "${API_URL}/api/v1/scenarios" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}13. Pipelines${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "List Pipelines" "${API_URL}/api/v1/pipelines" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}14. Dashboard${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Executive Dashboard Summary" "${API_URL}/api/v1/dashboard/summary" && ((PASSED++)) || ((FAILED++))
test_endpoint "Policy Performance" "${API_URL}/api/v1/dashboard/policy-performance" && ((PASSED++)) || ((FAILED++))
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}15. Data Quality${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
test_endpoint "Data Quality Dashboard" "${API_URL}/api/v1/data-quality/dashboard" && ((PASSED++)) || ((FAILED++))
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Validation Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✅ Passed: $PASSED${NC}"
echo -e "  ${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All endpoints validated successfully!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some endpoints failed. Check the output above for details.${NC}"
    exit 1
fi

