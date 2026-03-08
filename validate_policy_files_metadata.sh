#!/bin/bash
# Validate that policy files have metadata before deployment

set -e

echo "🔍 Validating Policy Files Have Metadata"
echo "=========================================="
echo ""

POLICY_FILES=$(find data -name "policy_*.json" -type f | head -10)
TOTAL=0
WITH_METADATA=0
WITH_ASSUMPTIONS=0
WITH_GUARDRAILS=0
WITH_VERSIONS=0

for file in $POLICY_FILES; do
    TOTAL=$((TOTAL + 1))
    echo "Checking: $file"
    
    RESULT=$(python3 -c "
import json
try:
    with open('$file', 'r') as f:
        data = json.load(f)
    has_metadata = 'metadata' in data
    metadata = data.get('metadata', {})
    assumptions = len(metadata.get('assumptions', []))
    guardrails = len(metadata.get('guardrails', []))
    versions = len(metadata.get('versions', []))
    print(f'METADATA:{has_metadata},ASSUMPTIONS:{assumptions},GUARDRAILS:{guardrails},VERSIONS:{versions}')
except Exception as e:
    print(f'ERROR:{e}')
")
    
    if echo "$RESULT" | grep -q "METADATA:True"; then
        WITH_METADATA=$((WITH_METADATA + 1))
    fi
    
    if echo "$RESULT" | grep -q "ASSUMPTIONS:[1-9]"; then
        WITH_ASSUMPTIONS=$((WITH_ASSUMPTIONS + 1))
    fi
    
    if echo "$RESULT" | grep -q "GUARDRAILS:[1-9]"; then
        WITH_GUARDRAILS=$((WITH_GUARDRAILS + 1))
    fi
    
    if echo "$RESULT" | grep -q "VERSIONS:[1-9]"; then
        WITH_VERSIONS=$((WITH_VERSIONS + 1))
    fi
    
    echo "  $RESULT"
    echo ""
done

echo "=========================================="
echo "Summary:"
echo "  Total policy files checked: $TOTAL"
echo "  Files with metadata: $WITH_METADATA"
echo "  Files with assumptions: $WITH_ASSUMPTIONS"
echo "  Files with guardrails: $WITH_GUARDRAILS"
echo "  Files with versions: $WITH_VERSIONS"
echo ""

if [ $WITH_METADATA -eq 0 ]; then
    echo "❌ ERROR: No policy files have metadata!"
    echo "   Policy files must have metadata.assumptions, metadata.guardrails, metadata.versions"
    exit 1
fi

if [ $WITH_ASSUMPTIONS -eq 0 ] || [ $WITH_GUARDRAILS -eq 0 ] || [ $WITH_VERSIONS -eq 0 ]; then
    echo "⚠️  WARNING: Some policy files are missing workspace data"
    echo "   This may cause issues on Azure if metadata isn't properly merged"
else
    echo "✅ All policy files have metadata with workspace data"
fi

