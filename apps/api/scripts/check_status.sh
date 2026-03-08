#!/bin/bash
# Quick status check - shows analysis status and monitor status

echo "=== Analysis & Observation Status ==="
echo ""

# Check monitor status
PID_FILE="/tmp/observation_monitor.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Observation Monitor: RUNNING (PID: $PID)"
        echo "   Log: tail -f /tmp/observation_monitor.log"
    else
        echo "⚠️  Observation Monitor: NOT RUNNING (stale PID file)"
    fi
else
    echo "⚠️  Observation Monitor: NOT RUNNING"
    echo "   Start it: ./start_observation_monitor.sh"
fi

echo ""

# Check analysis status via API
echo "📊 Analysis Status:"
python3 << 'EOF'
import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123"}

try:
    response = requests.get(f"{API_BASE_URL}/analyses", headers=HEADERS, params={"analysis_type": "IMPACT"}, timeout=10)
    if response.status_code == 200:
        analyses = response.json()
        status_counts = {}
        for a in analyses:
            status = a.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            print(f"   {status}: {count}")
        
        completed = [a for a in analyses if a.get("status") == "COMPLETED"]
        if completed:
            print(f"\n✅ {len(completed)} completed analyses ready for observations!")
        else:
            print(f"\n⏳ No completed analyses yet - waiting for worker to process...")
    else:
        print(f"   ⚠️  API error: {response.status_code}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")
EOF

echo ""
echo "=== Quick Commands ==="
echo "  Check monitor log: tail -f /tmp/observation_monitor.log"
echo "  Stop monitor: ./stop_observation_monitor.sh"
echo "  Start monitor: ./start_observation_monitor.sh"
echo "  Manual check: python3 scripts/check_and_create_observations.py"
