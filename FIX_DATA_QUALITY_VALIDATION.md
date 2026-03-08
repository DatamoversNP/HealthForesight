# Fixed Data Quality Validation Endpoint

## Issue
The `/api/v1/data-quality/validate` endpoint was returning 404 because it couldn't find the validation script.

## Root Cause
The path calculation in `apps/api/src/uepi_api/routers/data_quality.py` was incorrect:
- **Before:** `Path(__file__).parent.parent.parent.parent.parent / "scripts" / ...`
- **After:** `Path(__file__).parent.parent.parent.parent.parent.parent / "scripts" / ...`

The script exists at `scripts/comprehensive_data_quality_check.py` (project root), but the path calculation was going up one level too few.

## Fix Applied
Updated the path calculation to correctly navigate from:
- `apps/api/src/uepi_api/routers/data_quality.py` 
- Up 6 levels to project root
- Then to `scripts/comprehensive_data_quality_check.py`

## Status
✅ **Fixed** - The endpoint should now find the script correctly.

## Next Steps
**Restart the API server** to apply the fix:
```bash
# Stop current server (CTRL+C)
./START_API_NOW.sh
```

After restart, the data quality validation should work when you click "Run Validation" on the Data Quality Dashboard page.
