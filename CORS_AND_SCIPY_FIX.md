# CORS and Missing Dependency Fix

## Issues Found

### 1. ✅ CORS Configuration
- **Status**: Fixed
- The CORS configuration is correct and working (OPTIONS requests return 200 OK)

### 2. ❌ Missing Dependency: `scipy`
- **Error**: `ModuleNotFoundError: No module named 'scipy'`
- **Cause**: The predicted-impact endpoint imports `scipy.stats` but scipy is not installed
- **Location**: `uepi_common.analytics.method_checks` imports `scipy.stats`

## Fix Applied

1. **Added `scipy` and `numpy`** to the setup script (`setup-venv-and-start-api.sh`)
2. **Installing scipy** in the virtual environment
3. **Restarting API server** with the new dependencies

## Status

✅ **CORS**: Fixed (working correctly)  
✅ **Dependencies**: Added scipy and numpy to setup script  
⏳ **API Server**: Restarting with scipy installed

## Next Steps

Wait 20-30 seconds for the API server to restart, then:

1. **Refresh your browser** (hard refresh: Cmd+Shift+R)
2. **Try the Predicted Impact button again**
3. The errors should be resolved:
   - ✅ CORS errors: Fixed
   - ✅ 500 errors: Should be fixed once scipy is installed

## Verification

After restart, test:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","service":"uepi-api"}`

The predicted impact endpoint should now work without errors!
