# Product Flow Steps 6-9 Implementation Plan

## Current Status Assessment

### ✅ What We Have:
- **Step 6 (Post-implementation observation)**: 
  - ✅ Daily job for data generation and ingestion
  - ✅ Observation creation from impact analysis
  - ✅ Baseline vs Observed comparison
  - ✅ Predicted vs Observed comparison
  - ✅ Behavioral explanation with M17-M19 metrics

- **Step 7 (Learning loop)**:
  - ✅ Learning endpoints (`/learning/*`)
  - ✅ Elasticity model storage
  - ✅ Accuracy tracking (`record_prediction_accuracy`, `get_prediction_accuracy_summary`)
  - ✅ Learning from observations (`learn_from_observation`, `update_elasticity_from_observations`)
  - ⚠️ **Gap**: Automatic learning trigger when observations are created

- **Step 8 (What-if scenarios)**:
  - ✅ Simulation analysis endpoint (`/analyses/simulate`)
  - ⚠️ **Gap**: May not use latest elasticity models
  - ⚠️ **Gap**: May not show tradeoffs and risks clearly

- **Step 9 (Continuous cycle)**:
  - ✅ Daily job infrastructure
  - ⚠️ **Gap**: Automatic learning updates when new observations available
  - ⚠️ **Gap**: Automatic prediction regeneration when models update

### Key Principles Status:
- ✅ **Baseline/Predicted/Observed separation**: Structure exists in UI
- ✅ **Traceability**: Traceability framework exists
- ⚠️ **Refresh indicators**: RefreshIndicator component exists but may need enhancement
- ⚠️ **Clear separation in UI**: May need visual improvements

## Implementation Tasks

### Task 1: Automatic Learning Trigger (Step 7 Enhancement)
**Goal**: Automatically trigger learning when observations are created

**Changes Needed**:
1. **`observation_enhancement.py`**:
   - After creating observation, automatically call `learn_from_observation`
   - Record prediction accuracy automatically

2. **`daily_jobs.py`**:
   - After creating observations, trigger learning updates
   - Check if enough observations for elasticity model update

**Files to Modify**:
- `apps/api/src/uepi_api/observation_enhancement.py` - Add automatic learning trigger
- `apps/api/src/uepi_api/routers/daily_jobs.py` - Add learning trigger after observation creation

### Task 2: What-If Scenarios with Latest Learning (Step 8 Enhancement)
**Goal**: Ensure what-if scenarios use latest elasticity models and show tradeoffs

**Changes Needed**:
1. **`policy_predicted_impact.py`**:
   - Update `generate_predicted_impact_for_policy` to use latest elasticity model
   - If no elasticity model, use default coefficients

2. **`analyses_file.py`** (simulate endpoint):
   - Use latest elasticity model for simulations
   - Add tradeoff analysis (cost vs utilization)
   - Add risk indicators (confidence intervals, worst-case scenarios)

**Files to Modify**:
- `apps/api/src/uepi_api/routers/policy_predicted_impact.py` - Use latest elasticity models
- `apps/api/src/uepi_api/routers/analyses_file.py` - Enhance simulate endpoint

### Task 3: Continuous Learning Cycle (Step 9)
**Goal**: Automatically update predictions when elasticity models improve

**Changes Needed**:
1. **`learning_loop.py`**:
   - After elasticity model update, identify affected policies
   - Mark policies with "stale predictions" when models update

2. **`policies_file.py`**:
   - Add endpoint to regenerate predicted impact for policies with stale predictions
   - Add indicator in policy metadata: `prediction_based_on_model_version`

**Files to Modify**:
- `apps/api/src/uepi_api/learning_loop.py` - Add policy update trigger
- `apps/api/src/uepi_api/routers/policies_file.py` - Add stale prediction handling

### Task 4: Enhanced Refresh Indicators (Key Principle)
**Goal**: Make it obvious when insights refresh due to new data or policy changes

**Changes Needed**:
1. **UI Components**:
   - Enhance `RefreshIndicator` to show:
     - Last refresh timestamp
     - Reason for refresh (new data, policy change, model update)
     - Staleness indicator (if data/model is old)

2. **Refresh Reasons**:
   - `NEW_DATA_INGESTED`: New data period created
   - `BASELINE_REFRESHED`: Baseline analysis re-run
   - `POLICY_UPDATED`: Policy version changed
   - `MODEL_UPDATED`: Elasticity model updated
   - `OBSERVATION_ADDED`: New observation available

**Files to Modify**:
- `apps/web/src/components/common/RefreshIndicator.tsx` - Enhance with reasons
- `apps/api/src/uepi_api/storage_baselines.py` - Store refresh reasons
- `apps/api/src/uepi_api/storage_policies.py` - Store refresh reasons
- `apps/api/src/uepi_api/storage_learning.py` - Store refresh reasons

### Task 5: Clear Separation of Baseline/Predicted/Observed (Key Principle)
**Goal**: Make separation obvious in UI

**Changes Needed**:
1. **Observation Analysis Page**:
   - Add visual tabs/cards for Baseline, Predicted, Observed
   - Show clear labels: "Baseline Period: Jan 2024 - Dec 2025", "Predicted Impact (v1.2)", "Observed Impact (Jan 2026)"
   - Add comparison matrix showing all three side-by-side

2. **Policy Pages**:
   - Separate sections for Baseline Metrics, Predicted Impact, Observed Impact
   - Clear time-based labels

**Files to Modify**:
- `apps/web/src/pages/ObservationAnalysisPage.tsx` - Enhanced separation
- `apps/web/src/pages/PolicyCatalogPage.tsx` - Enhanced sections

### Task 6: Traceability Display Enhancement (Key Principle)
**Goal**: Make traceability obvious and easy to explore

**Changes Needed**:
1. **TraceabilityDisplay Component**:
   - Show data period links clearly
   - Show policy version links
   - Show baseline version links
   - Show elasticity model version used for predictions

2. **Drill-down**:
   - Click data period → See data period details
   - Click policy version → See policy version diff
   - Click baseline version → See baseline metrics

**Files to Modify**:
- `apps/web/src/components/common/TraceabilityDisplay.tsx` - Enhanced display

## Implementation Priority

### Phase 1 (High Priority - Core Loop):
1. Task 1: Automatic Learning Trigger
2. Task 4: Enhanced Refresh Indicators

### Phase 2 (Medium Priority - User Experience):
3. Task 5: Clear Separation of Baseline/Predicted/Observed
4. Task 2: What-If Scenarios with Latest Learning

### Phase 3 (Lower Priority - Advanced Features):
5. Task 3: Continuous Learning Cycle (automatic prediction updates)
6. Task 6: Traceability Display Enhancement

## Success Criteria

- [ ] When observation is created, prediction accuracy is automatically recorded
- [ ] When enough observations exist, elasticity model is automatically updated
- [ ] What-if scenarios use latest elasticity models
- [ ] Refresh indicators clearly show why data refreshed
- [ ] Baseline, Predicted, Observed are clearly separated in UI
- [ ] All insights are traceable to data period and policy version
- [ ] Users can see when insights are stale or need refresh
