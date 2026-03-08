# Pipeline Restoration Guide

## Current Situation

**Problem:**
- UI shows "Preconfigured (0)" and "Custom (0)" pipelines
- But 22 pipeline files exist in `data/pipelines/`
- Storage test confirms all 22 pipelines are found
- API returns empty array `[]`

**Root Cause:**
The API server loaded storage at startup when pipelines weren't present, and hasn't reloaded them. A restart is needed.

## Solution: Restart API Server

### Step 1: Stop Current API Server
1. Find the terminal where the API is running
2. Press `CTRL+C` to stop it

### Step 2: Restart API Server
```bash
./START_API_NOW.sh
```

Wait for the server to start (you'll see "Uvicorn running on http://0.0.0.0:8000")

### Step 3: Verify Pipelines Load
```bash
./FIX_AND_VERIFY_PIPELINES.sh
```

This will:
- ✅ Check pipeline files exist
- ✅ Test storage loading
- ✅ Test API endpoint
- ✅ Show if pipelines are loading correctly

### Step 4: Refresh Browser
1. Go to: http://localhost:3050/pipelines
2. Refresh the page (F5 or Cmd+R)
3. You should now see:
   - **Preconfigured (22)** instead of (0)
   - All your pipelines listed

## Expected Results

After restart, you should see:

### In API:
```bash
curl http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token"
```

Returns 22 pipelines including:
- Concurrent Review Pipeline
- Network Configuration Pipeline
- Market Event Pipeline
- Care Management Enrollment Pipeline
- Claims Lines Pipeline
- And 17 more...

### In UI:
- **Preconfigured (22)** tab shows all pipelines
- Each pipeline shows:
  - Name
  - Type
  - Status (Active/Inactive)
  - Created date
  - Actions (Run, Edit, Delete)

## Troubleshooting

### If API Still Returns 0 After Restart

1. **Check API logs** for errors:
   - Look for "Error listing pipelines" messages
   - Check for path issues

2. **Verify storage path**:
   ```bash
   python3 -c "from apps.api.src.uepi_api.storage_file import BASE_PATH; print(BASE_PATH)"
   ```
   Should show: `data` or `./data`

3. **Check pipeline files**:
   ```bash
   ls -la data/pipelines/pipeline-*.json | wc -l
   ```
   Should show: 22

### If UI Still Shows 0 After API Restart

1. **Hard refresh browser**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. **Clear browser cache**
3. **Check browser console** for JavaScript errors
4. **Verify API is responding**:
   ```bash
   curl http://localhost:8000/api/v1/pipelines \
     -H "Authorization: Bearer demo-token" | python3 -m json.tool
   ```

## Quick Verification Commands

```bash
# Check pipeline files
find data/pipelines -name "pipeline-*.json" | wc -l

# Test storage
./RESTORE_PIPELINES.sh

# Test API
curl -s http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Found {len(d)} pipelines')"

# Full verification
./FIX_AND_VERIFY_PIPELINES.sh
```

## Summary

Your 22 pipelines are safe and stored correctly. They just need the API server to be restarted to reload them. After restart:

1. ✅ API will return all 22 pipelines
2. ✅ UI will show "Preconfigured (22)"
3. ✅ You can run pipelines using `./RUN_ALL_PIPELINES.sh`

All your predefined pipelines will be restored!
