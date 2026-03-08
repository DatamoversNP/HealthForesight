# Quick Fix for Observations

## Problem
Analyses are being created with status "PENDING" but not processing, so observations don't have observed values.

## Solution Applied

I've updated the code to:
1. **Added synchronous analyses endpoint** - The `analyses_file.router` is now registered, which processes analyses immediately
2. **Updated script** - The script now waits for analyses to complete and checks for `treatment_post` data properly

## Next Steps

### Option 1: Restart API and Run Script (Recommended)

1. **Restart the API** to load the new router:
   ```bash
   # Stop current API (Ctrl+C or pkill)
   pkill -f 'uvicorn uepi_api.main:app'
   
   # Start API again
   cd apps/api/src
   export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Run the fix script**:
   ```bash
   python3 scripts/create_observations_from_claims_data.py
   ```

### Option 2: Use the Synchronous Endpoint Directly

The synchronous endpoint should now be available. The script will automatically use it, but if you want to test manually:

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/impact" \
  -H 'Authorization: Bearer dev-token-123' \
  -H 'Content-Type: application/json' \
  -d '{
    "policy_id": "POLICY_UUID",
    "treatment_filters": {
      "lob": ["COMMERCIAL", "MA", "MEDICAID"],
      "markets": ["BOS", "DFW", "NYC"],
      "in_network_only": true
    },
    "control_filters": null,
    "pre_window_months": 6,
    "post_window_months": 1
  }'
```

This should return status "COMPLETED" immediately with `treatment_post` metrics.

### Option 3: Check Existing Analyses

If you have existing PENDING analyses, you can check if they've completed:

```bash
# List analyses
curl -X GET "http://localhost:8000/api/v1/analyses?status=COMPLETED" \
  -H 'Authorization: Bearer dev-token-123' | python3 -m json.tool

# Get specific analysis
curl -X GET "http://localhost:8000/api/v1/analyses/{analysis_id}" \
  -H 'Authorization: Bearer dev-token-123' | python3 -m json.tool
```

## Expected Result

After running the script, you should see:
- ✅ Analyses with status "COMPLETED"
- ✅ Analyses with `result.metrics.treatment_post.utilization_per_1k > 0`
- ✅ Observations created with observed values
- ✅ UI showing actual numbers instead of "N/A"

## Troubleshooting

If analyses still show PENDING:
1. Check API logs for errors
2. Verify claims data exists: `ls -lh apps/data/target_data_model/*/CLAIMS_LINES/`
3. Check if the synchronous endpoint is working by looking at API response

If observations still show N/A:
1. Check that analyses have `treatment_post` data
2. Verify observations were created from completed analyses
3. Check observation metrics in API response
