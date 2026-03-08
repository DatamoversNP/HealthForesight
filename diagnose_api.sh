#!/bin/bash
# Diagnose why API isn't finding policy files

echo "🔍 API Storage Path Diagnosis"
echo "=============================="
echo ""

# Check where API is looking
echo "1. Checking STORAGE_PATH..."
if [ -n "$STORAGE_PATH" ]; then
    echo "   STORAGE_PATH: $STORAGE_PATH"
    echo "   Exists: $([ -d "$STORAGE_PATH" ] && echo "YES" || echo "NO")"
else
    echo "   STORAGE_PATH: NOT SET"
fi
echo ""

# Check policy files
echo "2. Policy files in data/:"
POLICY_FILES=$(find data -name "policy_*.json" -not -name "valid_policies.json" 2>/dev/null | wc -l | tr -d ' ')
echo "   Found: $POLICY_FILES files"
echo ""

# Test API response
echo "3. Testing API response..."
if curl -s http://localhost:8000/api/v1/policies > /dev/null 2>&1; then
    POLICY_COUNT=$(curl -s http://localhost:8000/api/v1/policies | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(len(d) if isinstance(d, list) else len(d.get('items', [])) if isinstance(d, dict) else 0)" 2>/dev/null || echo "0")
    echo "   API returns: $POLICY_COUNT policies"
    
    if [ "$POLICY_COUNT" = "0" ]; then
        echo ""
        echo "❌ PROBLEM: API is running but not finding policy files!"
        echo ""
        echo "Solution: Restart API with STORAGE_PATH set:"
        echo "  export STORAGE_PATH=\"$(pwd)/data\""
        echo "  ./start_api_local.sh"
    fi
else
    echo "   API is not running"
fi
echo ""

# Check project root calculation
echo "4. Project root calculation test:"
cd apps/api/src
python3 << 'PYEOF'
from pathlib import Path
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
print(f"   Calculated project root: {_PROJECT_ROOT}")
print(f"   Data dir would be: {_PROJECT_ROOT / 'data'}")
print(f"   Data dir exists: {(_PROJECT_ROOT / 'data').exists()}")
print(f"   Policy file exists: {(_PROJECT_ROOT / 'data' / 'policy_ST_BIOLOGIC_006.json').exists()}")
PYEOF
cd ../../..

