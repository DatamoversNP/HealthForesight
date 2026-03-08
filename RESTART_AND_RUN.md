# Restart API and Run Fix Script

## Issue Fixed
- Database password mismatch: Config had `uepi` but docker-compose uses `uepi123` ✅
- Made API startup more resilient to database connection errors ✅

## Steps to Run

### 1. Stop Current API (if running)
Press `Ctrl+C` in the terminal where API is running, or:
```bash
pkill -f 'uvicorn uepi_api.main:app'
```

### 2. Start API Again
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API should now start successfully (even if database connection fails, it will continue).

### 3. In Another Terminal, Run the Fix Script
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 scripts/create_observations_from_claims_data.py
```

## What the Script Will Do

1. ✅ Check if API is running
2. ✅ Get all policies (36 policies found)
3. ✅ For each policy:
   - Run impact analysis (synchronous endpoint - processes immediately)
   - Wait for analysis to complete
   - Check if analysis has `treatment_post` data
   - Create observation from analysis
4. ✅ Report success/failure for each observation

## Expected Results

After running, you should see:
- ✅ Analyses with status "COMPLETED" (not PENDING)
- ✅ Analyses with `treatment_post.utilization_per_1k > 0`
- ✅ Observations created with actual observed values
- ✅ UI showing real numbers instead of "N/A"

## If Database Connection Still Fails

The API will start anyway (startup is now resilient), but some endpoints may not work. The synchronous impact analysis endpoint should still work because it reads from files, not database.

## Troubleshooting

If analyses still show PENDING:
- Check API logs for errors
- Verify claims data exists: `ls -lh apps/data/target_data_model/*/CLAIMS_LINES/`
- Check if synchronous endpoint is being used (should return COMPLETED immediately)

If observations still show N/A:
- Check that analyses have `treatment_post` data
- Verify observations were created from completed analyses
- Check observation response from API
