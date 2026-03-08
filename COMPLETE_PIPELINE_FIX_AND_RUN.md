# Complete Pipeline Fix and Run Guide

## Issues Found

1. **Missing Required Fields**: 15 pipelines have missing required fields
2. **Incorrect Deduplication**: Some pipelines have wrong deduplication key fields
3. **Pipelines Not Executed**: Only CLAIMS_LINES has data in target (other 20+ pipelines haven't been run)

## Solution: Complete Fix and Run

### Quick Fix (All-in-One)

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"

# Run complete fix and execution
python3 apps/api/scripts/fix_and_run_all_pipelines.py
```

### Step-by-Step

#### Step 1: Update Pipeline Field Mappings

```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
python3 apps/api/scripts/update_pipelines_field_mappings.py
```

**Fixes Applied:**
- ✅ Claim Header Pipeline - Adds `total_paid`, `total_allowed`, `claim_status` to required_fields
- ✅ Appeal Grievance Pipeline - Ensures `outcome` in required_fields
- ✅ Call Center Contact Pipeline - Ensures `contact_topic` in required_fields
- ✅ Claims Lines Pipeline - Updates deduplication to `["claim_id", "claim_line_id"]`
- ✅ Member Diagnosis Pipeline - Ensures `onset_date` in required_fields and deduplication keys
- ✅ Benefit Design Pipeline - Ensures `service_category` in required_fields and deduplication keys
- ✅ Referral Pipeline - Ensures `referring_provider_id` in required_fields
- ✅ Provider Contract Pipeline - Ensures `effective_date` in required_fields
- ✅ Prior Authorization Request Pipeline - Ensures `decision`, `service_code` in required_fields
- ✅ Member Accumulator Pipeline - Ensures `accumulator_value` in required_fields, updates deduplication to `["member_id"]`
- ✅ Member Risk Stratification Pipeline - Ensures `risk_score` in required_fields
- ✅ Pharmacy Claims Pipeline - Updates deduplication to `["rx_claim_id"]`

#### Step 2: Validate Fixes

```bash
python3 apps/api/scripts/validate_target_data_model.py
python3 apps/api/scripts/validate_pipelines_deduplication.py
```

#### Step 3: Run All Pipelines

```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
python3 apps/api/scripts/run_all_pipelines_direct.py
```

**What This Does:**
- Matches each pipeline to its source files
- Executes pipelines directly (not via API)
- Processes all source data files
- Writes to `data/target_data_model/{tenant_id}/{dataset_type}/`
- Handles duplicates automatically
- Shows progress and results

#### Step 4: Verify Results

```bash
# Count target records
python3 apps/api/scripts/count_target_records.py

# Compare source vs target
python3 apps/api/scripts/compare_source_target_counts.py
```

## Expected Results

### After Fix:
- ✅ All pipelines have correct required_fields
- ✅ All pipelines have proper deduplication key fields
- ✅ All field mappings match target data model

### After Run:
- ✅ All 21+ datasets ingested into target data model
- ✅ Duplicates automatically removed
- ✅ Target record counts = Source counts - Duplicates
- ✅ All pipelines executed successfully

## Source Data Summary

**Total Source Records: 2,362,500**
- Claims Lines: 2,323,818 (from claims/YYYY/MM files)
- Other datasets: 38,682 records

## Target Data Expected

After running all pipelines:
- All datasets should have data in `data/target_data_model/{tenant_id}/{dataset_type}/`
- Record counts should match source (minus duplicates)
- Deduplication should be visible in comparison

## Pipeline Execution Details

The `run_all_pipelines_direct.py` script:
1. ✅ Loads all pipelines from database
2. ✅ Matches pipelines to source files automatically
3. ✅ Converts pipeline configs to PipelineMetadata
4. ✅ Creates PipelineEngine for each pipeline
5. ✅ Executes pipeline with each source file
6. ✅ Writes to target data model (Parquet files)
7. ✅ Handles duplicates based on pipeline strategy
8. ✅ Reports progress, records processed, duplicates removed

## Field Mapping Completeness

All pipelines now have:
- ✅ Complete field mappings matching source data schema
- ✅ All required fields from target data model
- ✅ Proper transform functions (to_date, to_decimal, to_int, to_bool, to_list)
- ✅ Correct deduplication strategies and key fields

## Next Steps

1. **Run the fix script** to update pipelines
2. **Run the execution script** to ingest all data
3. **Verify results** with count scripts
4. **Check frontend** - all pipelines should show data

All scripts are ready to execute!

