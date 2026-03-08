# Running Baseline Analysis

## Step 1: Start the API Server

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./restart-api-server.sh
```

Wait for the server to start (check for "✅ API server is responding!" message).

## Step 2: Run Baseline Analysis

### Option A: Using the Script (Recommended)

```bash
source .venv/bin/activate
python scripts/run_baseline_analysis_only.py
```

### Option B: Using the UI

1. Open browser to: http://localhost:3050/baseline-analysis
2. Click "Run Analysis" button
3. Wait for completion (may take a few minutes)

### Option C: Using curl

```bash
curl -X POST http://localhost:8000/api/v1/analyses/baseline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-token-123" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2025-12-31",
    "n_clusters": 5
  }'
```

## What Will Be Computed

The baseline analysis will now compute all metrics from the Final Metric Dictionary:

✅ **Primary Outcomes:**
   - util_rate_total_per_1000_mm
   - util_rate_target_per_1000_mm (when policy-scoped)
   - allowed_pmpm_total
   - allowed_pmpm_target (when policy-scoped)
   - allowed_total_annualized (NEW!)

✅ **Mix Metrics:**
   - soc_share_target_{categories} (dynamically computed)
   - inn_share_target
   - oon_leakage_rate_target_per_1000_mm (NEW!)
   - provider_hhi_target (NEW!)
   - top10_provider_share_target

✅ **Provider Segmentation:**
   - Provider archetypes
   - Provider concentration metrics

## Expected Output

- Baseline record created with all computed metrics
- Metrics available for policy-scoped baselines
- Ready for predicted impact and observation analysis

## Troubleshooting

If you see errors:
1. Check API server logs: `tail -f api-server.log`
2. Verify claims data exists: `ls -la apps/data/target_data_model/*/CLAIMS_LINES/`
3. Check API health: `curl http://localhost:8000/health`
