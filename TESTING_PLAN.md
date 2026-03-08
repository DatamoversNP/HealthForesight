# Extensive Testing Plan - All Phases

## Testing Strategy

This document outlines comprehensive testing for all phases of the continuous system implementation.

## Test Environment Setup

1. **Start API Server**
   ```bash
   ./setup-venv-and-start-api.sh
   # OR
   ./restart-api.sh
   ```

2. **Start Web Server** (if needed)
   ```bash
   cd apps/web
   npm run dev
   ```

3. **Verify Services**
   - API: http://localhost:8000/docs
   - Web: http://localhost:5173 (or configured port)

## Phase 1: Data Periods & Policy Versions

### Test 1.1: Data Period Creation from Ingestion
**Steps**:
1. Upload a claims file via `/api/v1/ingestions/upload`
2. Wait for ingestion to complete
3. Verify data period was created:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/periods
   ```
4. Verify baseline eligibility was determined correctly

**Expected**: Data period created with correct dates and baseline eligibility

### Test 1.2: Policy Version Creation
**Steps**:
1. Create a new policy via `/api/v1/policies`
2. Verify initial version was created:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/policies/{policy_id}/versions
   ```
3. Update the policy
4. Verify new version was created

**Expected**: Version 1 created on policy creation, new version on update

### Test 1.3: Data Period Querying
**Steps**:
1. List all data periods
2. Get baseline-eligible periods
3. Get latest baseline-eligible period
4. Filter by date range

**Expected**: Correct filtering and sorting

## Phase 2: Baseline Refresh System

### Test 2.1: Automatic Baseline Refresh
**Steps**:
1. Create baseline-eligible data period (via ingestion)
2. Verify baseline was automatically created/refreshed
3. Check baseline version number
4. Verify baseline metrics

**Expected**: Baseline automatically refreshed with new version

### Test 2.2: Baseline Shift Detection
**Steps**:
1. Create first baseline
2. Create second baseline with different metrics
3. Check shift detection:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/baselines/{baseline_id}/shift
   ```
4. Verify shift summary

**Expected**: Shift detected if >5% change in metrics

### Test 2.3: Manual Baseline Refresh
**Steps**:
1. Manually trigger baseline refresh:
   ```bash
   curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"baseline_type": "ROLLING", "window_months": 12, "refresh_reason": "MANUAL"}' \
     http://localhost:8000/api/v1/baselines/refresh
   ```
2. Verify new baseline version created
3. Check refresh reason is "MANUAL"

**Expected**: Baseline refreshed with correct parameters

## Phase 3: Observed Impact Tracking

### Test 3.1: Observation Creation
**Steps**:
1. Create an observation manually:
   ```bash
   curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_id": "<policy_id>",
       "analysis_id": "<analysis_id>",
       "metrics": {"observed_effect_size": -15.2, "utilization_per_1k": 110.3},
       "comparisons": {"vs_baseline": {}, "vs_predicted": {}}
     }' \
     http://localhost:8000/api/v1/observations
   ```
2. Verify observation was created
3. Verify learning was triggered (check accuracy record)

**Expected**: Observation created, accuracy record created, learning triggered

### Test 3.2: Observation Comparison Enhancement
**Steps**:
1. Create observation with baseline and predicted data
2. Verify comparisons were enhanced:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/observations/{observation_id}/comparison
   ```
3. Check baseline comparison
4. Check predicted comparison

**Expected**: Comparisons show change from baseline and prediction accuracy

### Test 3.3: Multi-Period Observation Tracking
**Steps**:
1. Create observations for multiple data periods
2. Query observations by policy:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/policies/{policy_id}/observations
   ```
3. Query observations by data period:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/periods/{period_id}/observations
   ```

**Expected**: Observations linked to periods and policies correctly

## Phase 4: Learning Loop System

### Test 4.1: Learning from Observation
**Steps**:
1. Create observation with predicted comparison
2. Verify accuracy record was created:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/learning/accuracy/{policy_id}
   ```
3. Create 3+ observations for same policy
4. Verify elasticity model was created/updated:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/learning/elasticity-models
   ```

**Expected**: Accuracy recorded, elasticity model created after 3 observations

### Test 4.2: Accuracy Tracking
**Steps**:
1. Create multiple observations with predictions
2. Get accuracy history:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/learning/accuracy/history/{policy_id}
   ```
3. Verify accuracy metrics (MAE, RMSE, accuracy %)

**Expected**: Accurate metrics calculated and stored

### Test 4.3: Elasticity Model Updates
**Steps**:
1. Create elasticity model
2. Add more observations
3. Verify model was updated with new coefficients
4. Check version increment
5. Verify confidence increased

**Expected**: Model updated, version incremented, confidence increased

## Phase 5: Integration & UI

### Test 5.1: Refresh Indicators
**Steps**:
1. Open Policy Catalog page
2. Verify refresh indicators show in policy table
3. Click refresh icon to refresh predicted impact
4. Verify indicator updates

**Expected**: Refresh indicators display correctly, refresh works

### Test 5.2: Traceability Display
**Steps**:
1. Open predicted impact dialog
2. Click "Traceability" tab
3. Verify traceability links are displayed
4. Check links show correct IDs

**Expected**: Traceability links displayed correctly

### Test 5.3: Learning Metrics Dashboard
**Steps**:
1. Open predicted impact dialog
2. Click "Learning Metrics" tab
3. Verify accuracy summary displays
4. Check accuracy history table
5. Verify elasticity models table

**Expected**: All metrics display correctly

### Test 5.4: End-to-End Workflow
**Steps**:
1. Upload data (creates data period)
2. Create policy (creates version)
3. Baseline auto-refreshes (if baseline-eligible)
4. Generate predicted impact
5. Create observation from analysis
6. Learning triggered automatically
7. View in UI with all Phase 5 features

**Expected**: Complete workflow functions end-to-end

## Automated Test Scripts

Create test scripts for:
1. API endpoint testing (using curl or Python requests)
2. UI component testing (using Playwright or Cypress)
3. Integration testing (end-to-end workflows)

## Test Data Requirements

1. **Sample Policies**: At least 5 policies (mix of standalone and composite)
2. **Sample Data Periods**: At least 3 baseline-eligible periods
3. **Sample Observations**: At least 5 observations for testing learning
4. **Sample Baselines**: Multiple baseline versions for shift testing

## Success Criteria

- ✅ All Phase 1 endpoints work correctly
- ✅ All Phase 2 endpoints work correctly
- ✅ All Phase 3 endpoints work correctly
- ✅ All Phase 4 endpoints work correctly
- ✅ All Phase 5 endpoints work correctly
- ✅ UI components render without errors
- ✅ Refresh indicators work correctly
- ✅ Traceability display shows correct data
- ✅ Learning metrics display correctly
- ✅ End-to-end workflows complete successfully

## Bug Reporting

Document any issues found during testing:
1. Endpoint that fails
2. Expected vs actual behavior
3. Error messages/logs
4. Steps to reproduce
