#!/bin/bash
# Quick status check for pipelines, validation, and API

echo "🔍 Checking System Status"
echo "========================"
echo ""

# 1. API Status
echo "1. API Status:"
if curl -s http://localhost:8000/api/v1/me > /dev/null 2>&1; then
    echo "   ✅ API is running"
else
    echo "   ❌ API is not running (start with ./START_API_NOW.sh)"
fi
echo ""

# 2. Pipelines
echo "2. Pipelines:"
PIPELINES=$(curl -s http://localhost:8000/api/v1/pipelines -H "Authorization: Bearer demo-token" 2>/dev/null || echo "[]")
COUNT=$(echo "$PIPELINES" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(len(d) if isinstance(d, list) else 0)" 2>/dev/null || echo "0")
if [ "$COUNT" -gt 0 ]; then
    echo "   ✅ Found: $COUNT pipeline(s)"
else
    echo "   ⚠️  No pipelines found"
fi
echo ""

# 3. Data Quality Validation
echo "3. Data Quality Validation:"
STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/data-quality/validate/status -H "Authorization: Bearer demo-token" 2>/dev/null || echo "{}")
STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else {}; print(d.get('status', 'not_started'))" 2>/dev/null || echo "unknown")
case "$STATUS" in
    "not_started")
        echo "   ⚠️  Not started yet"
        ;;
    "running")
        echo "   🔄 Running (check dashboard for progress)"
        ;;
    "completed")
        echo "   ✅ Completed (refresh dashboard to see results)"
        ;;
    "error")
        ERROR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else {}; print(d.get('error', 'Unknown error'))" 2>/dev/null || echo "Unknown")
        echo "   ❌ Error: $ERROR"
        ;;
    *)
        echo "   ⚠️  Status: $STATUS"
        ;;
esac
echo ""

# 4. Data Files
echo "4. Data Files:"
if [ -d "apps/api/data/target_data_model" ]; then
    FILE_COUNT=$(find apps/api/data/target_data_model -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$FILE_COUNT" -gt 0 ]; then
        echo "   ✅ Found: $FILE_COUNT CSV file(s)"
    else
        echo "   ⚠️  No CSV files found"
    fi
else
    echo "   ⚠️  Data directory not found"
fi
echo ""

echo "✅ Status check complete!"
echo ""
echo "💡 Next steps:"
echo "   - Run pipelines: ./RUN_ALL_PIPELINES.sh"
echo "   - Run validation: Go to Data Quality Dashboard and click 'Run Validation'"
echo "   - Check results: Refresh Data Quality Dashboard"
