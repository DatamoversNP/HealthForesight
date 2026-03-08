# Indentation Error Fixed

## Issue Found

The API server was failing to start with an `IndentationError` in `apps/api/src/uepi_api/main.py` at line 140.

**Error**: `IndentationError: unexpected indent`

## Root Cause

The file had router includes and endpoint definitions that were incorrectly placed:
1. Router includes were outside the `create_app()` function (lines 118-138)
2. Endpoint definitions (`@app.get("/health")`) had incorrect indentation
3. There was a duplicate `return app` statement
4. The `/api/v1/health/db` endpoint referenced a non-existent `engine` variable

## Fix Applied

1. **Moved all router includes inside `create_app()` function**
   - Stage 2 Policy API
   - Phase 2: Baselines  
   - Phase 3: Observations
   - Phase 4: Learning Loop
   - Phase 5: Traceability

2. **Fixed indentation of endpoint definitions**
   - `/health` and `/api/v1/health` endpoints
   - `/metrics` endpoint

3. **Removed duplicate `return app` statement**

4. **Removed `/api/v1/health/db` endpoint** (references non-existent database engine - not needed for file-storage-only mode)

## Verification

The file now:
- ✅ Has correct Python syntax
- ✅ All routers properly included inside `create_app()`
- ✅ All endpoints correctly indented
- ✅ Single `return app` at the end of function

## Next Steps

The API server should now start successfully. Test with:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","service":"uepi-api"}`
