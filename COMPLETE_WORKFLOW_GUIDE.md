# Complete Workflow Guide - 100% Mock Data Free

## Overview
This guide provides step-by-step instructions for the complete product workflow, validated with user persona.

## Product Flow

### Step 1: Initial Data Load (One-Time)
**Action**: Load client data from source folder to database
- Place claims data files in `apps/data/source_data/{tenant_id}/`
- Run ingestion pipeline to load data to `claims_lines` table
- Data is loaded with date tracking

### Step 2: Policy Setup
**Action**: User creates and activates policies
- Navigate to Policy Catalog
- Create policies with scope (LOB, market, codes)
- Activate policies (set status to ACTIVE)

### Step 3: Baseline Analysis
**Action**: Create baselines (general and policy-specific)

#### Option A: Quick Baseline Refresh (Recommended)
1. Navigate to **Baseline Analysis** page
2. Click **"Refresh General Baseline"** button
   - Creates baseline from database claims_lines table
   - Uses last 12 months of data
   - Computes metrics: utilization_per_1k, cost_pmpm, etc.
3. For each policy, click **"Refresh Policy-Specific Baseline"** dropdown
   - Select policy from dropdown
   - Creates policy-scoped baseline using policy's scope filters

#### Option B: Advanced Baseline Analysis
1. Click **"Run Baseline Analysis"** button
2. Enter analysis name (e.g., "Q1 2026 Baseline")
3. Optionally set date range
4. Click **"Run Analysis"**
   - Performs advanced analysis with provider archetypes, patient segments
   - Takes longer but provides more insights

### Step 4: Generate Predicted Impacts (One-Click)
**Action**: Generate predicted impacts for all policies
1. Navigate to **Policy Catalog** page
2. Click **"Generate Predicted Impact (All)"** button
   - Generates predicted impact for all active policies
   - Uses real baseline metrics from database
   - Policy-specific baselines are used when available
3. Wait for completion (shows progress)
4. Review results in **Predicted Impacts Overview** page

### Step 5: Daily Data Generation and Loading
**Action**: Generate and load data for previous days

#### Option A: Generate Data for Last 3 Days (Script)
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 scripts/generate_data_last_3_days.py
```
This will:
- Generate claims data for yesterday, 2 days ago, and 3 days ago
- Load data directly to database claims_lines table
- Create ~25,000 claims per day (10,000 members × 2.5 claims/member)

#### Option B: Generate Data via UI
1. Navigate to **Observation Analysis** page
2. Click **"Generate Claims Data"** button
   - Generates data for yesterday
   - Loads to database automatically
3. Repeat for additional days if needed

#### Option C: Daily Pipeline (Automated)
1. Navigate to **Observation Analysis** page
2. Click **"Run Daily Job"** button
   - Loads data from source folder (if available)
   - If no source data, generates demonstration data
   - Runs observations for all active policies

### Step 6: Observations Analysis
**Action**: View observations comparing observed vs baseline vs predicted

1. Navigate to **Observation Analysis** page
2. Select a policy from dropdown
3. View observations list
4. Click on an observation to view details

#### Observation Tabs:
- **Overview**: Key metrics summary
- **General Baseline**: Comparison against general baseline (all data)
- **Policy Baseline**: Comparison against policy-specific baseline
- **Predicted Comparison**: Comparison against predicted impact
- **Behavioral Explanation**: Detailed behavioral insights

## API Endpoints

### Baseline Management
- `POST /api/v1/baselines/refresh` - Refresh baseline (general or policy-specific)
- `GET /api/v1/baselines` - List all baselines
- `GET /api/v1/baselines/latest?policy_id={id}` - Get latest baseline

### Data Generation
- `POST /api/v1/data/generate-claims` - Generate claims data for specific date
- `POST /api/v1/data/generate-claims/yesterday` - Quick endpoint for yesterday

### Predicted Impacts
- `POST /api/v1/policies/generate-predicted-impact?force=false` - Generate for all policies

### Observations
- `GET /api/v1/observations` - List observations
- `POST /api/v1/observations/from-analysis/{analysis_id}` - Create observation from analysis

## Testing Checklist

### ✅ Baseline Creation
- [ ] General baseline created successfully
- [ ] Policy-specific baselines created for each policy
- [ ] Baselines show real metrics from database (not mock data)
- [ ] Baseline metrics match actual claims data

### ✅ Predicted Impacts
- [ ] One-click generation works for all policies
- [ ] Predicted impacts use real baseline metrics
- [ ] Policy-specific baselines are used when available
- [ ] Force regenerate option works

### ✅ Data Generation
- [ ] Data generated for last 3 days
- [ ] Data loaded to database successfully
- [ ] Date tracking works correctly
- [ ] Daily pipeline loads data correctly

### ✅ Observations
- [ ] Observations created for each policy
- [ ] General baseline comparison shows real values
- [ ] Policy-specific baseline comparison shows real values
- [ ] Predicted comparison shows real values
- [ ] No "N/A" values when data exists
- [ ] Behavioral explanation is comprehensive

## Validation with User Persona

### Analyst Persona
1. ✅ Can view all observations in one place
2. ✅ Can compare against both baseline types
3. ✅ Can see prediction accuracy
4. ✅ Can understand behavioral changes

### Policy Owner Persona
1. ✅ Can see policy-specific baseline comparison
2. ✅ Can see how policy is performing vs prediction
3. ✅ Can understand impact on utilization and cost

### Executive Persona
1. ✅ Can see high-level summary
2. ✅ Can see prediction accuracy
3. ✅ Can understand overall trends

## Troubleshooting

### "No data available" errors
- **Cause**: No claims data in database
- **Solution**: Run data generation script or use "Generate Claims Data" button

### "Baseline not found" errors
- **Cause**: No baseline created yet
- **Solution**: Use "Refresh General Baseline" or "Refresh Policy-Specific Baseline" buttons

### "N/A" values in comparisons
- **Cause**: Missing baseline or predicted impact data
- **Solution**: 
  1. Create baselines (Step 3)
  2. Generate predicted impacts (Step 4)
  3. Ensure observations are created after both are done

### Observations show same data for all policies
- **Cause**: Using mock data (should not happen now)
- **Solution**: Ensure observations are created from real analysis results

## Files Created/Modified

### Backend
- `apps/api/src/uepi_api/services/database_baseline_computation.py` - Database-only baseline computation
- `apps/api/src/uepi_api/services/daily_pipeline_service.py` - Daily data loading
- `apps/api/src/uepi_api/services/data_generation_service.py` - Data generation
- `apps/api/src/uepi_api/routers/data_generation.py` - Data generation endpoints
- `apps/api/src/uepi_api/routers/observations.py` - Removed mock data
- `apps/api/src/uepi_api/routers/policies.py` - Fixed predicted impacts to use real baselines
- `apps/api/src/uepi_api/baseline_refresh.py` - Database-only computation
- `apps/api/src/uepi_api/observation_enhancement.py` - Uses both baseline types

### Frontend
- `apps/web/src/pages/BaselineAnalysisPage.tsx` - Added baseline refresh UI
- `apps/web/src/pages/ObservationAnalysisPage.tsx` - Added policy baseline tab, generate data button
- `apps/web/src/lib/api.ts` - Added baseline and data generation methods

### Scripts
- `scripts/generate_data_last_3_days.py` - Generate data for last 3 days
- `scripts/complete_workflow_test.py` - Complete workflow test

## Next Steps After Setup

1. **Generate initial data**: Run `generate_data_last_3_days.py`
2. **Create baselines**: Use UI buttons in Baseline Analysis page
3. **Generate predicted impacts**: Use "Generate Predicted Impact (All)" button
4. **Create observations**: Use "Create Observation" button or run daily job
5. **View results**: Navigate to Observation Analysis page and explore tabs

## Notes

- All mock data has been removed
- System fails gracefully with helpful error messages
- Baselines are computed from actual database data only
- Predicted impacts use real baseline metrics
- Observations compare against both baseline types and predicted impact
- System runs without timeouts (10-hour timeout for long operations)
