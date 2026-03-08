# Fix: Ingestion Upload 500 Error

## Problem

The daily job is failing with a 500 error when uploading ingestion data:
```
POST /api/v1/ingestions/upload 500 Internal Server Error
ERROR: Daily job 7c92601a-5877-463d-8373-857cddc8455f failed:
```

The error message is cut off, making it hard to diagnose.

## Solution

I've improved error logging to capture the full traceback. The error handler now:
1. ✅ Prints the full error traceback to the console
2. ✅ Saves the traceback in the ingestion metadata
3. ✅ Raises a proper HTTPException with error details

## What Changed

**File:** `apps/api/src/uepi_api/routers/ingestions_file.py`

Updated the exception handler to:
- Print full traceback to console/logs
- Include traceback in ingestion metadata
- Provide better error messages

## Next Steps

1. **Check API logs** - The full error traceback should now appear in the API server logs
2. **Check ingestion metadata** - The error details are saved in the ingestion record
3. **Common causes:**
   - Missing dependencies (e.g., `ComprehensiveIngestionProcessor` dependencies)
   - File system permissions
   - Missing configuration
   - Memory issues with large files

## To Debug

Run the API server and check the console output when the daily job runs. You should see:

```
ERROR: Ingestion failed for <ingestion_id>:
<full error message>

Traceback:
<full traceback>
```

This will help identify the exact cause of the 500 error.

## Testing

Try running the daily job again and check:
1. API server console logs for the full error
2. The ingestion record's metadata field for error details
3. The daily job logs for any additional context
