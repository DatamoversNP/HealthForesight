# Restart API to Load Pipelines

## Current Status

✅ **22 pipeline files exist** in `data/pipelines/`
✅ **Storage test finds all 22 pipelines**
❌ **API returns 0 pipelines** (empty array)

## Solution: Restart API Server

The API server loaded storage at startup and needs to be restarted to reload pipelines.

### Step 1: Stop Current API Server

1. Find the terminal where the API is running
2. Look for output like:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```
3. Press `CTRL+C` to stop it

### Step 2: Restart API Server

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./START_API_NOW.sh
```

Wait for:
```
✅ uepi_api module found!
🌐 Starting API server...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Verify Pipelines Load

After restart, run:
```bash
./FIX_AND_VERIFY_PIPELINES.sh
```

You should see:
```
✅ API returns 22 pipelines
```

### Step 4: Refresh Browser

1. Go to: http://localhost:3050/pipelines
2. Refresh page (F5 or Cmd+R)
3. Should see: **Preconfigured (22)** instead of (0)

## Debug Logging Added

I've added debug logging to help diagnose the issue. After restart, check API logs for:
- `[PIPELINES] Listing pipelines for tenant: ...`
- `[STORAGE_PIPELINES] Storage.list_all() returned X pipelines`
- `[STORAGE_PIPELINES] After filtering by tenant_id, X pipelines remain`

This will help identify if:
- Storage is loading correctly
- Tenant ID filtering is working
- Pipelines are being returned

## Quick Test After Restart

```bash
curl -s http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Found {len(d)} pipelines')"
```

Should show: `Found 22 pipelines`

## Summary

**Action Required:** Restart API server to reload pipelines from storage.

After restart, all 22 pipelines should appear in both API and UI!
