# Manual Testing Instructions

## Prerequisites

1. **API Server Running**:
   ```bash
   cd apps/api/src
   export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Database Running**:
   - PostgreSQL should be running on localhost:5432
   - Database: `uepi_db`
   - User: `postgres`
   - Password: `postgres`

3. **Frontend Running** (optional):
   ```bash
   cd apps/web
   npm run dev
   ```

## Test 1: Check API Health

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `{"status":"healthy"}`

## Test 2: Check Database Connection

```bash
psql -h localhost -U postgres -d uepi_db -c "SELECT COUNT(*) FROM claims_lines;"
```

Expected: Returns a count (can be 0 if no data loaded yet)

## Test 3: Check Policies Exist

```bash
curl -X GET "http://localhost:8000/api/v1/policies" \
  -H "Authorization: Bearer dev-token-123" | python3 -m json.tool
```

Expected: Returns array of policies

## Test 4: Create Observation from Database

### Step 4a: Get a Policy ID

```bash
POLICY_ID=$(curl -s -X GET "http://localhost:8000/api/v1/policies" \
  -H "Authorization: Bearer dev-token-123" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')")
echo "Policy ID: $POLICY_ID"
```

### Step 4b: Create or Get Analysis

```bash
# Create analysis
ANALYSIS_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analyses/impact" \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json" \
  -d "{
    \"policy_id\": \"$POLICY_ID\",
    \"treatment_filters\": {\"lob\": [\"COMMERCIAL\"]},
    \"pre_window_months\": 6,
    \"post_window_months\": 1
  }")

ANALYSIS_ID=$(echo $ANALYSIS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))")
echo "Analysis ID: $ANALYSIS_ID"
```

### Step 4c: Create Observation

```bash
curl -X POST "http://localhost:8000/api/v1/observations/from-analysis/$ANALYSIS_ID?policy_id=$POLICY_ID" \
  -H "Authorization: Bearer dev-token-123" | python3 -m json.tool
```

Expected: Returns observation with metrics computed from database

## Test 5: Verify Observation Uses Database

Check the observation response for:
- `metrics.utilization_per_1k` - Should be > 0 if database has claims
- `metrics.cost_per_member` - Should be > 0 if database has claims
- `comparisons.vs_baseline` - Should have baseline comparison data
- `comparisons.vs_predicted` - Should have predicted comparison data

## Test 6: List Observations

```bash
curl -X GET "http://localhost:8000/api/v1/observations" \
  -H "Authorization: Bearer dev-token-123" | python3 -m json.tool
```

Expected: Returns array of observations

## Test 7: Check Frontend

1. Open browser: `http://localhost:3050`
2. Navigate to Observations page
3. Click on an observation
4. Verify:
   - Metrics show real values (not all N/A)
   - Baseline comparison has data
   - Predicted comparison has data
   - Values are different for different policies

## Troubleshooting

### If observations show mock data:

1. Check if claims exist in database:
   ```sql
   SELECT COUNT(*) FROM claims_lines WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
   ```

2. Check API logs for:
   - "Loading claims from database"
   - "Warning: Could not compute from database" (indicates fallback to mock)

3. Verify policy has `effective_start_date`:
   ```bash
   curl -s "http://localhost:8000/api/v1/policies/$POLICY_ID" \
     -H "Authorization: Bearer dev-token-123" | python3 -m json.tool | grep effective
   ```

### If API errors:

1. Check API server logs
2. Verify database connection in `packages/common/src/uepi_common/config.py`
3. Check PostgreSQL is running: `pg_isready -h localhost`

### If frontend shows errors:

1. Check browser console for errors
2. Verify CORS is configured in `apps/api/src/uepi_api/main.py`
3. Check network tab for API responses

## Expected Behavior

✅ **With Database Claims Data**:
- Observations compute metrics from database
- Each policy has different values based on actual claims
- Comparisons show real baseline and predicted values

⚠️ **Without Database Claims Data**:
- Observations use mock data (varied by policy_id)
- System logs: "Warning: Could not compute from database"
- This is expected fallback behavior
