# Frontend Data Loading Diagnostics

## Problem
Data is not visible on the frontend.

## Root Causes (Most Likely)

### 1. API Timeouts (Still Happening)
- API requests timing out before database queries complete
- **Fix Applied**: Increased frontend timeout to 60 seconds, added connection test timeouts

### 2. Empty Database
- No policies, observations, or other data in the database
- API returns empty arrays `[]` which frontend displays as "No data found"
- **Check**: Look at API server logs for "DEBUG" messages showing counts

### 3. Tenant ID Mismatch
- Data exists in database but with different tenant_id
- API filters by `current_user.tenant_id` which might not match data
- **Fix Applied**: Added debug logging to show tenant IDs in database vs. requested tenant ID

### 4. Database Connection Still Failing
- Connection tests pass but actual queries fail
- **Fix Applied**: Added connection tests before queries, better error handling

## Debugging Steps

### Check API Server Logs
Look for these debug messages:
```
DEBUG list_policies: Total policies in DB: X
DEBUG list_policies: Tenant IDs in DB: [...]
DEBUG list_policies: Looking for tenant_id: ...
DEBUG list_policies: Found X policies for tenant ...
```

### Check Frontend Console
Look for these console logs:
```
Loading policies...
Policies API response: { isArray: true, length: X, data: [...] }
Mapped policies: X
Loading observations with params: {...}
Observations API response: { isArray: true, length: X, data: [...] }
```

### Check Browser Network Tab
1. Open browser DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Look for requests to `/api/v1/policies` and `/api/v1/observations`
4. Check:
   - **Status**: Should be 200 (not 0, 500, or timeout)
   - **Response**: Should show actual data or empty array `[]`
   - **Time**: Should complete in < 10 seconds (not timeout)

## What Was Fixed

### 1. Enhanced Debug Logging
- Added detailed logging in API endpoints to show:
  - Total records in database
  - Tenant IDs in database
  - Records found for requested tenant
  - Query parameters used

### 2. Frontend Console Logging
- Added console.log statements to track:
  - API responses
  - Data transformation
  - Error details

### 3. Better Error Handling
- Frontend now shows specific error messages
- API returns detailed error messages instead of generic failures

## Next Steps

1. **Restart API Server** (required for debug logging to take effect)
2. **Open Browser Console** and check for debug messages
3. **Check API Server Logs** for debug output
4. **Verify Database Has Data**:
   - Use Database Viewer page to check `policies` and `observations` tables
   - Or check API logs for "Total policies in DB: X"

## If Database is Empty

If API logs show "Total policies in DB: 0", you need to:
1. Create policies using the Policy Catalog page
2. Generate claims data using the "Generate Claims Data" button
3. Run baseline analysis
4. Generate predicted impacts
5. Create observations

## If Tenant ID Mismatch

If API logs show policies exist but "Found 0 policies for tenant", the tenant_id in the database doesn't match the current user's tenant_id. Check:
- What tenant_id is in the database (from debug logs)
- What tenant_id the current user has (should be `00000000-0000-0000-0000-000000000001` for demo)
