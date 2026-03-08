# API Server Import Fixes

## Issues Fixed

1. **Fixed `policy_versions.py` router imports:**
   - Removed: `get_active_policy_version`, `get_latest_policy_version`, `track_version_changes`
   - Added: `get_latest_version`, `update_policy_version`
   - Updated all endpoint functions to use correct function names

2. **Fixed `observation_enhancement.py` imports:**
   - Changed: `get_latest_policy_version` → `get_latest_version`

3. **Fixed `analyses_file.py` imports:**
   - Changed: `get_latest_policy_version` → `get_latest_version`

4. **Fixed `integration_helpers.py` imports:**
   - Removed: `track_version_changes` (doesn't exist)
   - Changed: `get_latest_policy_version` → `get_latest_version`

## Start Server

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_API_SERVER.sh
```

Or manually:
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api
export PYTHONPATH="$(cd ../.. && pwd)/apps/api/src:$(cd ../.. && pwd)/packages/common/src:${PYTHONPATH}"
python3 -m uvicorn uepi_api.main:app --reload --port 8000
```

## Verify

Once started, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test:
```bash
curl http://localhost:8000/docs
```


