#!/bin/bash
# Fix pipelines not loading and verify they appear

set -e

echo "🔧 Fixing Pipeline Loading Issue"
echo "================================"
echo ""

# Step 1: Verify pipelines exist
echo "1️⃣  Checking pipeline files..."
PIPELINE_COUNT=$(find data/pipelines -name "pipeline-*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Found $PIPELINE_COUNT pipeline files"
echo ""

# Step 2: Test storage directly
echo "2️⃣  Testing storage loading..."
python3 << 'PYTHON_SCRIPT'
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "apps" / "api" / "src"))
sys.path.insert(0, str(Path.cwd() / "packages" / "common" / "src"))

from uepi_common.storage.file_storage import FileStorage
from uuid import UUID

pipeline_storage = FileStorage(base_path="data/pipelines", file_prefix="pipeline-")
all_pipelines = pipeline_storage.list_all()
tenant_id = UUID("00000000-0000-0000-0000-000000000001")
matching = [p for p in all_pipelines if str(p.get('tenant_id', '')) == str(tenant_id)]

print(f"   ✅ Storage finds {len(matching)} pipelines")
if matching:
    print(f"   📋 Sample: {matching[0].get('pipeline_name') or matching[0].get('name')}")
PYTHON_SCRIPT

echo ""

# Step 3: Check API
echo "3️⃣  Checking API endpoint..."
API_RESPONSE=$(curl -s http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" 2>&1)

API_COUNT=$(echo "$API_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(len(d))" 2>/dev/null || echo "0")

if [ "$API_COUNT" -gt 0 ]; then
    echo "   ✅ API returns $API_COUNT pipelines"
    echo ""
    echo "✅ Pipelines are loading correctly!"
    echo ""
    echo "💡 If UI still shows 0, try:"
    echo "   1. Refresh the browser page (F5 or Cmd+R)"
    echo "   2. Clear browser cache"
    echo "   3. Check browser console for errors"
else
    echo "   ❌ API returns 0 pipelines"
    echo ""
    echo "🔧 Solution: Restart API Server"
    echo ""
    echo "Steps:"
    echo "   1. Stop current API server:"
    echo "      - Find terminal running API"
    echo "      - Press CTRL+C"
    echo ""
    echo "   2. Restart API server:"
    echo "      ./START_API_NOW.sh"
    echo ""
    echo "   3. Wait for server to start (look for 'Uvicorn running')"
    echo ""
    echo "   4. Run this script again to verify:"
    echo "      ./FIX_AND_VERIFY_PIPELINES.sh"
    echo ""
    echo "   5. Refresh browser page to see pipelines"
fi

echo ""
