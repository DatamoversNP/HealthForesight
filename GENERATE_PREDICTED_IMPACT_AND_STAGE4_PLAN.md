# Generate Predicted Impact & Stage 4 Implementation Plan

## Overview
1. Generate predicted impact for all predefined/configured policies
2. Set up Stage 4: Synthetic data generation + Observed impact analysis with comparisons

## Step 1: Complete Configurations & Generate Predicted Impact

### Actions:
1. Use `POST /api/v1/policies/complete-configurations` to add missing configurations
2. Use `POST /api/v1/policies/generate-predicted-impact` to generate predicted impact for all policies

### Expected Result:
- All policies have complete configurations (levers, scope, conditions, exceptions)
- All policies have predicted impact generated (Stage 3.5)

## Step 2: Stage 4 - Synthetic Data Generation & Observed Impact Analysis

### What Stage 4 Needs:
1. **Synthetic Data Generation** (Post-Policy Implementation)
   - Generate claims data that reflects policy impact
   - Show behavioral changes (substitution, site shifts, utilization changes)
   - Use existing synthetic data generator (`scripts/synth/generate.py`) as base

2. **Observed Impact Analysis**
   - Run impact analysis on the synthetic post-policy data
   - Use existing `run_policy_impact_analysis` function
   - Compare against:
     - **Baseline** (Stage 3) - pre-policy metrics
     - **Predicted Impact** (Stage 3.5) - what we predicted
     - **Observed Impact** (Stage 4) - what actually happened

3. **Comparison Logic**
   - Prediction accuracy (predicted vs observed)
   - Baseline comparison (baseline vs observed)
   - Deviation analysis
   - Success/failure indicators

### Implementation Approach:
1. Enhance synthetic data generator to include policy-impact scenarios
2. Generate post-policy synthetic data
3. Run observed impact analysis
4. Compare observed vs predicted vs baseline
5. Display results with comparison metrics

## Next Steps:
1. Generate predicted impact for all policies (via API)
2. Enhance synthetic data generation for Stage 4 scenarios
3. Create Stage 4 analysis workflow
4. Implement comparison logic
5. Add UI for Stage 4 results
