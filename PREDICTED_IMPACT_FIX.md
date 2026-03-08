# Fix for Predicted Impact 404 Error

## Problem

The API was returning 404 errors when trying to access predicted impact because:
1. Policies file was in `data/policies_{tenant_id}.json`
2. API storage adapter looks for files in `/tmp/policies_{tenant_id}.json`
3. The `PolicyStorageAdapter` was missing a `get_policy()` method (only had `get_policies()`)

## Solution

1. **Copied policies file to `/tmp`**: The policies file with predicted impact has been copied to `/tmp/policies_00000000-0000-0000-0000-000000000002.json` where the API expects it.

2. **Added `get_policy()` method**: Added the missing `get_policy()` method to `PolicyStorageAdapter` class in `apps/api/src/uepi_api/storage/policy_storage.py`.

## Files Changed

- `apps/api/src/uepi_api/storage/policy_storage.py`: Added `get_policy()` method

## Next Steps

The API should now be able to:
- List all policies (already working)
- Get a single policy by ID (now fixed)
- Get predicted impact for a policy (should now work)

Try clicking the Psychology icon (🧠) button on any policy in the Policy Catalog page to view predicted impact.
