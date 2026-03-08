# File Storage Only Refactoring - Progress

## ✅ Completed
1. **Added predicted impact endpoints to `policies_file.py`**
   - GET `/policies/{policy_id}/predicted-impact`
   - POST `/policies/{policy_id}/predicted-impact`
   - POST `/policies/generate-predicted-impact`
   - All endpoints use file storage only (no database)

2. **Removed database import from `policies_file.py`**
   - Removed `from uepi_api.database import USE_FILE_STORAGE`
   - Router is now file-storage only

## ⚠️ Current Issue
- `storage_policies.py` has an error: `AttributeError: module 'uepi_api.storage.policy_storage' has no attribute 'list_all'`
- This is a mismatch between the storage API used by `storage_policies.py` and the actual storage implementation

## 📋 Next Steps

Since you want to remove ALL database references, here's what still needs to be done:

1. **Fix `storage_policies.py`** - It's using the wrong storage API
2. **Remove database references from other routers** (analyses, scorecards, etc.)
3. **Update `main.py`** to remove database/router conditional logic
4. **Clean up database.py** or remove it entirely
5. **Remove SQLAlchemy dependencies** (if not needed elsewhere)

## Current Status
- The API is running but policies endpoint has an error
- Predicted impact endpoints are added but can't be tested until storage issue is fixed
- File-based router is ready, just needs storage layer fix

## Recommendation
The system is already mostly file-based. The main issue is that `storage_policies.py` needs to be fixed to use the correct storage API. Once that's fixed, the file-based router should work correctly.
