# Stage 3.5 — Predicted Impact Implementation Summary

## Overview
Stage 3.5 generates predictive "expected impact" when a policy is created, BEFORE implementation. This is forward-looking and AI-driven.

## Implementation Status

### ✅ Completed

1. **Created `packages/common/src/uepi_common/analytics/predicted_impact.py`**
   - `PredictedImpactGenerator` class
   - Uses elasticity models and behavioral models
   - Predicts:
     - Utilization changes (per 1k, percentage)
     - Cost changes (PMPM, total)
     - Substitution effects
     - Provider response distribution (compliant/adaptive/resistant/circumvention)
     - Patient response signals (defer, substitute, ER fallback)

2. **Created `apps/api/src/uepi_api/routers/policy_predicted_impact.py`**
   - Helper functions for generating and storing predicted impact
   - Functions to store/retrieve predicted impact from policy metadata

3. **Integrated into Policy Creation**
   - Modified `create_policy` endpoint to generate predicted impact after policy creation
   - Stores predicted impact in `policy_metadata_json` (database mode) or policy file (file storage mode)
   - Works for both database and file storage modes

4. **Created Documentation**
   - `STAGE_3.5_IMPLEMENTATION.md` - Implementation details
   - `PRODUCT_FLOW_STAGES.md` - Clarifies distinction between Baseline, Predicted, and Observed impact

### ⏳ Pending

1. **Endpoint to Retrieve Predicted Impact**
   - Need to add: `GET /api/v1/policies/{policy_id}/predicted-impact`
   - This endpoint was started but the file was accidentally deleted
   - Should be added to `apps/api/src/uepi_api/routers/policies.py`

2. **Stage 4 Integration**
   - Update Stage 4 (observed impact) to compare against predicted impact
   - This will be done when implementing Stage 4

## Next Steps

1. Restore `apps/api/src/uepi_api/routers/policies.py` if needed (from git)
2. Add the predicted impact retrieval endpoint
3. Test predicted impact generation on policy creation
4. When implementing Stage 4, integrate comparison with predicted impact

## Files Created/Modified

- ✅ `packages/common/src/uepi_common/analytics/predicted_impact.py` (NEW)
- ✅ `apps/api/src/uepi_api/routers/policy_predicted_impact.py` (NEW)
- ✅ `STAGE_3.5_IMPLEMENTATION.md` (NEW)
- ✅ `PRODUCT_FLOW_STAGES.md` (NEW)
- ⚠️ `apps/api/src/uepi_api/routers/policies.py` (MODIFIED - but file was accidentally deleted, needs restoration)
