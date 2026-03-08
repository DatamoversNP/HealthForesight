# Stage 3.5 — Predicted Impact Implementation

## Overview
Stage 3.5 generates predictive "expected impact" when a policy is created, BEFORE implementation. This is forward-looking and AI-driven, using:
- Elasticity models
- Behavioral models  
- Provider compliance probabilities
- Patient sensitivity
- Substitution patterns

## Distinction from Other Stages

- **Stage 3 (Baseline)**: Historical behavior and utilization PRIOR to policy
- **Stage 3.5 (Predicted Impact)**: Forward-looking prediction of expected impact when policy is CREATED
- **Stage 4 (Observed Impact)**: Actual measured outcomes AFTER implementation

Stage 4 compares observed outcomes against BOTH baseline (Stage 3) and predicted impact (Stage 3.5) for learning and calibration.

## Implementation

### 1. Created `packages/common/src/uepi_common/analytics/predicted_impact.py`
   - `PredictedImpactGenerator` class
   - Uses elasticity models and behavioral models
   - Predicts:
     - Utilization changes (per 1k, percentage)
     - Cost changes (PMPM, total)
     - Substitution effects
     - Provider response distribution (compliant/adaptive/resistant/circumvention)
     - Patient response signals (defer, substitute, ER fallback)

### 2. Integration
   - ✅ Integrated into policy creation endpoint
   - ✅ Store predicted impact with policy (in policy_metadata_json)
   - ✅ Create endpoint to retrieve predicted impact (`GET /api/v1/policies/{policy_id}/predicted-impact`)
   - ✅ Update Stage 4 to compare against predictions (implemented in `run_policy_impact_analysis`)
   - ✅ Update documentation

### 3. Stage 4 Comparison Implementation
Stage 4 impact analysis (`apps/worker/src/uepi_worker/impact_analysis.py`) now compares observed outcomes against:
- **Baseline (Stage 3)**: Historical reference point - compares observed change from baseline
- **Predicted Impact (Stage 3.5)**: Expected outcomes - compares observed vs predicted with accuracy metrics

The comparison results are included in the Stage 4 analysis response under the `comparisons` field:
- `comparisons.predicted_impact`: Comparison with predicted impact including prediction error and accuracy
- `comparisons.baseline`: Comparison with baseline metrics
