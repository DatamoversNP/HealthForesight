# Execute Workflow: Generate Data, Create Baselines & Observations

## Quick Start

1. **Start the API server** (if not already running):
   ```bash
   cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Run the workflow script** (in a new terminal):
   ```bash
   python3 scripts/generate_data_and_create_baselines_observations.py
   ```

## What the Script Does

### Step 1: Generate Policy-Scoped Data
- Generates general claims data for last 3 days
- Generates policy-specific claims data matching each policy's scope (procedure codes, diagnosis codes, service categories)
- Handles duplicate data gracefully (skips if already exists)

### Step 2: Create Baselines
- Creates general baseline (across all data)
- Creates policy-specific baselines for each active policy
- Uses actual database data (no mock data)

### Step 3: Create Observations
- Completes any pending analyses
- Creates observations for all policies with completed impact analyses
- Skips observations that already exist

## Script Features

✅ **Production-ready**: Handles errors gracefully, continues on failures
✅ **Safe**: Only uses POST endpoints for data generation, doesn't modify GET endpoints
✅ **Progress tracking**: Shows progress for large operations
✅ **Error handling**: Continues even if some operations fail

## Expected Output

```
================================================================================
🚀 GENERATE DATA, CREATE BASELINES & OBSERVATIONS
================================================================================
Started at: 2026-02-08T10:51:53.213588
✅ Connected to API server

📊 STEP 1: Generating Policy-Scoped Data
   Found 36 active policies
   📅 Generating data for 2026-02-07...
      ✅ Generated 25000 general claims
      ✅ Generated policy-specific data for 15/15 policies
   ...

📊 STEP 2: Creating Baselines
   ✅ General baseline created
   ✅ Policy-specific baselines: 15/36 policies

📈 STEP 3: Creating Observations
   ✅ Observations: 10 created, 33 skipped, 0 failed

📊 FINAL SUMMARY
Data Generation: ✅ Success
Baselines: General=1, Policy-specific=15/36
Observations: 10 created, 33 skipped, 0 failed
```

## Notes

- The script limits policy-specific data generation to 15 policies per day to avoid timeouts
- Policy-specific baselines may fail if the generated data doesn't match the policy scope (this is expected)
- Observations are only created for policies with completed impact analyses
- All operations are idempotent (safe to run multiple times)

## Troubleshooting

If you see connection errors:
1. Make sure the API server is running on port 8000
2. Check that the database is accessible
3. Verify the API server logs for any errors

If baselines fail:
- This is expected if the generated data doesn't match policy scopes
- General baseline should still succeed
- Policy-specific baselines require data that matches the policy's procedure codes, diagnosis codes, etc.
