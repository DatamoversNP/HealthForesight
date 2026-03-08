# Fix Observations - Action Plan

## Diagnostic Results

✅ Claims data exists (384MB file)
❌ API server is not running
❌ Analysis files are metadata only (no treatment_post metrics)
❌ Observations don't have observed values

## Root Cause

The analysis files in `apps/api/src/data/analyses/` are just metadata records. The actual analysis results with `treatment_post` metrics should be:
1. Computed by running impact analyses on actual claims data
2. Stored in database (`ImpactAnalysisResult` table)
3. Used to create observations

## Step-by-Step Fix

### Step 1: Start the API Server

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

Keep this running in a terminal window.

### Step 2: Verify API is Running

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Step 3: Run Impact Analyses with Actual Claims Data

For each policy, run an impact analysis that loads actual claims data:

```bash
# Get list of policies first
curl -X GET "http://localhost:8000/api/v1/policies" \
  -H 'Authorization: Bearer dev-token-123' | python3 -m json.tool

# For each policy, run impact analysis
curl -X POST "http://localhost:8000/api/v1/analyses/impact" \
  -H 'Authorization: Bearer dev-token-123' \
  -H 'Content-Type: application/json' \
  -d '{
    "policy_id": "POLICY_UUID_HERE",
    "treatment_filters": {
      "lob": ["COMMERCIAL", "MA", "MEDICAID"],
      "markets": ["BOS", "DFW", "NYC"],
      "in_network_only": true
    },
    "control_filters": null,
    "pre_window_months": 6,
    "post_window_months": 6
  }'
```

**Important:** The impact analysis endpoint (`/api/v1/analyses/impact`) should:
- Load claims data from `apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/`
- Filter to post-policy period
- Compute `treatment_post` metrics:
  - `utilization_per_1k`
  - `allowed_pmpm`
  - `paid_pmpm`
  - `total_claims`

### Step 4: Verify Analysis Has treatment_post Data

After running an analysis, check if it has results:

```bash
# Get analysis by ID
curl -X GET "http://localhost:8000/api/v1/analyses/{analysis_id}" \
  -H 'Authorization: Bearer dev-token-123' | python3 -m json.tool

# Check if result_data_json has metrics.treatment_post
```

Or check in database:
```sql
SELECT 
  id, 
  analysis_id,
  result_data_json->'metrics'->'treatment_post' as treatment_post
FROM impact_analysis_results
WHERE result_data_json->'metrics'->'treatment_post' IS NOT NULL
LIMIT 5;
```

### Step 5: Create Observations from Analyses

Once analyses have `treatment_post` data, create observations:

```bash
# Create observation from analysis
curl -X POST "http://localhost:8000/api/v1/observations/from-analysis/{analysis_id}?policy_id={policy_id}" \
  -H 'Authorization: Bearer dev-token-123'
```

### Step 6: Verify Observations Have Data

```bash
# List observations
curl -X GET "http://localhost:8000/api/v1/observations" \
  -H 'Authorization: Bearer dev-token-123' | python3 -m json.tool

# Check if observations have:
# - metrics.utilization_per_1k > 0
# - metrics.cost_pmpm > 0
# - comparisons.vs_baseline.observed_utilization_per_1k > 0
# - comparisons.vs_predicted.observed_utilization > 0
```

## Alternative: Use Daily Job (Recommended)

The daily job automates steps 3-5:

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/daily-data-and-observations" \
  -H 'Authorization: Bearer dev-token-123' \
  -H 'Content-Type: application/json' \
  -d '{
    "target_date": "2024-12-15",
    "run_observations": true
  }'
```

This will:
1. Generate/load post-policy claims data
2. Run impact analyses on actual data
3. Create observations from analyses

## Quick Fix Script

I'll create a script to automate this process. Run it after starting the API:

```bash
python3 scripts/create_observations_from_claims_data.py
```

## Key Code Locations

### Where Impact Analysis Computes treatment_post
- **File:** `apps/api/src/uepi_api/routers/analyses_file.py`
- **Function:** `compute_pre_post_metrics()`
- **Lines:** 23-91
- **Key:** Computes `treatment_post` from actual claims DataFrame

### Where Observations Extract Metrics
- **File:** `apps/api/src/uepi_api/observation_enhancement.py`
- **Function:** `extract_metrics_from_analysis_result()`
- **Lines:** 13-56
- **Key:** Looks for `analysis_result["metrics"]["treatment_post"]`

## Expected Data Flow

```
Claims Data (384MB CSV)
    ↓
Impact Analysis Endpoint
    ↓
Load Claims → Filter Post-Period → Compute Metrics
    ↓
Store in ImpactAnalysisResult.result_data_json
    {
      "metrics": {
        "treatment_post": {
          "utilization_per_1k": 130.5,
          "allowed_pmpm": 45.23,
          "paid_pmpm": 42.10,
          "total_claims": 1250
        }
      }
    }
    ↓
Create Observation
    ↓
Extract treatment_post → Store in observation.metrics
    ↓
UI Shows Observed Values ✅
```

## Next Steps

1. **Start API server** (Step 1)
2. **Run diagnostic** to verify claims data is accessible
3. **Run impact analyses** on policies (Step 3)
4. **Verify analyses have treatment_post** (Step 4)
5. **Create observations** from analyses (Step 5)
6. **Verify observations have data** (Step 6)

Or use the **daily job** which automates everything.
