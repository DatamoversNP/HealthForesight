# Product Flow Stages - Baseline, Predicted, and Observed Impact

## Stage 3 — Baseline Analysis
**Historical behavior and utilization PRIOR to policy implementation**

- Represents the historical baseline before any policy changes
- Measures utilization patterns, provider behavior, and patient behavior
- Used as a reference point for comparison
- Generated via baseline analysis engine

## Stage 3.5 — Predicted Impact (NEW)
**Forward-looking prediction generated when a policy is CREATED**

- Generated automatically when a policy is created (before implementation)
- Uses:
  - Elasticity models
  - Behavioral models
  - Provider compliance probabilities
  - Patient sensitivity
  - Substitution patterns
- AI-driven and forward-looking
- Stored with the policy for future comparison

## Stage 4 — Observed Impact
**Actual measured outcomes AFTER policy implementation**

- Measures what actually happened after policy changes
- Uses causal/statistical methods:
  - Difference-in-Differences (DiD)
  - Interrupted Time Series
  - Pre/Post analysis
- Explains outcomes via substitution and behavioral attribution
- **Compares observed outcomes against BOTH:**
  - Baseline (Stage 3)
  - Predicted impact (Stage 3.5)
- Enables learning, calibration, and confidence scoring

## Comparison and Learning

Stage 4 analysis compares observed outcomes against:
1. **Baseline (Stage 3)**: Historical reference point
   - Compares observed change from baseline utilization
   - Shows absolute and percentage change from historical baseline
2. **Predicted Impact (Stage 3.5)**: What we expected to happen
   - Compares observed effect size vs predicted effect size
   - Calculates prediction error (absolute and percentage)
   - Computes prediction accuracy score
   - Enables model calibration and learning

This comparison enables:
- Model calibration - improving prediction models based on observed accuracy
- Learning from prediction accuracy - understanding which predictions were accurate and why
- Confidence scoring improvements - adjusting confidence scores based on historical prediction accuracy
- Understanding of prediction errors - identifying systematic biases in predictions
- Better future predictions - using comparison data to improve Stage 3.5 predictions

### Comparison Results Structure

Stage 4 analysis results include a `comparisons` field with:
- `comparisons.predicted_impact`: Comparison with predicted impact (Stage 3.5)
  - `predicted_impact_available`: Boolean indicating if predicted impact was available
  - `predicted`: Predicted values (effect_size, percent_change)
  - `observed`: Observed values (effect_size, percent_change)
  - `prediction_error`: Error metrics (effect_size_error, percent_change_error, effect_size_error_pct)
  - `prediction_accuracy_pct`: Accuracy score (0-100, higher is better)
  - `within_predicted_range`: Whether observed is within predicted range
  - `prediction_confidence`: Confidence score from predicted impact
  
- `comparisons.baseline`: Comparison with baseline (Stage 3)
  - `baseline_available`: Boolean indicating if baseline was available
  - `baseline_utilization_per_1k`: Baseline utilization value
  - `observed_change_from_baseline`: Absolute change from baseline
  - `observed_change_from_baseline_pct`: Percentage change from baseline

## API Endpoints

- **Stage 3 (Baseline)**: `POST /api/v1/analyses/baseline`, `GET /api/v1/analyses/{analysis_id}/baseline`
- **Stage 3.5 (Predicted Impact)**: Generated automatically on policy creation, retrieved via `GET /api/v1/policies/{policy_id}/predicted-impact`
- **Stage 4 (Observed Impact)**: `POST /api/v1/analyses/impact`, `GET /api/v1/analyses/{analysis_id}/results`
