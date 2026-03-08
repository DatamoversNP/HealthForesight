# Fix Pipelines and Run All Data Ingestion

## Issues Identified

1. **Missing Required Fields**: Some pipelines are missing required fields in their configurations
2. **Incorrect Deduplication**: Some pipelines have wrong deduplication key fields
3. **Pipelines Not Run**: Most pipelines haven't been executed yet (only CLAIMS_LINES has data)

## Solution

### Step 1: Update Pipeline Field Mappings

First, update existing pipelines with correct field mappings and deduplication:

```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
python3 apps/api/scripts/update_pipelines_field_mappings.py
```

This will fix:
- Missing required fields
- Incorrect deduplication key fields
- Field mapping issues

### Step 2: Verify Fixes

```bash
python3 apps/api/scripts/validate_target_data_model.py
python3 apps/api/scripts/validate_pipelines_deduplication.py
```

### Step 3: Run All Pipelines

Run all pipelines to ingest source data:

```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
python3 apps/api/scripts/run_all_pipelines_direct.py
```

This will:
- Match each pipeline to its source files
- Execute pipelines directly (not via API)
- Process all source data files
- Write to target data model
- Handle duplicates automatically
- Show progress and results

### Step 4: Verify Results

```bash
# Count target records
python3 apps/api/scripts/count_target_records.py

# Compare source vs target
python3 apps/api/scripts/compare_source_target_counts.py
```

## Expected Results

After running all pipelines:
- ✅ All 21+ datasets ingested
- ✅ Duplicates removed automatically
- ✅ Target record counts match source (minus duplicates)
- ✅ All pipelines have correct field mappings
- ✅ All pipelines have proper deduplication

## Pipeline Execution Details

The `run_all_pipelines_direct.py` script:
1. Loads all pipelines from database
2. Matches pipelines to source files
3. Converts pipeline configs to PipelineMetadata
4. Creates PipelineEngine for each pipeline
5. Executes pipeline with each source file
6. Writes results to `data/target_data_model/{tenant_id}/{dataset_type}/`
7. Handles duplicates based on pipeline deduplication strategy
8. Reports progress and results

## Field Mapping Fixes

The following pipelines will be updated:

1. **Claim Header Pipeline** - Add `total_paid`, `total_allowed`, `claim_status` to required_fields
2. **Appeal Grievance Pipeline** - Ensure `outcome` is in required_fields
3. **Call Center Contact Pipeline** - Ensure `contact_topic` is in required_fields
4. **Claims Lines Pipeline** - Update deduplication to use `["claim_id", "claim_line_id"]`
5. **Member Diagnosis Pipeline** - Ensure `onset_date` is in required_fields and deduplication keys
6. **Benefit Design Pipeline** - Ensure `service_category` is in required_fields and deduplication keys
7. **Referral Pipeline** - Ensure `referring_provider_id` is in required_fields
8. **Provider Contract Pipeline** - Ensure `effective_date` is in required_fields
9. **Prior Authorization Request Pipeline** - Ensure `decision`, `service_code` are in required_fields
10. **Member Accumulator Pipeline** - Ensure `accumulator_value` is in required_fields, update deduplication
11. **Member Risk Stratification Pipeline** - Ensure `risk_score` is in required_fields
12. **Pharmacy Claims Pipeline** - Update deduplication to use `["rx_claim_id"]`

All fixes are applied automatically by the update script.

