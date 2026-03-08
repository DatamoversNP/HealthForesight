#!/bin/bash
# Run all existing pipelines

set -e

echo "🚀 Running All Pipelines"
echo "=========================="

# Get API base URL
API_URL="${API_URL:-http://localhost:8000}"
TENANT_ID="00000000-0000-0000-0000-000000000001"

echo "📋 Fetching all pipelines..."
PIPELINES=$(curl -s "${API_URL}/api/v1/pipelines" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" 2>/dev/null || echo "[]")

if [ "$PIPELINES" = "[]" ] || [ -z "$PIPELINES" ]; then
  echo "⚠️  No pipelines found"
  exit 0
fi

# Count pipelines
PIPELINE_COUNT=$(echo "$PIPELINES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 0)" 2>/dev/null || echo "0")

echo "✅ Found $PIPELINE_COUNT pipeline(s)"
echo ""

# Extract pipeline IDs and run them
echo "$PIPELINES" | python3 << 'PYTHON_SCRIPT'
import sys
import json
import subprocess
import time

try:
    pipelines = json.load(sys.stdin)
    if not isinstance(pipelines, list):
        pipelines = []
    
    if not pipelines:
        print("No pipelines to run")
        sys.exit(0)
    
    api_url = "http://localhost:8000"
    success_count = 0
    error_count = 0
    
    for pipeline in pipelines:
        pipeline_id = pipeline.get("id") or pipeline.get("pipeline_id")
        pipeline_name = pipeline.get("name") or pipeline.get("pipeline_type", "Unknown")
        
        if not pipeline_id:
            print(f"⚠️  Skipping pipeline without ID: {pipeline_name}")
            continue
        
        print(f"🔄 Running pipeline: {pipeline_name} (ID: {pipeline_id})")
        
        # Run pipeline via API
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    f"{api_url}/api/v1/pipelines/{pipeline_id}/run",
                    "-H", "Authorization: Bearer demo-token",
                    "-H", "Content-Type: application/json"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout) if result.stdout else {}
                if response.get("status") in ["PROCESSING", "PENDING", "COMPLETED"]:
                    print(f"   ✅ Started successfully (Status: {response.get('status')})")
                    success_count += 1
                else:
                    print(f"   ⚠️  Response: {result.stdout[:200]}")
                    error_count += 1
            else:
                print(f"   ❌ Failed: {result.stderr[:200]}")
                error_count += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:200]}")
            error_count += 1
        
        # Small delay between runs
        time.sleep(1)
    
    print("")
    print("📊 Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {error_count}")
    print(f"   📦 Total: {len(pipelines)}")
    
except Exception as e:
    print(f"Error processing pipelines: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ Pipeline execution complete!"
echo ""
echo "💡 Check pipeline status at: http://localhost:3050/pipelines"
