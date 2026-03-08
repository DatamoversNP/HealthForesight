# Fixed: Storage Path Issue

## Root Cause

The API server changes directory to `apps/api/src` before starting (in `START_API_NOW.sh`), so when the storage code uses `./data`, it resolves to `apps/api/src/data` instead of the project root `data/`.

## The Fix

Updated `apps/api/src/uepi_api/storage_file.py` to:
1. Calculate project root from `__file__` location
2. Use **absolute path** to `project_root/data` instead of relative `./data`
3. This ensures pipelines are found regardless of working directory

## What Changed

**Before:**
```python
return "./data"  # Relative - wrong when running from apps/api/src
```

**After:**
```python
project_root = Path(__file__).parent.parent.parent.parent.parent
return str(project_root / "data")  # Absolute - always correct
```

## Next Steps

1. **Restart API Server:**
   ```bash
   # Stop current API (CTRL+C)
   ./START_API_NOW.sh
   ```

2. **Verify Pipelines Load:**
   ```bash
   ./FIX_AND_VERIFY_PIPELINES.sh
   ```

3. **Should now show:**
   ```
   ✅ API returns 22 pipelines
   ```

4. **Refresh browser** at http://localhost:3050/pipelines

## Why This Works

- **Before:** API runs from `apps/api/src/`, so `./data` → `apps/api/src/data` (doesn't exist)
- **After:** Uses absolute path `project_root/data` → `/Users/.../data` (correct location)

The fix ensures the storage path is always correct regardless of where the API server runs from!
