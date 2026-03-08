#!/bin/bash
# Fix pipelines: check API, seed pipelines, verify
cd "$(dirname "$0")"

export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"

echo "🔍 Step 1: Checking if API server is running..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ API server is running"
else
    echo "❌ API server is NOT running on port 8000"
    echo "   Please start it with: ./start_api_simple.sh"
    exit 1
fi

echo ""
echo "🔍 Step 2: Checking pipelines in database..."
python3 -c "
from uepi_api.storage_pipelines import list_pipelines
try:
    pipelines = list_pipelines('00000000-0000-0000-0000-000000000001')
    print(f'Found {len(pipelines)} pipelines')
    if len(pipelines) == 0:
        print('⚠️  No pipelines found - need to seed them')
    else:
        print('✅ Pipelines exist')
        for p in pipelines[:3]:
            print(f'   - {p.get(\"pipeline_name\", \"Unknown\")}')
except Exception as e:
    print(f'❌ Error checking pipelines: {e}')
" 2>&1

echo ""
echo "🔍 Step 3: Testing API endpoint..."
curl -s -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/pipelines | head -c 200 && echo "..." || echo "❌ API endpoint failed"

echo ""
echo "✅ Done! If pipelines are missing, run: python3 apps/api/scripts/04_seed_pipelines.py"

