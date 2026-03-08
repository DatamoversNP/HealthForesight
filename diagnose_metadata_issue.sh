#!/bin/bash
# Diagnose why policy metadata (assumptions, guardrails, versions) is not loading on Azure

set -e

API_URL="https://healthforesight-api-9016.azurewebsites.net"
TEST_POLICY_ID="ST_BIOLOGIC_006"

echo "🔍 Diagnosing Policy Metadata Issue"
echo "===================================="
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
    print(f\"   Has metadata in response: {'metadata' in data}\")
    if 'metadata' in data:
        metadata = data['metadata']
        print(f\"   Metadata assumptions: {len(metadata.get('assumptions', []))}\")
        print(f\"   Metadata guardrails: {len(metadata.get('guardrails', []))}\")
        print(f\"   Metadata versions: {len(metadata.get('versions', []))}\")
except Exception as e:
    print(f\"❌ Error parsing response: {e}\")
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
    print(f\"   Policy ID: {data.get('policy_id', 'N/A')}\")
    print(f\"   Has metadata: {'metadata' in data}\")
    if 'metadata' in data:
        metadata = data['metadata']
        print(f\"   Metadata keys: {list(metadata.keys())}\")
        print(f\"   Metadata assumptions: {len(metadata.get('assumptions', []))}\")
        print(f\"   Metadata guardrails: {len(metadata.get('guardrails', []))}\")
        print(f\"   Metadata versions: {len(metadata.get('versions', []))}\")
    print(f\"   Root level assumptions: {len(data.get('assumptions', []))}\")
    print(f\"   Root level guardrails: {len(data.get('guardrails', []))}\")
    print(f\"   Root level versions: {len(data.get('versions', []))}\")
except Exception as e:
    print(f\"❌ Error parsing response: {e}\")
"

echo ""
echo "3. Testing Individual Assumptions Endpoint..."
ASSUMPTIONS_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/assumptions")
echo "$ASSUMPTIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f\"✅ Assumptions endpoint returned {len(data)} assumptions\")
    else:
        print(f\"⚠️  Assumptions endpoint returned: {type(data)}\")
        print(f\"   Data: {str(data)[:200]}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
    print(f\"Response: {sys.stdin.read()[:200]}\")
"

echo ""
echo "4. Testing Individual Guardrails Endpoint..."
GUARDRAILS_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/guardrails")
echo "$GUARDRAILS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f\"✅ Guardrails endpoint returned {len(data)} guardrails\")
    else:
        print(f\"⚠️  Guardrails endpoint returned: {type(data)}\")
        print(f\"   Data: {str(data)[:200]}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
    print(f\"Response: {sys.stdin.read()[:200]}\")
"

echo ""
echo "5. Testing Individual Versions Endpoint..."
VERSIONS_RESPONSE=$(curl -s "${API_URL}/api/v1/policies/${TEST_POLICY_ID}/versions")
echo "$VERSIONS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f\"✅ Versions endpoint returned {len(data)} versions\")
    else:
        print(f\"⚠️  Versions endpoint returned: {type(data)}\")
        print(f\"   Data: {str(data)[:200]}\")
except Exception as e:
    print(f\"❌ Error: {e}\")
    print(f\"Response: {sys.stdin.read()[:200]}\")
"

echo ""
echo "===================================="
echo "Diagnosis complete. Check output above."

