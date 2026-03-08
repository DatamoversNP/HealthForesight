# Critical Fix Applied - Timeout Issues

## Problem
Frontend requests timing out at exactly 10 seconds because:
1. Frontend timeout was still 10 seconds (not updated to 60)
2. Database connection tests were hanging (no timeout wrapper)

## Fixes Applied ✅

### 1. Frontend Timeout Increased
**File:** `apps/web/src/lib/api.ts`
- Changed default timeout from `10000ms` (10 seconds) to `60000ms` (60 seconds)
- Updated all individual timeout overrides:
  - `/policies` endpoint: 10s → 60s
  - Pipeline runs: 10s → 60s
  - Pipeline health: 10s → 60s

### 2. Database Connection Test with Timeout
**File:** `apps/api/src/uepi_api/auth.py`
- Added `ThreadPoolExecutor` to run connection tests with timeout
- Connection test now has 5-second timeout wrapper
- If connection test times out or fails, skips database queries and uses demo user

## Action Required

### 1. Restart Frontend (if running)
The frontend needs to be rebuilt/restarted to pick up the new timeout:
```bash
# In the frontend terminal, restart the dev server
# Or just refresh the browser after rebuilding
```

### 2. Restart API Server (REQUIRED)
The API server must be restarted for the connection test timeout to take effect:
```bash
cd apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Expected Behavior After Restart

✅ Frontend requests will wait up to 60 seconds (instead of 10)  
✅ Database connection tests will timeout after 5 seconds (instead of hanging)  
✅ Auth endpoints will work even if database is unavailable (demo user fallback)  
✅ Clear error messages when database connection fails

## Why This Should Work Now

1. **Frontend timeout (60s)** > **Connection test timeout (5s)** > **Database query timeout (30s)**
   - Frontend gives enough time for slow operations
   - Connection test fails fast if database is unavailable
   - Actual queries have their own timeout protection

2. **Graceful degradation**: If database is unavailable, auth endpoints return demo user immediately (no database queries)

3. **Clear error messages**: Instead of hanging, requests will fail with specific error messages

## If Issues Persist

1. **Check if PostgreSQL is running:**
   ```bash
   ps aux | grep postgres
   ```

2. **Test database connection:**
   ```bash
   psql -h localhost -U postgres -d uepi_db
   ```

3. **Check API server logs** for specific database errors

4. **Verify both servers restarted:**
   - Frontend: Check browser console for new timeout values
   - API: Check server logs for "Application startup complete"
