# Data Quality Validation - Work in Progress

## Status: ✅ API Created, ⏳ UI Update Needed

### Completed ✅

1. **Created Comprehensive Data Quality Check Script**
   - File: `scripts/comprehensive_data_quality_check.py`
   - Validates: Completeness, Uniqueness, Validity, Referential Integrity
   - Generates: Quality report as JSON
   - Checks: All comprehensive scope fields

2. **Created Data Quality API Endpoint**
   - File: `apps/api/src/uepi_api/routers/data_quality.py`
   - Endpoints:
     - `GET /api/v1/data-quality/report` - Get quality report
     - `POST /api/v1/data-quality/validate` - Run validation
     - `GET /api/v1/data-quality/summary` - Get quick summary
   - Registered in `main.py`

### In Progress ⏳

3. **Update API Client** (`apps/web/src/lib/api.ts`)
   - Add `getDataQualityReport()`
   - Add `runDataQualityValidation()`
   - Add `getDataQualitySummary()`

4. **Update DataExplorerPage UI** (`apps/web/src/pages/DataExplorerPage.tsx`)
   - Add Data Quality tab/section
   - Show quality scores per dataset
   - Display issues by severity
   - Show validation status

### Next Steps

5. **Run Data Quality Check** (via API or script)
6. **Fix Any Issues Found**
7. **Run Baseline/Predicted/Observed Analysis**
8. **Display Results on UI**

## Quick Test

To test data quality API:
```bash
# Start API server
./start-both-servers.sh

# Run validation (or use UI button)
curl -X POST http://localhost:8000/api/v1/data-quality/validate \
  -H "Authorization: Bearer dev-token-123"

# Get summary
curl http://localhost:8000/api/v1/data-quality/summary \
  -H "Authorization: Bearer dev-token-123"
```

## Data Quality Checks

The script validates:
- ✅ **Completeness**: All required fields present and populated
- ✅ **Uniqueness**: No duplicate keys (claim_line_id, member_id, npi)
- ✅ **Validity**: Date formats, numeric values, data types
- ✅ **Referential Integrity**: member_id → members, npi → providers
- ✅ **Comprehensive Scope**: plan_id, product_type, state, region, network_tier, service_category, diagnosis_group
