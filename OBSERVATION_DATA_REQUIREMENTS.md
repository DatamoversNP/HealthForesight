# Observation Data Requirements

## The Problem

Observations are showing "N/A" for observed values because they're not being computed from actual claims data.

## Expected Flow

```
Daily Claims Data → Data Ingestion → Impact Analysis → Observations
     ↓                    ↓                ↓                ↓
  Claims arrive      Load to TDM      Compute metrics   Create observation
  after policy       (Parquet/CSV)    from actual      with observed values
  goes live                            claims data
```

## What's Needed for Meaningful Observations

### 1. **Claims Data Must Exist**

Claims data needs to be loaded into the target data model:
- Location: `apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/claims_lines.csv`
- Or: Parquet files in partitioned structure
- Must contain post-policy claims (after policy effective date)

**Check if data exists:**
```bash
ls -lh apps/data/target_data_model/00000000-0000-0000-0000-000000000001/CLAIMS_LINES/
```

### 2. **Impact Analyses Must Run on Actual Data**

Impact analyses need to:
- Load claims data from the target data model
- Filter to post-policy period (after policy effective date)
- Compute `treatment_post` metrics from actual claims:
  - `utilization_per_1k` = (total_claims / member_count) * 1000
  - `allowed_pmpm` = total_allowed / member_months
  - `paid_pmpm` = total_paid / member_months

**Check analysis results:**
```bash
# Look for analysis result files
find apps/api/src/data/analyses -name "*.json" | head -5
# Check if they have treatment_post metrics
```

### 3. **Observations Must Be Created from Analyses**

When creating observations:
- Extract `treatment_post` metrics from analysis result
- These become the "observed" values in the observation
- Compare against baseline and predicted values

**Current code path:**
- `extract_metrics_from_analysis_result()` in `observation_enhancement.py`
- Looks for: `analysis_result["metrics"]["treatment_post"]`
- Extracts: `utilization_per_1k`, `paid_pmpm`, `allowed_pmpm`

## How to Get Meaningful Data

### Option 1: Run Daily Job (Recommended)

The daily job should:
1. Generate/load post-policy claims data
2. Ingest data into target data model
3. Run impact analyses on actual data
4. Create observations from analyses

```bash
# Trigger daily job via API
curl -X POST http://localhost:8000/api/v1/jobs/daily-data-and-observations \
  -H 'Authorization: Bearer dev-token-123' \
  -H 'Content-Type: application/json' \
  -d '{"target_date": "2024-12-15", "run_observations": true}'
```

### Option 2: Manual Process

1. **Load claims data:**
   ```bash
   # Generate post-policy data
   python scripts/daily_post_policy_job.py --date 2024-12-15
   ```

2. **Run impact analysis:**
   ```bash
   # For each policy, run impact analysis
   curl -X POST http://localhost:8000/api/v1/analyses/impact \
     -H 'Authorization: Bearer dev-token-123' \
     -H 'Content-Type: application/json' \
     -d '{
       "policy_id": "policy-uuid",
       "treatment_filters": {...},
       "pre_window_months": 6,
       "post_window_months": 6
     }'
   ```

3. **Create observations:**
   ```bash
   # Create observation from analysis
   curl -X POST "http://localhost:8000/api/v1/observations/from-analysis/{analysis_id}?policy_id={policy_id}" \
     -H 'Authorization: Bearer dev-token-123'
   ```

## Diagnostic Script

Run the diagnostic script to check current state:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python scripts/diagnose_observation_data.py
```

This will check:
1. ✅ If claims data exists
2. ✅ If analyses have `treatment_post` metrics
3. ✅ If observations have observed values

## Key Code Locations

### Where Metrics Are Extracted
- **File:** `apps/api/src/uepi_api/observation_enhancement.py`
- **Function:** `extract_metrics_from_analysis_result()`
- **Lines:** 13-56
- **Key:** Looks for `analysis_result["metrics"]["treatment_post"]`

### Where Impact Analysis Computes Metrics
- **File:** `apps/api/src/uepi_api/routers/analyses_file.py`
- **Function:** `compute_pre_post_metrics()`
- **Lines:** 23-80
- **Key:** Computes `treatment_post` metrics from actual claims DataFrame

### Where Claims Data Is Loaded
- **File:** `packages/common/src/uepi_common/analytics/impact.py`
- **Class:** `ImpactAnalysisEngine`
- **Method:** `_load_data()`
- **Key:** Loads claims from Parquet/CSV files in target data model

## Expected Data Structure

### Analysis Result Should Have:
```json
{
  "metrics": {
    "treatment_post": {
      "utilization_per_1k": 130.5,
      "allowed_pmpm": 45.23,
      "paid_pmpm": 42.10,
      "total_claims": 1250,
      "total_allowed": 54276.0,
      "total_paid": 50520.0
    },
    "treatment_pre": {...}
  },
  "impact_estimate": {
    "effect_size": -18.5,
    "percent_change": -14.2
  }
}
```

### Observation Should Have:
```json
{
  "metrics": {
    "utilization_per_1k": 130.5,  // From treatment_post
    "cost_pmpm": 45.23,           // From treatment_post.allowed_pmpm
    "observed_effect_size": -18.5,
    "observed_percent_change": -14.2
  },
  "comparisons": {
    "vs_baseline": {
      "baseline_utilization_per_1k": 152.0,
      "observed_utilization_per_1k": 130.5,  // From metrics
      "utilization_change": -21.5,
      "utilization_change_pct": -14.1
    },
    "vs_predicted": {
      "predicted_utilization": 140.0,
      "observed_utilization": 130.5,  // From metrics
      "utilization_prediction_error": -9.5
    }
  }
}
```

## Next Steps

1. **Run diagnostic script** to identify what's missing
2. **If no claims data:** Run daily job or load data manually
3. **If no analyses:** Run impact analyses on policies
4. **If analyses have no data:** Check that claims data exists and is being loaded correctly
5. **Recreate observations** from analyses that have actual data
