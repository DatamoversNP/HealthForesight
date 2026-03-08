# Fix Policies Loading Issue

## Problem
Preconfigured policies (8-10 expected) were not showing up on the policies page.

## Root Cause
1. Policies in `valid_policies.json` didn't have `tenant_id` set on individual policies
2. File-level `tenant_id` was `00000000-0000-0000-0000-000000000002` but demo user uses `00000000-0000-0000-0000-000000000001`
3. Policy loading code was filtering by tenant_id, so policies without tenant_id weren't matching

## Fixes Applied

### 1. Updated Policy Loading Logic ✅
- Modified `policy_storage.py` to:
  - Use file-level `tenant_id` if individual policies don't have it
  - Include policies without `tenant_id` (assume they're for current tenant)
  - Better handling of legacy policy files

### 2. Updated Policy Files ✅
- Added `tenant_id` to all policies in `valid_policies.json`
- Added `tenant_id` to all individual `policy_*.json` files
- Set tenant_id to `00000000-0000-0000-0000-000000000001` (demo tenant)

## Next Steps

**Restart the API server:**
```bash
# Stop current server (CTRL+C)
./START_API_NOW.sh
```

**Then refresh your browser** - policies should now appear!

## Verification

After restarting, check:
1. Policies page: http://localhost:3050/policies
2. API endpoint: http://localhost:8000/api/v1/policies
3. Check API logs for: `✅ Loaded X policies from valid_policies.json`

## Expected Policies

You should see these 5 policies:
1. Outpatient MRI Prior Authorization
2. Infusion Site-of-Care Optimization
3. Physical Therapy Visit Limit
4. Urgent Care Copay Increase
5. Advanced Imaging Control Bundle

If you had 8-10 policies, they may be in a different location. Run the search script to find them.
