# Complete Setup Guide: Data Quality, Pipelines, and Data Generation

## 1. Why Data Quality Shows 0% But "No Issues Found"

### The Issue
The dashboard shows **0% quality** but **"No issues found"** - this seems contradictory.

### Explanation
- **0% Quality**: No data quality report exists yet (validation hasn't been run)
- **"No Issues Found"**: The issues array is empty (because no report exists)
- **Solution**: Run validation to generate the report

See `EXPLAIN_DATA_QUALITY_ZERO_PERCENT.md` for details.

## 2. Run All Existing Pipelines

### Quick Start
```bash
./RUN_ALL_PIPELINES.sh
```

### What It Does
1. Fetches all pipelines from the API
2. Runs each pipeline sequentially
3. Shows status for each pipeline
4. Provides a summary of successes/failures

### Manual Run
```bash
# Get pipeline IDs
curl http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token"

# Run a specific pipeline
curl -X POST http://localhost:8000/api/v1/pipelines/{pipeline_id}/run \
  -H "Authorization: Bearer demo-token"
```

## 3. Generate Data from Last Date Onwards

### Quick Start
```bash
./GENERATE_DATA_FROM_LAST_DATE.sh
```

### Configuration
```bash
# Generate 3 months (default)
./GENERATE_DATA_FROM_LAST_DATE.sh

# Generate 6 months
MONTHS_TO_GENERATE=6 ./GENERATE_DATA_FROM_LAST_DATE.sh

# Custom output directory
OUT_DIR=data/custom ./GENERATE_DATA_FROM_LAST_DATE.sh
```

### What It Does
1. **Finds latest existing data** - Scans `apps/api/data/target_data_model/` for the most recent month
2. **Calculates start date** - Starts from the month after the latest data
3. **Generates new data** - Creates claims, members, and providers for the specified months
4. **Saves to target directory** - Outputs to the correct location for the API

### Manual Generation
```bash
# Use the generator script directly
python3 scripts/synth/generate.py \
  --out data/demo \
  --members 50000 \
  --providers 5000 \
  --months 3 \
  --seed 42
```

## 4. Complete Workflow

### Step 1: Generate New Data
```bash
./GENERATE_DATA_FROM_LAST_DATE.sh
```

### Step 2: Run Pipelines
```bash
./RUN_ALL_PIPELINES.sh
```

### Step 3: Run Data Quality Validation
1. Go to Data Quality Dashboard
2. Click "Run Validation"
3. Wait for completion (check status endpoint)
4. Refresh dashboard to see results

### Step 4: Verify Results
- Check Data Quality Dashboard for quality scores
- Check Pipeline Monitoring for pipeline status
- Check Data Explorer for data availability

## 5. Troubleshooting

### Pipelines Not Running
- Check API is running: `curl http://localhost:8000/api/v1/pipelines`
- Check pipeline status: Go to Pipeline Monitoring page
- Check logs: Look at API server logs

### Data Not Generating
- Check Python dependencies: `pip install pandas polars`
- Check output directory permissions
- Check disk space

### Data Quality Still 0%
- Wait for validation to complete (can take 5-10 minutes)
- Check validation status: `curl http://localhost:8000/api/v1/data-quality/validate/status`
- Check for errors in API logs

## 6. Scripts Created

1. **RUN_ALL_PIPELINES.sh** - Runs all existing pipelines
2. **GENERATE_DATA_FROM_LAST_DATE.sh** - Generates data from last date onwards
3. **EXPLAIN_DATA_QUALITY_ZERO_PERCENT.md** - Explains the 0% quality issue

## 7. Next Steps

After running these scripts:
1. ✅ Data will be generated from the last date onwards
2. ✅ Pipelines will process the new data
3. ✅ Data quality validation will show actual scores (not 0%)
4. ✅ Dashboard will display real metrics

All systems will be operational with fresh data!
