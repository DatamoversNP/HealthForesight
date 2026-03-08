# API Timeout Fixes

## Problem
Frontend requests are timing out after 10 seconds because database queries are hanging indefinitely.

## Root Cause
Database connection and queries were not configured with timeouts, causing requests to hang when the database is slow or unavailable.

## Fixes Applied

### 1. Database Connection Timeouts (`apps/api/src/uepi_api/database.py`)
- Added `connect_timeout: 10` (10 second connection timeout)
- Added `statement_timeout: 30000` (30 second query timeout)
- Added `pool_recycle: 3600` (recycle connections after 1 hour)

### 2. Connection Tests Before Queries
- Added connection test in `list_policies` endpoint
- Added connection tests in `get_user_roles` and `get_user_permissions` endpoints
- These tests fail fast if database is unavailable

### 3. Enhanced Health Endpoint
- Added `/api/v1/health/detailed` endpoint that tests database connectivity
- Basic `/health` endpoint remains fast (no database check)

## Next Steps

1. **Restart the API server** to apply the timeout changes:
   ```bash
   # Stop the current server (Ctrl+C in the terminal running it)
   # Then restart:
   cd apps/api/src
   export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Test the health endpoint** (should respond quickly):
   ```bash
   curl http://localhost:8000/health
   ```

3. **Test database connectivity**:
   ```bash
   curl http://localhost:8000/api/v1/health/detailed
   ```

4. **If database is not accessible**, check:
   - Is PostgreSQL running?
   - Is the database connection string correct?
   - Can you connect to the database manually?

## Expected Behavior After Fix

- Requests should fail fast (within 10 seconds) instead of hanging
- Error messages will indicate database connection issues
- Frontend will receive proper error responses instead of timeouts
