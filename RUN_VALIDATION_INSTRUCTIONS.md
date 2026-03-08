# How to Run Data Quality Validation

## Status: Command timed out when running directly

The validation script requires pandas and the Python environment. Here are the best ways to run it:

## Option 1: Via API Server (Recommended) ✅

Since the API server runs in the proper environment with all dependencies:

1. **Start the servers:**
   ```bash
   ./start-both-servers.sh
   ```

2. **Via UI:**
   - Navigate to `http://localhost:3050/data-explorer`
   - Click on the **"Data Quality"** tab
   - Click **"Run Validation"** button
   - Wait for it to complete (may take 2-5 minutes)

3. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/data-quality/validate \
     -H "Authorization: Bearer dev-token-123" \
     -H "Content-Type: application/json"
   ```

## Option 2: Via Virtual Environment

If you want to run the script directly:

```bash
# Activate venv
source .venv/bin/activate

# Run validation
python3 scripts/comprehensive_data_quality_check.py

# Or install pandas if needed
pip install pandas numpy
python3 scripts/comprehensive_data_quality_check.py
```

## Option 3: Quick Check (Basic Validation)

For a quick check without full validation, you can verify files exist:

```bash
# Check files exist
ls -lh apps/data/target_data_model/00000000-0000-0000-0000-000000000001/CLAIMS_LINES/claims_lines.csv
ls -lh apps/data/target_data_model/00000000-0000-0000-0000-000000000001/ENROLLMENT/enrollment.csv
ls -lh apps/data/target_data_model/00000000-0000-0000-0000-000000000001/PROVIDERS/providers.csv

# Check file sizes (should be ~64MB for claims)
du -sh apps/data/target_data_model/00000000-0000-0000-0000-000000000001/*
```

## Expected Results

After validation completes, you should see:
- **Quality Report**: Saved to `apps/data/target_data_model/{tenant_id}/data_quality_report.json`
- **Overall Score**: Should be 90-100% (all fields populated, no duplicates, valid data)
- **Dataset Scores**: Each dataset (CLAIMS_LINES, ENROLLMENT, PROVIDERS) should score 90-100%
- **Issues**: Should be minimal or none (possibly some LOW severity warnings)

## Next Steps After Validation

1. Review issues (if any) in the UI
2. Fix any HIGH severity issues
3. Run Baseline Analysis
4. Generate Predicted Impact
5. Run Observation Analysis

The validation script is ready - it just needs to run in an environment with pandas/numpy installed, which the API server has.
