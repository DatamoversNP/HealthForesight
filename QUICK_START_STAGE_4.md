# Quick Start: Stage 4 Data Generation & Analysis

## Quick Summary

To generate post-policy data and run Stage 4 analysis:

### 1. Generate Data (requires pandas/polars)
```bash
# Install dependencies if needed
pip install pandas polars

# Generate 6 months of post-policy data
python3 scripts/generate_post_policy_synthetic_data.py --months 6 --out data/post_policy
```

### 2. Ingest Data
- Use the UI: Go to "Data & Ingestion" → Upload files or provide manifest URI
- Or use API: `POST /api/v1/ingestions` with manifest_uri

### 3. Run Analysis
- Use the UI: Go to "Analyses" → Create "Impact Analysis"
- Or use API: `POST /api/v1/analyses/impact` with policy_id and filters

### 4. View Results
- Results include comparisons:
  - Observed vs Predicted Impact (prediction accuracy)
  - Observed vs Baseline (policy impact)

## Requirements

- Python 3.11+ with pandas, polars
- API server running
- Policies with predicted impact already generated (Stage 3.5)

## Output Location

- Generated data: `data/post_policy/`
- Manifest: `data/post_policy/manifest.json`

## Note

If you get "ModuleNotFoundError: No module named 'pandas'", install dependencies:
```bash
pip install pandas polars
```

Or run in Docker if available.
