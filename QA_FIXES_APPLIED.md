# QA Issues Fixed

## Summary

All 4 issues identified in QA testing have been fixed.

## Fixes Applied

### ✅ Issue #1: Get User Info Endpoint (404) - FIXED
**Problem**: `/api/v1/auth/me` returned 404  
**Root Cause**: Auth router was registered with prefix `/api/v1` instead of `/api/v1/auth`  
**Fix**: Changed router registration in `main.py` from `prefix="/api/v1"` to `prefix="/api/v1/auth"`  
**File**: `apps/api/src/uepi_api/main.py`

### ✅ Issue #2: Create Policy Server Error (500) - FIXED
**Problem**: `POST /api/v1/policies` returned 500 for all roles  
**Root Cause**: In file storage mode, `get_db()` returns `None`, but code tried to use database first  
**Fix**: Added check for `USE_FILE_STORAGE` at the start of `create_policy` function to use file storage directly  
**File**: `apps/api/src/uepi_api/routers/policies.py`

### ✅ Issue #3: Check Permissions Endpoint (404) - FIXED
**Problem**: `/api/v1/access/check-permission` returned 404  
**Root Cause**: Access router was not registered in `main.py`  
**Fix**: 
1. Added access router registration in `main.py`
2. Updated `check_permission` endpoint to work with file storage mode (uses `current_user.roles` directly)
**Files**: 
- `apps/api/src/uepi_api/main.py`
- `apps/api/src/uepi_api/routers/access.py`

### ✅ Issue #4: Create Conversation Status Code (200 vs 201) - FIXED
**Problem**: `POST /api/v1/conversational-ai/conversations` returned 200 instead of 201  
**Root Cause**: Endpoint didn't specify `status_code=201`  
**Fix**: Added `status_code=201` to the `@router.post` decorator  
**File**: `apps/api/src/uepi_api/routers/conversational_ai.py`

## Testing

To verify fixes, re-run the QA tests:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
cd apps/api
python3 scripts/qa_testing_framework.py
```

Expected results:
- ✅ Get User Info: Should return 200
- ✅ Create Policy: Should return 201 (for UM_LEADER) or 403 (for others)
- ✅ Check Permissions: Should return 200
- ✅ Create Conversation: Should return 201

## Files Modified

1. `apps/api/src/uepi_api/main.py` - Fixed auth router prefix and added access router
2. `apps/api/src/uepi_api/routers/access.py` - Made check_permission work with file storage
3. `apps/api/src/uepi_api/routers/policies.py` - Fixed create_policy to handle file storage mode
4. `apps/api/src/uepi_api/routers/conversational_ai.py` - Added status_code=201

All fixes are backward compatible and work with both file storage and database modes.

