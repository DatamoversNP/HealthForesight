# Fix: Missing Pipelines Issue

## Problem
You had 20+ predefined pipelines that were executed earlier, but they're not showing up in the API response.

## Investigation Results

✅ **Pipelines Exist**: Found 20 pipeline files in `data/pipelines/`
✅ **Index Exists**: `data/pipelines/index.json` has 22 pipeline IDs
✅ **Storage Works**: Direct storage test found 22 pipelines
✅ **Tenant ID Matches**: All pipelines have correct tenant_id (`00000000-0000-0000-0000-000000000001`)

## Root Cause

The pipelines are stored correctly, but the API endpoint may not be loading them properly. This could be due to:
1. API server needs restart to reload storage
2. Authentication issue with the endpoint
3. Storage path mismatch

## Solution

### Step 1: Verify Pipelines Exist
```bash
./RESTORE_PIPELINES.sh
```

This script will:
- Count pipeline files
- Test storage loading
- Test API endpoint
- Show sample pipelines

### Step 2: Restart API Server
If pipelines are found in storage but not in API:
```bash
# Stop current API server (CTRL+C)
./START_API_NOW.sh
```

### Step 3: Verify Pipelines Load
After restart, check:
```bash
curl http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" | python3 -m json.tool
```

Or use the script:
```bash
./RESTORE_PIPELINES.sh
```

## Expected Results

After restart, you should see:
- **22 pipelines** in API response
- Pipeline names like:
  - Concurrent Review Pipeline
  - Network Configuration Pipeline
  - Market Event Pipeline
  - Claim Header Pipeline
  - etc.

## If Still Not Working

1. **Check API logs** for errors
2. **Verify storage path** - pipelines should be in `data/pipelines/`
3. **Check tenant_id** - all pipelines should have `00000000-0000-0000-0000-000000000001`
4. **Test storage directly** - the script does this automatically

## Pipeline Files Found

The following pipeline files exist:
- `pipeline-421d1ae3-a1a7-4827-9538-778b2839b7da.json` (Claim Header Pipeline)
- `pipeline-6852d537-9bd9-43f6-8a3e-a6dbcb24d6d3.json`
- `pipeline-d7bb307a-faf5-4bb0-96b7-574c9d952c89.json`
- ... and 17 more

All pipelines are ready to be restored - just need to restart the API server!
