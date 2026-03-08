# Baseline Analysis - Data Quality Issues

## Issue Found: Empty Date Column

The baseline analysis is unable to generate time series data because the `service_date_from` column in the claims data is **empty** (all values are null/empty strings).

### Current Status

- ✅ **Baseline analysis runs successfully**
- ✅ **Patient Segments**: Working - shows HIGH/MEDIUM/LOW risk segments
- ✅ **Confounder Calendar**: Working - shows seasonal events
- ✅ **Benchmarks**: Working - shows utilization/cost metrics
- ❌ **Time Series**: Empty - cannot generate because date column is empty
- ❌ **Provider Archetypes**: Empty - expected (no provider ID columns in data)

### Root Cause

The claims CSV file at:
```
apps/data/target_data_model/00000000-0000-0000-0000-000000000001/CLAIMS_LINES/claims_lines.csv
```

Has the `service_date_from` column but all values are empty/null. This causes:
1. All date conversions to result in NaT (Not a Time)
2. All rows to be filtered out
3. No time series data to be generated

### Solution Options

1. **Regenerate data**: Re-run data generation to include valid dates in `service_date_from`
2. **Use alternative date column**: If another date column exists (e.g., `service_date_to`, `paid_date`), update the code to use it
3. **Generate synthetic dates**: If no date columns exist, create synthetic dates based on row order or other heuristics

### Code Changes Made

The code now:
- Checks if date column is empty before attempting conversion
- Logs detailed information about date parsing issues
- Gracefully handles missing dates (returns empty time series instead of failing)

### Next Steps

To fix time series generation:
1. Ensure the claims data has valid dates in `service_date_from` (or another date column)
2. Re-run baseline analysis after data is fixed
3. Time series should then populate automatically
