# Comprehensive Refactoring Plan - Mock Data Free Product

## Overview
Complete refactoring to remove all mock data and ensure product works with real database data only.

## Key Requirements

1. **100% Mock Data Free** - Show "data doesn't exist" instead of mock values
2. **Two Baseline Types**:
   - General baseline (across all data)
   - Policy-specific baseline (for observations comparison)
3. **Baselines from Database Only** - Compute from actual claims_lines table data
4. **Daily Data Loading** - Pipeline loads from source folders to database daily
5. **Real Predicted Impacts** - Policy-specific, based on actual data
6. **Data Generation Button** - Generate claims data for previous day (demo purposes)
7. **Product Flow**:
   - One-time load: Client data from source folder → database
   - User sets up policies
   - Baseline analysis: General + policy-specific
   - One-click: Generate predicted impacts for all policies
   - Daily: New data → daily pipeline → database
   - Observations: Compare against both baselines + predicted impact
8. **No Timeouts** - System runs without user interaction

## Implementation Steps

### Phase 1: Remove Mock Data (CRITICAL)
- [x] Remove mock data from observations.py
- [ ] Remove mock data from baseline computation
- [ ] Remove mock data from predicted impacts
- [ ] Update all endpoints to return null/empty instead of mock

### Phase 2: Fix Baseline Computation
- [ ] Create database-only baseline computation
- [ ] Implement general baseline (all data)
- [ ] Implement policy-specific baseline
- [ ] Update baseline refresh to use database

### Phase 3: Daily Pipeline System
- [ ] Create daily data loading pipeline
- [ ] Add date tracking to claims_lines
- [ ] Create pipeline scheduler
- [ ] Add pipeline monitoring

### Phase 4: Data Generation
- [ ] Create data generation endpoint
- [ ] Add UI button for data generation
- [ ] Generate data for previous day

### Phase 5: Fix Observations
- [ ] Update observations to use real baselines
- [ ] Fix comparisons (general + policy-specific)
- [ ] Remove mock behavioral explanations

### Phase 6: Remove Timeouts
- [ ] Increase all timeouts
- [ ] Add retry logic
- [ ] Ensure long-running operations complete

## Files to Modify

1. `apps/api/src/uepi_api/routers/observations.py` - Remove mock data
2. `apps/api/src/uepi_api/baseline_refresh.py` - Use database only
3. `apps/api/src/uepi_api/baseline_metrics_computation.py` - Database computation
4. `apps/api/src/uepi_api/routers/daily_jobs.py` - Daily pipeline
5. `apps/api/src/uepi_api/routers/policy_predicted_impact.py` - Real predictions
6. New: `apps/api/src/uepi_api/services/data_generator.py` - Data generation
7. New: `apps/api/src/uepi_api/services/daily_pipeline.py` - Daily loading
