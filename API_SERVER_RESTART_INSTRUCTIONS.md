# API Server Restart Instructions

## Issue
The API server process exists but is not responding to HTTP requests, causing `ERR_CONNECTION_TIMED_OUT` errors in the web app.

## Solution

I've restarted the API server using `setup-venv-and-start-api.sh`. The server should be starting up now.

## Wait Time

The API server typically takes **15-20 seconds** to fully start up, especially on first run when it needs to:
1. Activate virtual environment
2. Install/verify dependencies
3. Load all modules
4. Start uvicorn server

## Verification Steps

1. **Check if server is running**:
   ```bash
   lsof -ti:8000
   ```
   Should return a process ID

2. **Test health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy","service":"uepi-api"}`

3. **Check in browser**:
   - Open: http://localhost:8000/docs
   - Should see Swagger API documentation

## If Still Not Working

If after 20-30 seconds the server still doesn't respond:

1. **Check the terminal** where the server is running for error messages

2. **Manual restart**:
   ```bash
   # Stop any existing process
   lsof -ti:8000 | xargs kill -9
   
   # Start fresh
   ./setup-venv-and-start-api.sh
   ```

3. **Check for port conflicts**:
   ```bash
   lsof -i:8000
   ```

## Expected Behavior After Restart

Once the API server is running:
- ✅ Web app at http://localhost:3050 will connect successfully
- ✅ No more connection timeout errors
- ✅ Policies will load in Policy Catalog
- ✅ All API endpoints will work

## Current Status

The API server restart has been initiated. Please wait 15-20 seconds and then:
1. Refresh the web app at http://localhost:3050
2. The connection errors should be resolved
3. You should see data loading in the UI
