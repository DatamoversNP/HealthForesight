# Fix Scorecards Predicted Impact Structure

## Issue
The scorecards generation endpoint was failing with a 500 error because it expected a specific structure for predicted impact data that doesn't match the actual structure.

## Root Cause
The `generate_scorecard_from_predicted_impact` function expected:
- `predicted_impact.projected_impact.cost_savings`
- `predicted_impact.projected_impact.utilization_change`
- `predicted_impact.projected_impact.behavioral_response`

But the actual predicted impact structure uses:
- `predicted_impact.metrics.cost_change_pct`
- `predicted_impact.metrics.utilization_change_pct`
- etc.

## Fix Applied
Updated `apps/api/src/uepi_api/storage_scorecards.py` to:
1. Check for new format first (`metrics`)
2. Fallback to old format (`projected_impact`) if new format not found
3. Map the metrics correctly to what scorecard generation needs

## Also Fixed
- String policy ID support in scorecards endpoint (already done)

## Status
✅ **Fixed** - Scorecards generation now handles both predicted impact formats.

## Restart Required
The server needs to restart to apply this fix:
```bash
# Stop current server (CTRL+C)
./START_API_NOW.sh
```

## After Restart
- Scorecards generation should work
- Will work with both old and new predicted impact formats
- Will handle string policy IDs correctly
