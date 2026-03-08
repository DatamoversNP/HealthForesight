# Policy-Specific Baseline Creation Fix

## Problem
Policy-specific baselines were not being created (0/36) because baseline computation couldn't find matching data, even though policy-scoped data was generated.

## Root Cause
**Mismatch between data generation and baseline filtering**:
- **Data Generation**: Extracts procedure codes from `policy.logic.policy_levers[].targets`
- **Baseline Computation**: Only looked for codes in `policy_scope.get('procedure_codes')` (which was often empty)

## Solution Implemented

### 1. Updated `compute_policy_specific_baseline_from_database()`
- Added optional `policy` parameter to accept full policy object
- Imports and uses `extract_policy_target_codes()` from `policy_scoped_data_generation.py`
- Extracts codes from policy levers (same as data generation)
- Merges codes from both `policy_scope` and policy levers
- Uses merged codes for filtering claims

### 2. Updated Callers
- Updated `compute_baseline_metrics()` to accept and pass `policy` parameter
- Updated `refresh_baseline()` to get full policy object and pass it to baseline computation

### 3. Enhanced Logging
- Added diagnostic logging to show:
  - How many codes were extracted from levers
  - How many codes are being used for filtering
  - How many claims remain after each filter step

## Files Modified

1. **`apps/api/src/uepi_api/services/database_baseline_computation.py`**
   - Added import for `extract_policy_target_codes`
   - Updated function signature to accept `policy` parameter
   - Added code extraction from policy levers
   - Added code merging logic
   - Updated filtering to use merged codes
   - Added diagnostic logging

2. **`apps/api/src/uepi_api/baseline_refresh.py`**
   - Updated `compute_baseline_metrics()` signature to accept `policy` parameter
   - Updated calls to `compute_policy_specific_baseline_from_database()` to pass policy object
   - Updated `refresh_baseline()` to get and pass full policy object

## How It Works Now

1. **Data Generation** (unchanged):
   - Extracts codes from `policy.logic.policy_levers[].targets`
   - Generates claims with those codes

2. **Baseline Computation** (fixed):
   - Extracts codes from `policy.logic.policy_levers[].targets` (same as data generation)
   - Also checks `policy_scope` for codes
   - Merges both sources
   - Filters claims using merged codes
   - **Result**: Finds the same data that was generated!

## Testing

To test the fix:

1. **Restart API server** (if running):
   ```bash
   cd apps/api && python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Run baseline creation**:
   ```bash
   python3 scripts/generate_data_and_create_baselines_observations.py
   ```

3. **Expected Result**:
   - Policy-specific baselines should now be created
   - Check logs for diagnostic messages showing code extraction and filtering

## Expected Output

When creating policy-specific baselines, you should now see:
```
📋 Extracted codes from policy levers: X procedure codes, Y diagnosis codes
🔍 Using merged codes: X procedure codes, Y diagnosis codes, Z service categories
   Filtered by procedure codes: N claims remaining
   Filtered by diagnosis codes: M claims remaining
   Filtered by service categories: K claims remaining
✅ Found K claims matching policy scope for baseline computation
```

Instead of:
```
⚠️  No claims match policy filters for policy {policy_id}
```

## Next Steps

1. Test the fix with the workflow script
2. Verify policy-specific baselines are created
3. Check that observations can reference policy-specific baselines
4. Monitor logs for any issues

---

**Status**: ✅ Fix Implemented - Ready for Testing
