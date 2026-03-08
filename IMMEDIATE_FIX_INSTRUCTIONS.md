# Immediate Fix Instructions - CORS and 500 Errors

## The Problem
The API server is still running OLD code without CORS configuration. The server needs to be restarted to pick up the fixes.

## Quick Fix (Run This Now)

Open Terminal and run:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./RESTART_API_NOW.sh
```

This script will:
1. ✅ Stop the old API server
2. ✅ Install missing dependencies (scikit-learn, scipy, numpy)
3. ✅ Start API server with NEW CORS configuration
4. ✅ Verify it's working

## After Running the Script

Wait 10 seconds, then:
1. Refresh your browser at http://localhost:3050/policies
2. Click "Generate Predicted Impact" button
3. Should work now! ✅

## If It Still Doesn't Work

Check the logs:
```bash
tail -f api-server.log
```

Look for:
- ✅ "Application startup complete" = Good
- ❌ Any "ERROR" or "ImportError" = Problem

## What Was Fixed

1. **CORS Configuration** (`apps/api/src/uepi_api/main.py`)
   - Added comprehensive CORS origins list
   - Configured proper headers

2. **Dependencies** 
   - Added scikit-learn to install list
   - scipy and numpy already included

3. **Import Handling**
   - Made scipy imports optional in analytics code
   - Added early validation

## Summary

**The code is fixed, but the server needs to restart to use it.**

Run `./RESTART_API_NOW.sh` and it will work! 🚀
