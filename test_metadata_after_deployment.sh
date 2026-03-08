#!/bin/bash
# Test metadata loading after deployment

set -e

API_URL="https://healthforesight-api-9016.azurewebsites.net"
TEST_POLICY_ID="ST_BIOLOGIC_006"

echo "🔍 Testing Metadata Loading After Deployment"
echo "=============================================="
echo ""

echo "1. Testing Policy Workspace Endpoint..."
WORKSPACE_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/workspace")
echo "$WORKSPACE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"✅ Workspace endpoint returned data\")
    print(f\"   Assumptions: {len(data.get('assumptions', []))}\")
    print(f\"   Guardrails: {len(data.get('guardrails', []))}\")
    print(f\"   Versions: {len(data.get('versions', []))}\")
    if len(data.get('assumptions', [])) > 0:
        print(f\"   ✅ ASSUMPTIONS LOADING!\")
    if len(data.get('guardrails', [])) > 0:
        print(f\"   ✅ GUARDRAILS LOADING!\")
    if len(data.get('versions', [])) > 0:
        print(f\"   ✅ VERSIONS LOADING!\")
except Exception as e:
    print(f\"❌ Error: {e}\")
    print(f\"Response: {sys.stdin.read()[:500]}\")
"

echo ""
echo "2. Testing Individual Policy Endpoint..."
POLICY_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}")
echo "$POLICY_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"✅ Policy endpoint returned data\")
    metadata = data.get('metadata', {})
    print(f\"   Metadata assumptions: {len(metadata.get('assumptions', []))}\")
    print(f\"   Metadata guardrails: {len(metadata.get('guardrails', []))}\")
    print(f\"   Metadata versions: {len(metadata.get('versions', []))}\")
    print(f\"   Root assumptions: {len(data.get('assumptions', []))}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
"

echo ""
echo "3. Testing Versions Endpoint..."
VERSIONS_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/versions")
echo "$VERSIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f\"✅ Versions endpoint returned {len(data)} versions\")
        if len(data) > 0:
            print(f\"   ✅ VERSIONS ENDPOINT WORKING!\")
    else:
        print(f\"⚠️  Versions endpoint returned: {type(data).__name__}\")
        print(f\"   Data: {str(data)[:200]}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
    print(f\"Response: {sys.stdin.read()[:200]}\")
"

echo ""
echo "4. Testing Assumptions Endpoint..."
ASSUMPTIONS_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/assumptions")
echo "$ASSUMPTIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f\"✅ Assumptions endpoint returned {len(data)} assumptions\")
        if len(data) > 0:
            print(f\"   ✅ ASSUMPTIONS ENDPOINT WORKING!\")
    else:
        print(f\"⚠️  Assumptions endpoint returned: {type(data).__name__}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
"

echo ""
echo "5. Testing Guardrails Endpoint..."
GUARDRAILS_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/guardrails")
echo "$GUARDRAILS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f\"✅ Guardrails endpoint returned {len(data)} guardrails\")
        if len(data) > 0:
            print(f\"   ✅ GUARDRAILS ENDPOINT WORKING!\")
    else:
        print(f\"⚠️  Guardrails endpoint returned: {type(data).__name__}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
"

echo ""
echo "=============================================="
echo "Test complete. Check results above."

