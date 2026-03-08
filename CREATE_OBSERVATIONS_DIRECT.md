# Create Observations Directly from Claims Data

Since the API database connection is failing, I've created a script that works directly with the claims data file.

## Run This Script

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 scripts/create_observations_direct_from_claims.py
```

## What It Does

1. ✅ **Loads claims data** from the 384MB CSV file
2. ✅ **Computes pre-policy metrics** (6 months before policy effective date)
3. ✅ **Computes post-policy metrics** (1 month after policy effective date)
4. ✅ **Creates observations** with actual observed values
5. ✅ **Saves to files** in `apps/api/src/data/observations/`

## Output

The script will create observation JSON files with:
- ✅ Actual `utilization_per_1k` from claims data
- ✅ Actual `cost_pmpm` from claims data
- ✅ `vs_baseline` comparisons with real numbers
- ✅ `behavioral_explanation` with actual percent change

## After Running

The observations will be saved as JSON files. You can:
1. **Import them via API** when database is working
2. **Use them directly** if the API reads from files
3. **View them in UI** if the frontend can load from files

## Expected Results

You should see output like:
```
✅ Baseline: Utilization=125.50, Cost PMPM=$45.23
✅ Observed: Utilization=106.70, Cost PMPM=$38.40
✅ Observation created: {obs_id}.json
   Utilization: 106.70
   Cost PMPM: $38.40
   Change: -15.0%
```

This will give you observations with **real observed values** instead of "N/A"!
