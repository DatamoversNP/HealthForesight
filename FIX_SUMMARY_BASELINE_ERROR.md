# Baseline Analysis Error Fix Summary

## Problem
Baseline analysis failing with 500 error: "Missing dependency: cann...lease ensure all required packages are installed."

## Root Cause
The `BaselineAnalysisEngine` needs:
- ✅ `scipy` (already in startup script)
- ✅ `scikit-learn` (already in startup script)  
- ❌ `statsmodels` (missing from startup script)

Additionally, the endpoint didn't check dependencies upfront, making errors hard to diagnose.

## Fixes Applied

### 1. Added Dependency Check to API Endpoint ✅
**File:** `apps/api/src/uepi_api/routers/analyses.py`

Added upfront dependency check before running baseline analysis:
```python
# Check for required dependencies
missing_deps = []
try:
    import scipy
except ImportError:
    missing_deps.append("scipy")
    
try:
    import sklearn
except ImportError:
    missing_deps.append("scikit-learn")
    
try:
    import statsmodels
except ImportError:
    missing_deps.append("statsmodels")

if missing_deps:
    raise HTTPException(
        status_code=503,
        detail=f"Missing required dependencies: {', '.join(missing_deps)}. Please install them: pip install {' '.join(missing_deps)}"
    )
```

**Benefits:**
- Clear error message if dependencies are missing
- Returns 503 (Service Unavailable) instead of 500
- Provides installation instructions

### 2. Added statsmodels to Startup Script ✅
**File:** `start-both-servers.sh`

Added `statsmodels` to the pip install list:
```bash
pip install --quiet \
    ...
    scipy \
    numpy \
    scikit-learn \
    statsmodels  # ← Added this
```

**Benefits:**
- Dependencies automatically installed when starting servers
- Ensures consistent environment setup

## Next Steps

### 1. Restart API Server
The server needs to be restarted to:
- Pick up the new dependency check code
- Install `statsmodels` if it's missing

```bash
./stop-both-servers.sh
./start-both-servers.sh
```

This will:
- Install all dependencies including `statsmodels`
- Start servers with updated code

### 2. Verify Dependencies
You can verify in the API server environment:
```bash
# If server is running via venv
source .venv/bin/activate
python3 -c "import scipy; import sklearn; import statsmodels; print('✅ All dependencies available')"
```

### 3. Run Baseline Analysis
After restart:
- Via UI: Navigate to `http://localhost:3050/baseline-analysis` and click "Run Baseline Analysis"
- Or the analysis should work now with all dependencies installed

## Expected Results

**Before Fix:**
- ❌ Generic 500 error
- ❌ Unclear error message
- ❌ Missing statsmodels dependency

**After Fix:**
- ✅ Clear error message if dependencies missing (503 status)
- ✅ All dependencies installed via startup script
- ✅ Baseline analysis should work

## If Still Getting Errors

If you still get errors after restarting:

1. **Check server logs** for detailed error messages:
   ```bash
   tail -f api-server.log
   ```

2. **Verify dependencies are installed**:
   ```bash
   source .venv/bin/activate
   pip list | grep -E "scipy|scikit-learn|statsmodels"
   ```

3. **Install manually if needed**:
   ```bash
   pip install scipy scikit-learn statsmodels
   ```

4. **Check the error message** - it should now be clear what's missing!

## Files Modified
- ✅ `apps/api/src/uepi_api/routers/analyses.py` - Added dependency check
- ✅ `start-both-servers.sh` - Added statsmodels to install list

All fixes are complete and ready to test!
