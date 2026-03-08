# Predicted Impact Alignment with Policy Activation Logic - Fixed

## Issue Found

The predicted impact generation was **NOT** using policy-specific baselines in some code paths, which means:
1. It was using general baselines instead of policy-scoped baselines
2. It wasn't leveraging the activation date logic we implemented for baselines
3. Predictions weren't as accurate as they could be

## Fixes Applied

### 1. ✅ Single Policy Predicted Impact (`apps/api/src/uepi_api/routers/policies.py`)

**Before:**
```python
baseline = get_latest_baseline(current_user.tenant_id)  # General baseline only
```

**After:**
```python
# Try policy-specific baseline first (uses historical data before activation)
baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy_id)
if not baseline:
    # Fall back to general baseline if no policy-specific baseline exists
    baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
```

**Benefits:**
- Uses policy-specific baseline when available (filtered by policy scope)
- Falls back to general baseline if policy-specific doesn't exist
- Automatically uses historical data before activation (because baselines are computed that way)

### 2. ✅ File-Based Policy Predicted Impact (`apps/api/src/uepi_api/routers/policies_file.py`)

**Before:**
```python
latest_baseline = get_latest_baseline(current_user.tenant_id)  # General baseline only
```

**After:**
```python
# Try policy-specific baseline first
if policy_id_uuid:
    latest_baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy_id_uuid)

# Fall back to general baseline if no policy-specific baseline exists
if not latest_baseline:
    latest_baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
```

**Benefits:**
- Same as above - uses policy-specific baseline when available
- Properly maps policy-specific metrics (`util_rate_target_per_1000_mm`) vs general metrics (`util_rate_total_per_1000_mm`)

### 3. ✅ Batch Predicted Impact Generation (Already Correct)

The `generate_all_policies_predicted_impact` function (line 827) was already correctly using policy-specific baselines:
```python
# Try policy-specific baseline first
policy_baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy.id)
if not policy_baseline:
    # Fallback to general baseline
    policy_baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
```

## How It Works Now

1. **Baseline Selection Priority:**
   - First: Policy-specific baseline (if exists) - uses historical data before activation, filtered by policy scope
   - Second: General baseline (if no policy-specific exists) - uses historical data before activation

2. **Activation Date Logic:**
   - Baselines are computed to end BEFORE policy activation (we fixed this earlier)
   - Predicted impact now uses these baselines, so it automatically uses historical data before activation
   - No additional activation date logic needed in predicted impact generation

3. **Policy Scope Filtering:**
   - Policy-specific baselines are filtered by policy scope (LOB, markets, codes)
   - Predicted impact uses these scoped baselines, making predictions more accurate

## Verification

To verify predicted impact is using policy-specific baselines:

1. **Check baseline exists:**
   ```bash
   curl http://localhost:8000/api/v1/baselines?policy_id=<policy_id>
   ```

2. **Generate predicted impact:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/policies/<policy_id>/predicted-impact
   ```

3. **Verify it uses policy-specific baseline:**
   - Check API logs for "Using policy-specific baseline" messages
   - Verify predicted impact metrics align with policy scope

## Summary

✅ **Predicted impact now:**
- Uses policy-specific baselines when available
- Falls back to general baselines if needed
- Automatically uses historical data before activation (via baseline logic)
- Uses policy-scoped metrics for more accurate predictions

✅ **All aligned with baseline logic:**
- Historical data only (before activation) ✅
- Policy-specific filtering ✅
- Activation date awareness ✅
