# Pipeline Fixes and Execution Summary

## Issues Identified

1. **15 Pipelines Missing Required Fields** - Validation found missing required fields
2. **Incorrect Deduplication** - Some pipelines have wrong deduplication key fields  
3. **Pipelines Not Executed** - Only CLAIMS_LINES has data (other 20+ pipelines haven't been run)

## Solutions Created

### 1. Update Pipeline Script
**File**: `apps/api/scripts/update_pipelines_field_mappings.py`

Fixes 12 pipelines with:
- Missing required fields
- Incorrect deduplication key fields
- Field mapping issues

### 2. Run All Pipelines Script
**File**: `apps/api/scripts/run_all_pipelines_direct.py`

Executes all pipelines:
- Matches pipelines to source files automatically
- Processes all source data files
- Writes to target data model
- Handles duplicates automatically
- Reports progress and results

### 3. All-in-One Script
**File**: `apps/api/scripts/fix_and_run_all_pipelines.py`

Combines all steps:
1. Update pipelines
2. Validate fixes
3. Run all pipelines
4. Count and compare results

## Quick Start

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"

# Run everything
python3 apps/api/scripts/fix_and_run_all_pipelines.py
```

## Pipelines That Will Be Fixed

1. **Claim Header Pipeline** - Add `total_paid`, `total_allowed`, `claim_status`
2. **Appeal Grievance Pipeline** - Ensure `outcome` in required_fields
3. **Call Center Contact Pipeline** - Ensure `contact_topic` in required_fields
4. **Claims Lines Pipeline** - Update deduplication to `["claim_id", "claim_line_id"]`
5. **Member Diagnosis Pipeline** - Ensure `onset_date` in required_fields and deduplication
6. **Benefit Design Pipeline** - Ensure `service_category` in required_fields and deduplication
7. **Referral Pipeline** - Ensure `referring_provider_id` in required_fields
8. **Provider Contract Pipeline** - Ensure `effective_date` in required_fields
9. **Prior Authorization Request Pipeline** - Ensure `decision`, `service_code` in required_fields
10. **Member Accumulator Pipeline** - Ensure `accumulator_value` in required_fields, update deduplication
11. **Member Risk Stratification Pipeline** - Ensure `risk_score` in required_fields
12. **Pharmacy Claims Pipeline** - Update deduplication to `["rx_claim_id"]`

## Source Data Summary

**Total: 2,362,500 records**
- Claims Lines: 2,323,818 (from claims/YYYY/MM files)
- Other 21 datasets: 38,682 records

## Expected Target Results

After running all pipelines:
- ✅ All 21+ datasets in target data model
- ✅ Duplicates automatically removed
- ✅ Target counts = Source counts - Duplicates
- ✅ All field mappings complete
- ✅ All pipelines validated

## Verification

After execution, verify with:
```bash
python3 apps/api/scripts/count_target_records.py
python3 apps/api/scripts/compare_source_target_counts.py
```

All scripts are ready to execute!

