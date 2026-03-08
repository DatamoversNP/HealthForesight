#!/bin/bash
# Restore and verify pipelines are loading correctly

set -e

echo "🔍 Checking Pipeline Status"
echo "==========================="
echo ""

# Check if pipelines exist
PIPELINE_COUNT=$(find data/pipelines -name "pipeline-*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "📁 Pipeline files found: $PIPELINE_COUNT"

# Check index
if [ -f "data/pipelines/index.json" ]; then
    INDEX_COUNT=$(python3 -c "import json; print(len(json.load(open('data/pipelines/index.json'))))" 2>/dev/null || echo "0")
    echo "📋 Index entries: $INDEX_COUNT"
else
    echo "⚠️  Index file not found"
fi

echo ""
echo "🧪 Testing Pipeline Storage..."
echo ""

# Test pipeline loading
python3 << 'PYTHON_SCRIPT'
import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path.cwd() / "apps" / "api" / "src"))
sys.path.insert(0, str(Path.cwd() / "packages" / "common" / "src"))

from uepi_common.storage.file_storage import FileStorage
from uuid import UUID

# Test pipeline storage
pipeline_storage = FileStorage(base_path="data/pipelines", file_prefix="pipeline-")

print("Testing pipeline storage...")
all_pipelines = pipeline_storage.list_all()
print(f"✅ Total pipelines from storage: {len(all_pipelines)}")

# Check tenant_id filtering
tenant_id = UUID("00000000-0000-0000-0000-000000000001")
tenant_id_str = str(tenant_id)
matching = [p for p in all_pipelines if str(p.get('tenant_id', '')) == tenant_id_str]
print(f"✅ Pipelines matching tenant_id: {len(matching)}")

# Show sample
if matching:
    print("\n📋 Sample pipelines:")
    for p in matching[:5]:
        name = p.get('pipeline_name') or p.get('name', 'Unknown')
        pid = p.get('pipeline_id') or p.get('id', 'Unknown')
        active = p.get('active', True)
        print(f"   - {name} (ID: {pid[:8]}..., Active: {active})")
else:
    print("⚠️  No pipelines found matching tenant_id")
    
    # Check what tenant_ids exist
    tenant_ids = set()
    for p in all_pipelines:
        tid = p.get('tenant_id', '')
        if tid:
            tenant_ids.add(tid)
    print(f"\nFound tenant_ids in pipelines: {list(tenant_ids)}")
PYTHON_SCRIPT

echo ""
echo "🌐 Testing API Endpoint..."
echo ""

# Test API
API_RESPONSE=$(curl -s http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" 2>&1)

if echo "$API_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(f'API returned: {len(d)} pipelines')" 2>/dev/null; then
    echo "✅ API is responding"
    PIPELINE_NAMES=$(echo "$API_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; [print(f'   - {p.get(\"pipeline_name\") or p.get(\"name\")}') for p in d[:5]]" 2>/dev/null)
    if [ -n "$PIPELINE_NAMES" ]; then
        echo "$PIPELINE_NAMES"
    else
        echo "⚠️  API returned 0 pipelines"
        echo "   Response: ${API_RESPONSE:0:200}"
    fi
else
    echo "❌ API call failed or returned error"
    echo "   Response: ${API_RESPONSE:0:200}"
fi

echo ""
echo "✅ Pipeline check complete!"
echo ""
echo "💡 If pipelines are found in storage but not in API:"
echo "   1. Restart API server: ./START_API_NOW.sh"
echo "   2. Check API logs for errors"
echo "   3. Verify authentication is working"
