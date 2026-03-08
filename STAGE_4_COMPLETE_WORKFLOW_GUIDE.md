# Stage 4 Complete Workflow Guide

## Overview
This guide walks through generating post-policy synthetic data, ingesting it, and running Stage 4 impact analysis.

## Prerequisites
- Python 3.11+ with pandas, polars installed
- OR Docker environment with proper dependencies
- API server running (for ingestion and analysis)

## Step 1: Generate Post-Policy Synthetic Data

### Option A: Using Python directly (requires pandas, polars)
```bash
cd /Users/nilesh.patil/Downloads/Utilization\ Elastisity\ and\ Policy\ Impact\ Solution
python3 scripts/generate_post_policy_synthetic_data.py --months 6 --out data/post_policy
```

### Option B: Using Docker (if available)
```bash
docker-compose exec api python scripts/generate_post_policy_synthetic_data.py --months 6 --out /app/data/post_policy
```

### What gets generated:
- `data/post_policy/claims_lines_YYYYMM.csv` - Claims data by month
- `data/post_policy/enrollment.csv` - Member enrollment data
- `data/post_policy/providers.csv` - Provider directory
- `data/post_policy/manifest.json` - Manifest file for ingestion

**Note:** All data generated reflects policy impacts (policies are effective from the start date).

## Step 2: Ingest the Generated Data

### Option A: Using the API (Recommended)

1. **Upload files to object storage** (if using S3/MinIO)
   - Upload all CSV files from `data/post_policy/`
   - Note the S3/minIO URIs

2. **Create ingestion via API:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ingestions" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "ingestion_type": "CLAIMS_LINES",
       "manifest_uri": "file:///path/to/data/post_policy/manifest.json"
     }'
   ```

3. **Or use the UI:**
   - Go to "Data & Ingestion" page
   - Upload files or provide manifest URI
   - Create ingestion job

### Option B: Using file-based storage (local development)
- The ingestion will process files directly from the file system
- Ensure manifest.json paths are correct

## Step 3: Run Stage 4 Impact Analysis

### Using the API:

1. **Create impact analysis:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analyses/impact" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_id": "POLICY_UUID",
       "treatment_filters": {
         "lob": ["COMMERCIAL"],
         "markets": ["NYC", "DFW"],
         "in_network_only": true
       },
       "control_filters": null,
       "pre_window_months": 6,
       "post_window_months": 6
     }'
   ```

2. **The analysis will:**
   - Load historical data (before policy effective date) as baseline/pre-period
   - Load new synthetic data (from policy effective date) as observed/post-period
   - Run Difference-in-Differences (DiD) analysis
   - Compare observed impact against predicted impact (Stage 3.5)
   - Compare observed impact against baseline (Stage 3)
   - Return comprehensive results with comparisons

### Using the UI:
- Go to "Analyses" page
- Create new "Impact Analysis"
- Select policy and configure filters
- Run analysis
- View results with comparison metrics

## Step 4: View Results

### Results Structure:
```json
{
  "policy_id": "...",
  "impact_result": {
    "effect_size": -15.5,
    "percent_change": -12.3,
    "confidence_interval": [-20.0, -11.0],
    ...
  },
  "comparisons": {
    "predicted_impact": {
      "predicted": {
        "effect_size": -18.0,
        "percent_change": -15.0
      },
      "observed": {
        "effect_size": -15.5,
        "percent_change": -12.3
      },
      "prediction_error": {
        "effect_size_error": 2.5,
        "effect_size_error_pct": 13.9
      },
      "prediction_accuracy_pct": 86.1,
      "within_predicted_range": true
    },
    "baseline": {
      "baseline_utilization_per_1k": 125.0,
      "observed_change_from_baseline": -15.5,
      "observed_change_from_baseline_pct": -12.3
    }
  },
  "summary": {
    "effect_size": -15.5,
    "percent_change": -12.3,
    "confidence_score": 85,
    "data_sufficient": true,
    "warnings": []
  }
}
```

## Key Metrics in Results

### Observed Impact Metrics:
- `effect_size`: Absolute change in utilization per 1k members
- `percent_change`: Percentage change from baseline
- `confidence_interval`: Statistical confidence interval
- `confidence_score`: Overall confidence (0-100)

### Comparison Metrics:

**Predicted vs Observed:**
- `prediction_accuracy_pct`: How close observed was to predicted (higher is better)
- `effect_size_error`: Difference between predicted and observed
- `within_predicted_range`: Whether observed falls within predicted confidence interval

**Baseline vs Observed:**
- `observed_change_from_baseline`: Absolute change from baseline
- `observed_change_from_baseline_pct`: Percentage change from baseline

## Troubleshooting

### Data Generation Issues:
- **ModuleNotFoundError**: Install pandas and polars: `pip install pandas polars`
- **Permission errors**: Check file permissions on output directory
- **Date errors**: Ensure start date is in YYYY-MM-DD format

### Ingestion Issues:
- **Manifest not found**: Check manifest.json path is correct
- **File not found**: Ensure all CSV files are in the correct location
- **Storage errors**: Check object storage credentials and permissions

### Analysis Issues:
- **No data found**: Verify data was ingested correctly and dates match
- **Policy not found**: Ensure policy exists and has predicted impact generated
- **Filter errors**: Check filter syntax matches expected format

## Next Steps

After running Stage 4 analysis:
1. Review comparison metrics to see how well predictions matched reality
2. Analyze prediction accuracy to improve future predictions
3. Review baseline comparisons to understand policy impact
4. Use results for policy decision-making and optimization
