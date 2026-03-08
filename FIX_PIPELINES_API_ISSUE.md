# Fix: Pipelines Not Loading in API

## Problem
- ✅ **22 pipelines exist** in `data/pipelines/`
- ✅ **Storage test finds all 22 pipelines**
- ❌ **API returns empty array `[]`**

## Root Cause
The API server is running but not loading pipelines. This is likely because:
1. API server needs restart to reload storage
2. Storage path might be different when API runs vs. direct test

## Solution

### Step 1: Restart API Server
The API server needs to be restarted to reload the pipelines:

```bash
# Stop current API server (CTRL+C in terminal running API)
./START_API_NOW.sh
```

### Step 2: Verify Pipelines Load
After restart, test again:
```bash
./RESTORE_PIPELINES.sh
```

Or directly:
```bash
curl http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" | python3 -m json.tool
```

### Step 3: Check API Logs
If still not working, check API server logs for:
- Storage path being used
- Any errors loading pipelines
- Tenant ID being used

## Expected Result After Restart

You should see 22 pipelines in the API response, including:
- Concurrent Review Pipeline
- Network Configuration Pipeline  
- Market Event Pipeline
- Care Management Enrollment Pipeline
- Claims Lines Pipeline
- And 17 more...

## Why This Happens

The pipelines are stored correctly in `data/pipelines/`, but the API server:
1. Loads storage paths at startup
2. May cache the initial (empty) state
3. Needs restart to reload from disk

## Quick Test

After restarting, you can quickly test:
```bash
curl -s http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Found {len(d)} pipelines')"
```

Should show: `Found 22 pipelines`
