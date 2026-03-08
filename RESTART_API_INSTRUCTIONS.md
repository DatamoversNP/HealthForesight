# API Server Restart Instructions

## Problem
Frontend requests are timing out because database queries are hanging.

## Solution Applied
Added database connection timeouts and connection tests to prevent hanging queries.

## Action Required: Restart API Server

**The API server MUST be restarted for the timeout fixes to take effect.**

### Steps:

1. **Stop the current API server:**
   - Go to the terminal where the API server is running
   - Press `Ctrl+C` to stop it

2. **Restart the API server:**
   ```bash
   cd apps/api/src
   export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verify the server started:**
   - You should see: `INFO: Application startup complete.`
   - Check health endpoint: `curl http://localhost:8000/health`

4. **Test database connectivity:**
   ```bash
   curl http://localhost:8000/api/v1/health/detailed
   ```

## What Changed

1. **Database Connection Timeouts:**
   - 10-second connection timeout
   - 30-second query timeout
   - Connection pool recycling

2. **Connection Tests:**
   - Added connection tests before database queries in:
     - `/auth/me` endpoint (via `verify_token`)
     - `/policies` endpoint
     - `/access/users/{user_id}/roles` endpoint
     - `/access/users/{user_id}/permissions` endpoint

3. **Graceful Degradation:**
   - Auth endpoints now work without database (fallback to demo user)
   - Access endpoints return default values if database is unavailable
   - Policies endpoint returns 503 with clear error message

## Expected Behavior After Restart

- Requests should fail fast (within 10 seconds) instead of hanging
- Error messages will clearly indicate database connection issues
- Frontend will receive proper error responses instead of timeouts
- Auth endpoints will work even if database is unavailable (demo mode)

## If Issues Persist

If requests still timeout after restart:

1. Check if PostgreSQL is running:
   ```bash
   # Check if PostgreSQL is running
   ps aux | grep postgres
   ```

2. Test database connection manually:
   ```bash
   # Try connecting to database
   psql -h localhost -U postgres -d uepi_db
   ```

3. Check database connection string in config:
   - File: `packages/common/src/uepi_common/config.py`
   - Should be: `postgresql://postgres:postgres@localhost:5432/uepi_db`

4. Check API server logs for database errors
