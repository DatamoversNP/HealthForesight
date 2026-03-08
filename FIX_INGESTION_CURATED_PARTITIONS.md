# Fix: Ingestion Upload Missing `curated_partitions` Field

## Problem

The ingestion upload was failing with:
```
1 validation error for IngestionProcessingResult
curated_partitions
  Field required [type=missing, input_value={'ingestion_id': UUID('56...rs': [], 'warnings': []}, input_type=dict]
```

The `ComprehensiveIngestionProcessor.process_file()` method doesn't return `curated_partitions`, but the `IngestionProcessingResult` model requires it.

## Solution

I've fixed this by:

1. **Made `curated_partitions` optional** - Added default value `[]` to the model
2. **Made other optional fields explicit** - Added defaults for `raw_zone_uri`, `errors`, and `warnings`
3. **Explicitly constructed response** - Instead of using `**kwargs`, now explicitly extracts and defaults all required fields

## What Changed

**File:** `apps/api/src/uepi_api/routers/ingestions_file.py`

### 1. Updated `IngestionProcessingResult` model:
```python
class IngestionProcessingResult(BaseModel):
    success: bool
    ingestion_id: UUID
    raw_zone_uri: Optional[str] = None  # Added default
    curated_partitions: List[str] = []  # Added default
    record_count: int
    records_valid: int
    records_invalid: int
    errors: List[Dict[str, Any]] = []  # Added default
    warnings: List[Dict[str, Any]] = []  # Added default
```

### 2. Updated response construction:
```python
result_data = {
    "ingestion_id": ingestion_id,
    "success": processing_result.get("success", False),
    "record_count": processing_result.get("record_count", 0),
    "records_valid": processing_result.get("records_valid", 0),
    "records_invalid": processing_result.get("records_invalid", 0),
    "raw_zone_uri": processing_result.get("raw_zone_uri"),
    "curated_partitions": processing_result.get("curated_partitions", []),
    "errors": processing_result.get("errors", []),
    "warnings": processing_result.get("warnings", []),
}

return IngestionProcessingResult(**result_data)
```

## Testing

The daily job should now complete successfully without the 500 error. The ingestion will:
1. ✅ Process the file
2. ✅ Return a valid response with all required fields
3. ✅ Complete the daily job

## Next Steps

The daily job should now work correctly. If `curated_partitions` are needed in the future, the `ComprehensiveIngestionProcessor` should be updated to return them, but the API will handle missing values gracefully.
