#!/bin/bash
# Verify Azure Deployment - Alternative to SSH
# Uses Azure CLI and API endpoints to verify data is deployed

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

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 Verifying Azure Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check 1: API Health
echo -e "${BLUE}Step 1: Checking API Health...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/health" 2>/dev/null || echo "ERROR")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "  ${GREEN}✅ API is healthy${NC}"
    echo "  Response: $BODY"
else
    echo -e "  ${RED}❌ API health check failed: HTTP $HTTP_CODE${NC}"
    echo "  Response: $BODY"
fi
echo ""

# Check 2: STORAGE_PATH environment variable
echo -e "${BLUE}Step 2: Checking STORAGE_PATH environment variable...${NC}"
STORAGE_PATH=$(az webapp config appsettings list \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --query "[?name=='STORAGE_PATH'].value" -o tsv 2>/dev/null || echo "")

if [ -n "$STORAGE_PATH" ]; then
    echo -e "  ${GREEN}✅ STORAGE_PATH is set: $STORAGE_PATH${NC}"
else
    echo -e "  ${YELLOW}⚠️  STORAGE_PATH not found in app settings${NC}"
    echo "  This may cause the API to not find data files"
fi
echo ""

# Check 3: Policies endpoint
echo -e "${BLUE}Step 3: Checking Policies endpoint...${NC}"
POLICIES_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/policies" 2>/dev/null || echo "ERROR")
POLICIES_HTTP_CODE=$(echo "$POLICIES_RESPONSE" | tail -n 1)
POLICIES_BODY=$(echo "$POLICIES_RESPONSE" | sed '$d')

if [ "$POLICIES_HTTP_CODE" = "200" ]; then
    # Try to count policies (if jq is available)
    if command -v jq &> /dev/null; then
        POLICY_COUNT=$(echo "$POLICIES_BODY" | jq '. | length' 2>/dev/null || echo "unknown")
        echo -e "  ${GREEN}✅ Policies endpoint working${NC}"
        echo "  Number of policies: $POLICY_COUNT"
    else
        echo -e "  ${GREEN}✅ Policies endpoint working${NC}"
        echo "  Response length: $(echo "$POLICIES_BODY" | wc -c) bytes"
    fi
else
    echo -e "  ${RED}❌ Policies endpoint failed: HTTP $POLICIES_HTTP_CODE${NC}"
    echo "  Response: $(echo "$POLICIES_BODY" | head -c 200)"
fi
echo ""

# Check 4: Policy Workspace (assumptions, guardrails, versions)
echo -e "${BLUE}Step 4: Checking Policy Workspace endpoint...${NC}"
# Try with a known policy ID
TEST_POLICY_ID="ST_BIOLOGIC_006"
WORKSPACE_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/workspace" 2>/dev/null || echo "ERROR")
WORKSPACE_HTTP_CODE=$(echo "$WORKSPACE_RESPONSE" | tail -n 1)
WORKSPACE_BODY=$(echo "$WORKSPACE_RESPONSE" | sed '$d')

if [ "$WORKSPACE_HTTP_CODE" = "200" ]; then
    if command -v jq &> /dev/null; then
        ASSUMPTIONS_COUNT=$(echo "$WORKSPACE_BODY" | jq '.assumptions | length' 2>/dev/null || echo "0")
        GUARDRAILS_COUNT=$(echo "$WORKSPACE_BODY" | jq '.guardrails | length' 2>/dev/null || echo "0")
        VERSIONS_COUNT=$(echo "$WORKSPACE_BODY" | jq '.versions | length' 2>/dev/null || echo "0")
        echo -e "  ${GREEN}✅ Policy workspace endpoint working${NC}"
        echo "  Policy: $TEST_POLICY_ID"
        echo "  Assumptions: $ASSUMPTIONS_COUNT"
        echo "  Guardrails: $GUARDRAILS_COUNT"
        echo "  Versions: $VERSIONS_COUNT"
    else
        echo -e "  ${GREEN}✅ Policy workspace endpoint working${NC}"
        echo "  Response length: $(echo "$WORKSPACE_BODY" | wc -c) bytes"
    fi
else
    echo -e "  ${YELLOW}⚠️  Policy workspace endpoint: HTTP $WORKSPACE_HTTP_CODE${NC}"
    if [ "$WORKSPACE_HTTP_CODE" = "404" ]; then
        echo "  Policy '$TEST_POLICY_ID' not found (this is OK if policy doesn't exist)"
    else
        echo "  Response: $(echo "$WORKSPACE_BODY" | head -c 200)"
    fi
fi
echo ""

# Check 5: Predicted Impact endpoint
echo -e "${BLUE}Step 5: Checking Predicted Impact endpoint...${NC}"
PREDICTED_IMPACT_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/predicted-impact" 2>/dev/null || echo "ERROR")
PREDICTED_IMPACT_HTTP_CODE=$(echo "$PREDICTED_IMPACT_RESPONSE" | tail -n 1)
PREDICTED_IMPACT_BODY=$(echo "$PREDICTED_IMPACT_RESPONSE" | sed '$d')

if [ "$PREDICTED_IMPACT_HTTP_CODE" = "200" ]; then
    echo -e "  ${GREEN}✅ Predicted impact endpoint working${NC}"
    if command -v jq &> /dev/null; then
        echo "  Response preview: $(echo "$PREDICTED_IMPACT_BODY" | jq -c 'keys' 2>/dev/null || echo "valid JSON")"
    fi
elif [ "$PREDICTED_IMPACT_HTTP_CODE" = "404" ]; then
    echo -e "  ${YELLOW}⚠️  Predicted impact not found (404)${NC}"
    echo "  This is expected if predicted impact hasn't been generated for this policy"
else
    echo -e "  ${RED}❌ Predicted impact endpoint error: HTTP $PREDICTED_IMPACT_HTTP_CODE${NC}"
    echo "  Response: $(echo "$PREDICTED_IMPACT_BODY" | head -c 200)"
fi
echo ""

# Check 6: Recent deployment logs
echo -e "${BLUE}Step 6: Checking recent deployment logs...${NC}"
echo "  Fetching last 20 log lines..."
az webapp log tail \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --output none 2>&1 | head -20 || {
    echo -e "  ${YELLOW}⚠️  Could not fetch logs (this is OK)${NC}"
}
echo ""

# Check 7: Kudu Console URL (alternative to SSH)
echo -e "${BLUE}Step 7: Alternative ways to access files...${NC}"
KUDU_URL="https://${API_APP_NAME}.scm.azurewebsites.net"
echo "  Kudu Console (file browser): ${KUDU_URL}"
echo "  Navigate to: Debug Console > CMD > site > wwwroot > data"
echo "  This allows you to browse files without SSH"
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Verification Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "To verify data files are deployed:"
echo "  1. Visit Kudu Console: ${KUDU_URL}"
echo "  2. Navigate to: Debug Console > CMD"
echo "  3. Run: ls -la /home/site/wwwroot/data/"
echo "  4. Check for: policies/, predicted_impacts/, baselines/, etc."
echo ""
echo "To check API logs for file access errors:"
echo "  az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
echo ""

