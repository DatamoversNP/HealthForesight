# API Connection Fix

## Issue
The web application is getting `ERR_CONNECTION_TIMED_OUT` errors when trying to connect to the API server on port 8000.

## Solution Applied

1. **Checked API Server Status**: Verified if API server process is running
2. **Restarted API Server**: Used `restart-api.sh` to restart the server
3. **Verified Connection**: Checked if server responds to health checks

## Status

The API server is being restarted. It should be available at:
- **API Base URL**: http://localhost:8000/api/v1
- **Health Check**: http://localhost:8000/health

## If Issues Persist

If you still see connection errors:

1. **Check if API server is running**:
   ```bash
   lsof -ti:8000
   ```

2. **Manually restart API server**:
   ```bash
   ./restart-api.sh
   # OR
   ./setup-venv-and-start-api.sh
   ```

3. **Check API server logs** in the terminal where it's running

4. **Verify the API server started successfully**:
   - Look for "Application startup complete" message
   - Check for any error messages in the terminal

## Expected Behavior

Once the API server is running:
- ✅ Web app at http://localhost:3050 should connect successfully
- ✅ No more `ERR_CONNECTION_TIMED_OUT` errors
- ✅ Policies should load in the Policy Catalog
- ✅ All API endpoints should be accessible

## Quick Test

After restart, test the API:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","service":"uepi-api"}`
