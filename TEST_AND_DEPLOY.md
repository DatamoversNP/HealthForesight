# Test and Deploy Guide

## Problem Found
The API is running but returning 0 policies because `STORAGE_PATH` is not set correctly.

## Solution

### Step 1: Restart API with Correct Path
```bash
./restart_api_with_data.sh
```

This script:
- Sets `STORAGE_PATH` to the absolute path of `data/` directory
- Restarts the API with correct environment
- Ensures API can find policy files

### Step 2: Test API
In another terminal:
```bash
./test_api_local.sh
```

**Expected results:**
- ✅ Assumptions: 3
- ✅ Guardrails: 3  
- ✅ Versions: 1
- ✅ Policies: 24+

### Step 3: Deploy
Once tests pass:
```bash
./START_PRODUCTION_BUILD.sh
```

## Why This Happens

The API calculates project root from file paths, but when running locally, the `STORAGE_PATH` environment variable must be set to the absolute path of the `data/` directory.

The `restart_api_with_data.sh` script sets this automatically.

## Quick Test
```bash
# After restarting API, test:
curl http://localhost:8000/api/v1/policies/ST_BIOLOGIC_006/workspace | python3 -m json.tool | grep -A 2 assumptions
```

You should see assumptions data in the response.

