# Restore Policies and Predicted Impact

## Current Status

### Policies Found
- ✅ **5 policies** in `data/valid_policies.json` (UUID IDs: 10000000-...)
- ✅ **5 policies** in `apps/api/data/policies/` (String IDs: CS_UCC_004, PA_MRI_OP_001, etc.)
- ✅ **Total: 10 unique policies** across all locations

### Predicted Impact Status
- ⚠️ **No predicted_impact found** in policy files currently
- The predicted impact results may have been:
  1. Stored separately and need to be re-linked
  2. Lost during a previous migration
  3. Need to be regenerated

## Fixes Applied

### 1. Policy Loading ✅
- Updated `policy_storage.py` to check multiple locations:
  - `/tmp/policies_{tenant_id}.json`
  - `data/policies_{tenant_id}.json`
  - `data/valid_policies.json`
  - `apps/api/data/policies/` (NEW - where your preconfigured policies are)
  - Individual `data/policy_*.json` files

### 2. Tenant ID Fix ✅
- All policies now have `tenant_id` set to `00000000-0000-0000-0000-000000000001` (demo tenant)
- Policies will now load correctly

### 3. Predicted Impact Preservation ✅
- Updated `_save_to_file` to preserve `predicted_impact` when updating policies
- Predicted impact is preserved from existing policies when merging

### 4. String Policy ID Support ✅
- Updated `get_policy` to handle both UUID and string policy IDs

## Next Steps

### Option 1: Run Migration Script (Recommended)
```bash
./MIGRATE_ALL_POLICIES_AND_PREDICTED_IMPACT.sh
```

This will:
- Collect all 10 policies from all locations
- Set correct tenant_id
- Preserve any predicted_impact data
- Save to `/tmp/policies_{tenant_id}.json` for API to find

### Option 2: Just Restart API
The code now automatically finds policies in `apps/api/data/policies/`, so you can:
```bash
# Stop current API (CTRL+C)
./START_API_NOW.sh
```

Then refresh browser - all 10 policies should appear!

## Regenerating Predicted Impact

If predicted impact results are missing, you can regenerate them:

1. **Via UI**: Go to Policies page → Click "Generate Predicted Impact (All)"
2. **Via API**: `POST /api/v1/policies/generate-predicted-impact`

## Verification

After restarting, check:
- Policies page: http://localhost:3050/policies (should show 10 policies)
- API: http://localhost:8000/api/v1/policies (should return 10 policies)
- Check API logs for: `✅ Loaded X policies from apps/api/data/policies/`

## Policy Names You Should See

1. Outpatient MRI Prior Authorization (PA_MRI_OP_001)
2. Infusion Site-of-Care Optimization (SOC_INFUSION_002)
3. Physical Therapy Visit Limit (PT_FREQ_003)
4. Urgent Care Copay Increase (CS_UCC_004)
5. Advanced Imaging Control Bundle (COMPOUND_IMG_005)
6. Plus 5 more from valid_policies.json
