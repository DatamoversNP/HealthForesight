# Complete Workflow: Pipelines, Data Quality, and Dashboard

## Step 1: Run All Pipelines

### Check if API is Running
```bash
curl http://localhost:8000/api/v1/me
```

If you get a response, the API is running. If not, start it:
```bash
./START_API_NOW.sh
```

### Run Pipelines
```bash
./RUN_ALL_PIPELINES.sh
```

**Expected Output:**
- If pipelines exist: Shows pipeline count and runs each one
- If no pipelines: Shows "⚠️  No pipelines found"

**Note:** If no pipelines are found, you may need to:
1. Create pipelines via the UI (Pipelines page)
2. Or pipelines may be stored in a different location

### Check Pipeline Status
After running, check the Pipeline Monitoring page:
- Go to: http://localhost:3050/pipelines
- Or: http://localhost:3050/pipeline-monitoring

## Step 2: Run Data Quality Validation

### Option A: Via Dashboard (Recommended)
1. **Open Data Quality Dashboard**
   - Go to: http://localhost:3050/data-quality
   - Or navigate via sidebar: Data Quality

2. **Click "Run Validation" Button**
   - Large purple button at the top right
   - Should return immediately (async processing)

3. **Check Status**
   - The validation runs in the background
   - Can take 5-10 minutes for large datasets
   - Status endpoint: `GET /api/v1/data-quality/validate/status`

### Option B: Via API
```bash
# Start validation
curl -X POST http://localhost:8000/api/v1/data-quality/validate \
  -H "Authorization: Bearer demo-token"

# Check status
curl http://localhost:8000/api/v1/data-quality/validate/status \
  -H "Authorization: Bearer demo-token"
```

**Expected Response:**
```json
{
  "status": "started",
  "message": "Data quality validation started...",
  "started_at": "2026-01-23T..."
}
```

## Step 3: Check Data Quality Dashboard Results

### Wait for Validation to Complete
- Validation runs asynchronously
- Check status every 30-60 seconds
- Should complete in 5-10 minutes

### Refresh Dashboard
1. **Go to Data Quality Dashboard**
   - http://localhost:3050/data-quality

2. **Check Metrics**
   - **Overall Quality**: Should show actual percentage (e.g., 85.5%)
   - **Total Issues**: Number of issues found
   - **Datasets Monitored**: Number of datasets checked
   - **Avg Completeness**: Average completeness percentage

3. **Check Graphs**
   - **Quality Scores by Dataset**: Line graph showing quality over time
   - **Issues by Severity**: Bar chart showing issue breakdown

### If Still Showing 0%
- Validation may still be running (check status endpoint)
- Validation may have failed (check API logs)
- No data files may exist (check `apps/api/data/target_data_model/`)

## Troubleshooting

### No Pipelines Found
**Possible Causes:**
1. Pipelines haven't been created yet
2. Pipelines stored in different location
3. API authentication issue

**Solutions:**
1. Create pipelines via UI: http://localhost:3050/pipelines
2. Check pipeline storage: `data/pipelines/` or `apps/api/data/pipelines/`
3. Verify API is running: `curl http://localhost:8000/api/v1/pipelines`

### Validation Not Starting
**Check:**
1. API is running: `curl http://localhost:8000/api/v1/me`
2. Data files exist: `ls -la apps/api/data/target_data_model/`
3. Validation script exists: `ls -la scripts/comprehensive_data_quality_check.py`

### Validation Stuck
**Check Status:**
```bash
curl http://localhost:8000/api/v1/data-quality/validate/status \
  -H "Authorization: Bearer demo-token"
```

**If Status is "running":**
- Wait longer (can take 10+ minutes)
- Check for validation process: `ps aux | grep comprehensive_data_quality`

**If Status is "error":**
- Check error message in status response
- Check API server logs
- Re-run validation

## Quick Status Check Script

Create `CHECK_STATUS.sh`:
```bash
#!/bin/bash
echo "🔍 Checking System Status"
echo "========================"
echo ""
echo "1. API Status:"
curl -s http://localhost:8000/api/v1/me > /dev/null && echo "   ✅ API is running" || echo "   ❌ API is not running"
echo ""
echo "2. Pipelines:"
PIPELINES=$(curl -s http://localhost:8000/api/v1/pipelines -H "Authorization: Bearer demo-token")
COUNT=$(echo "$PIPELINES" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(len(d) if isinstance(d, list) else 0)" 2>/dev/null || echo "0")
echo "   Found: $COUNT pipeline(s)"
echo ""
echo "3. Data Quality Validation:"
STATUS=$(curl -s http://localhost:8000/api/v1/data-quality/validate/status -H "Authorization: Bearer demo-token")
echo "   $STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"   Status: {d.get('status', 'unknown')}\")" 2>/dev/null || echo "   Status: unknown"
echo ""
echo "4. Data Files:"
if [ -d "apps/api/data/target_data_model" ]; then
    FILE_COUNT=$(find apps/api/data/target_data_model -name "*.csv" | wc -l)
    echo "   Found: $FILE_COUNT CSV file(s)"
else
    echo "   ⚠️  Data directory not found"
fi
```

## Summary

1. ✅ **Run Pipelines**: `./RUN_ALL_PIPELINES.sh`
2. ✅ **Run Validation**: Click "Run Validation" on dashboard
3. ✅ **Check Results**: Refresh Data Quality Dashboard

All steps are now ready to execute!
