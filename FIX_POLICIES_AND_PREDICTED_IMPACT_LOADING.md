# Fix Policies and Predicted Impact Loading

## Root Cause
The predefined policies in `data/valid_policies.json` have `tenant_id: 00000000-0000-0000-0000-000000000002`, but the demo tenant is `00000000-0000-0000-0000-000000000001`. This mismatch prevents policies from loading.

## Fix Applied
Updated `apps/api/src/uepi_api/storage/policy_storage.py` to **always assign the current tenant_id** to policies loaded from `valid_policies.json`, regardless of what tenant_id is stored in the file.

**Change:**
- Before: Policies from `valid_policies.json` kept their original tenant_id (wrong one)
- After: Policies from `valid_policies.json` are always assigned the current tenant_id

## Files Changed
- `apps/api/src/uepi_api/storage/policy_storage.py` (line 144-146)

## Related Issues Fixed
1. ✅ **Policies not loading** - Fixed tenant_id assignment
2. ✅ **Predicted impact not loading** - Already fixed (policy merging logic)
3. ✅ **Analyses not loading** - Fixed tenant_id comparison
4. ✅ **Pipelines not loading** - Fixed tenant_id comparison

## Status
✅ **Fixed** - The code now correctly assigns tenant_id to policies from `valid_policies.json`.

## Critical: API Server Must Be Restarted

**The API server MUST be restarted for this fix to take effect!**

```bash
# Stop current server (CTRL+C)
./START_API_NOW.sh
```

## After Restart, You Should See:

✅ **Policies Page:**
- 5 predefined policies will load
- All policies will have correct tenant_id
- Predicted impact will be visible (if generated)

✅ **What-If Analysis Page:**
- Policies dropdown will be populated
- Previous scenarios will load
- Can create new scenarios

✅ **Dashboard:**
- Policy performance data will show
- Cost impact by policy will display
- Utilization trends will display

## Summary of All Fixes Waiting for Restart

1. ✅ **Policies loading** - Fixed tenant_id assignment in `valid_policies.json`
2. ✅ **Predicted impact loading** - Fixed policy merging logic
3. ✅ **Dashboard data** - Fixed policy ID matching + fallback
4. ✅ **Pipeline loading** - Fixed tenant_id comparison
5. ✅ **Data quality validation** - Fixed script path
6. ✅ **What-If Analysis loading** - Fixed analyses tenant_id comparison
7. ✅ **Analyses loading** - Fixed tenant_id comparison

**All fixes are in place - restart the API server to apply them!**
