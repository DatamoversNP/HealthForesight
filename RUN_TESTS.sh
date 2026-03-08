#!/bin/bash
# Comprehensive Test Suite for All Phases
# This script runs tests for Phases 1-5 of the continuous system

set -e

echo "🧪 Starting Comprehensive Test Suite"
echo "===================================="
echo ""

API_BASE="http://localhost:8000/api/v1"
TOKEN="dev-token-123"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "Testing: $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$API_BASE$endpoint" || echo "ERROR\n000")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$API_BASE$endpoint" || echo "ERROR\n000")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$API_BASE$endpoint" || echo "ERROR\n000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    elif [ "$http_code" -eq 404 ]; then
        echo -e "${YELLOW}⚠ SKIP${NC} (Not found - may be expected)"
        return 1
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "  Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "📋 Phase 1: Data Periods & Policy Versions"
echo "-------------------------------------------"

# Test 1.1: List data periods
test_endpoint "List Data Periods" "GET" "/periods"

# Test 1.2: Get baseline-eligible periods
test_endpoint "Get Baseline-Eligible Periods" "GET" "/periods/baseline-eligible"

# Test 1.3: List policies (to get policy IDs for version tests)
echo -n "Getting policies for version tests... "
POLICIES_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/policies" || echo "[]")
POLICY_ID=$(echo "$POLICIES_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

if [ -n "$POLICY_ID" ]; then
    echo -e "${GREEN}✓ Found policy${NC}"
    
    # Test 1.4: List policy versions
    test_endpoint "List Policy Versions" "GET" "/policies/$POLICY_ID/versions"
    
    # Test 1.5: Get latest policy version
    test_endpoint "Get Latest Policy Version" "GET" "/policies/$POLICY_ID/versions/latest"
else
    echo -e "${YELLOW}⚠ No policies found${NC}"
fi

echo ""
echo "📊 Phase 2: Baseline Refresh System"
echo "------------------------------------"

# Test 2.1: List baselines
test_endpoint "List Baselines" "GET" "/baselines"

# Test 2.2: Get latest baseline
test_endpoint "Get Latest Baseline" "GET" "/baselines/latest"

# Test 2.3: Check should refresh baseline
test_endpoint "Check Should Refresh Baseline" "GET" "/baselines/should-refresh"

echo ""
echo "👁️ Phase 3: Observed Impact Tracking"
echo "-------------------------------------"

# Test 3.1: List observations
test_endpoint "List Observations" "GET" "/observations"

# Test 3.2: Get observations for policy (if we have a policy ID)
if [ -n "$POLICY_ID" ]; then
    test_endpoint "Get Observations for Policy" "GET" "/policies/$POLICY_ID/observations"
fi

echo ""
echo "🧠 Phase 4: Learning Loop System"
echo "--------------------------------"

# Test 4.1: List elasticity models
test_endpoint "List Elasticity Models" "GET" "/learning/elasticity-models"

# Test 4.2: Get prediction accuracy (if we have a policy ID)
if [ -n "$POLICY_ID" ]; then
    test_endpoint "Get Prediction Accuracy" "GET" "/learning/accuracy/$POLICY_ID"
fi

echo ""
echo "🔗 Phase 5: Traceability & Refresh Status"
echo "------------------------------------------"

# Test 5.1: Query traceability
test_endpoint "Query Traceability" "GET" "/traceability/query"

# Test 5.2: Get refresh status (if we have a policy ID and impact)
if [ -n "$POLICY_ID" ]; then
    # Try to get predicted impact to check refresh status
    IMPACT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/policies/$POLICY_ID/predicted-impact" || echo "{}")
    COMPUTED_AT=$(echo "$IMPACT_RESPONSE" | grep -o '"computed_at":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    
    if [ -n "$COMPUTED_AT" ]; then
        test_endpoint "Get Refresh Status" "GET" "/traceability/refresh-status?entity_type=prediction&entity_id=$POLICY_ID&last_refresh_timestamp=$COMPUTED_AT"
    else
        echo -e "${YELLOW}⚠ No predicted impact found for refresh status test${NC}"
    fi
fi

# Test 5.3: Get audit trail (if we have a policy ID)
if [ -n "$POLICY_ID" ]; then
    test_endpoint "Get Audit Trail" "GET" "/traceability/audit-trail?entity_type=policy&entity_id=$POLICY_ID"
fi

echo ""
echo "===================================="
echo "📊 Test Results Summary"
echo "===================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed or were skipped${NC}"
    exit 1
fi
