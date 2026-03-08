#!/bin/bash
# Verify prediction and forecast features
# Run from project root

set -e
API_BASE="http://localhost:8000"
AUTH_HEADER="Authorization: Bearer dev-token-123"

echo "=========================================="
echo "Prediction & Forecast Verification"
echo "=========================================="
echo ""

# Check if API is running
echo "1. Checking API health..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/health" 2>/dev/null || echo "000")
if [ "$HEALTH" != "200" ]; then
    echo "   ❌ API not running. Start with:"
    echo "      cd $(pwd) && export PYTHONPATH=\${PWD}/apps/api/src:\${PWD}/packages/common/src:\$PYTHONPATH"
    echo "      export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uepi_db"
    echo "      python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi
echo "   ✅ API is running"
echo ""

# Get policies
echo "2. Fetching policies..."
POLICIES=$(curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/policies" 2>/dev/null)
POLICY_IDS=$(echo "$POLICIES" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get('items', [])
    ids = [p.get('id') or p.get('policy_id') for p in items if p.get('id') or p.get('policy_id')]
    print(' '.join(str(i) for i in ids[:5]))
except Exception as e:
    print('', end='')
" 2>/dev/null)

if [ -z "$POLICY_IDS" ]; then
    echo "   ❌ No policies found"
    exit 1
fi
POLICY_ID=$(echo $POLICY_IDS | awk '{print $1}')
echo "   ✅ Found policies. Using policy_id: $POLICY_ID"
echo ""

# Regenerate predicted impact for first policy
echo "3. Regenerating predicted impact for policy $POLICY_ID..."
PRED_RESP=$(curl -s -w "\n%{http_code}" -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    "$API_BASE/api/v1/policies/$POLICY_ID/predicted-impact" 2>/dev/null)
PRED_HTTP=$(echo "$PRED_RESP" | tail -1)
PRED_BODY=$(echo "$PRED_RESP" | sed '$d')

if [ "$PRED_HTTP" != "200" ]; then
    echo "   ⚠️  Predicted impact generation returned $PRED_HTTP"
    echo "   Response: $(echo "$PRED_BODY" | head -c 200)"
else
    # Check for confidence_intervals and ramp_up_projections
    HAS_CI=$(echo "$PRED_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('confidence_intervals') else 'no')" 2>/dev/null || echo "no")
    HAS_RAMP=$(echo "$PRED_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('ramp_up_projections') else 'no')" 2>/dev/null || echo "no")
    echo "   ✅ Predicted impact regenerated"
    echo "      confidence_intervals: $HAS_CI"
    echo "      ramp_up_projections: $HAS_RAMP"
fi
echo ""

# Get analyses
echo "4. Fetching analyses..."
ANALYSES=$(curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/analyses?analysis_type=IMPACT&limit=5" 2>/dev/null)
ANALYSIS_IDS=$(echo "$ANALYSES" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get('items', [])
    ids = [a.get('id') or a.get('analysis_id') for a in items if a.get('id') or a.get('analysis_id')]
    print(' '.join(str(i) for i in ids[:3]))
except: print('')
" 2>/dev/null)

if [ -n "$ANALYSIS_IDS" ]; then
    AID=$(echo $ANALYSIS_IDS | awk '{print $1}')
    echo "   Creating observation from analysis $AID..."
    OBS_RESP=$(curl -s -w "\n%{http_code}" -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" \
        "$API_BASE/api/v1/observations/from-analysis/$AID?policy_id=$POLICY_ID" 2>/dev/null)
    OBS_HTTP=$(echo "$OBS_RESP" | tail -1)
    OBS_BODY=$(echo "$OBS_RESP" | sed '$d')
    
    if [ "$OBS_HTTP" = "200" ] || [ "$OBS_HTTP" = "201" ]; then
        OBS_ID=$(echo "$OBS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('observation_id',''))" 2>/dev/null)
        if [ -n "$OBS_ID" ]; then
            echo "   ✅ Observation created: $OBS_ID"
            # Check vs_predicted for confidence_intervals and ramp_up
            HAS_CI=$(echo "$OBS_BODY" | python3 -c "
import sys,json
d=json.load(sys.stdin)
cp = d.get('comparisons',{}).get('vs_predicted',{})
print('yes' if cp.get('confidence_intervals') else 'no')
" 2>/dev/null || echo "no")
            HAS_RAMP=$(echo "$OBS_BODY" | python3 -c "
import sys,json
d=json.load(sys.stdin)
cp = d.get('comparisons',{}).get('vs_predicted',{})
print('yes' if cp.get('ramp_up_projections') else 'no')
" 2>/dev/null || echo "no")
            echo "      vs_predicted confidence_intervals: $HAS_CI"
            echo "      vs_predicted ramp_up_projections: $HAS_RAMP"
        fi
    else
        echo "   ⚠️  Observation creation returned $OBS_HTTP"
    fi
else
    echo "   ⚠️  No IMPACT analyses found (skipping observation creation)"
fi
echo ""

# Test forecast endpoint
echo "5. Testing forecast endpoint..."
OBSERVATIONS=$(curl -s -H "$AUTH_HEADER" "$API_BASE/api/v1/observations" 2>/dev/null)
OBS_IDS=$(echo "$OBSERVATIONS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get('items', [])
    ids = [o.get('observation_id') or o.get('id') for o in items if o.get('observation_id') or o.get('id')]
    print(' '.join(str(i) for i in ids[:2]))
except: print('')
" 2>/dev/null)

if [ -n "$OBS_IDS" ]; then
    OID=$(echo $OBS_IDS | awk '{print $1}')
    echo "   Testing forecast for observation $OID (utilization)..."
    FC_UTIL=$(curl -s -w "\n%{http_code}" -H "$AUTH_HEADER" \
        "$API_BASE/api/v1/observations/$OID/forecast?policy_id=$POLICY_ID&metric_type=utilization" 2>/dev/null)
    FC_UTIL_HTTP=$(echo "$FC_UTIL" | tail -1)
    
    echo "   Testing forecast for observation $OID (cost)..."
    FC_COST=$(curl -s -w "\n%{http_code}" -H "$AUTH_HEADER" \
        "$API_BASE/api/v1/observations/$OID/forecast?policy_id=$POLICY_ID&metric_type=cost" 2>/dev/null)
    FC_COST_HTTP=$(echo "$FC_COST" | tail -1)
    
    if [ "$FC_UTIL_HTTP" = "200" ] && [ "$FC_COST_HTTP" = "200" ]; then
        echo "   ✅ Forecast endpoint OK (utilization: $FC_UTIL_HTTP, cost: $FC_COST_HTTP)"
        FC_BODY=$(echo "$FC_UTIL" | sed '$d')
        HAS_VALUES=$(echo "$FC_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('forecast_values') else 'no')" 2>/dev/null || echo "no")
        echo "      forecast_values: $HAS_VALUES"
    else
        echo "   ⚠️  Forecast returned util=$FC_UTIL_HTTP cost=$FC_COST_HTTP"
    fi
else
    echo "   ⚠️  No observations found (need at least one for forecast test)"
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
