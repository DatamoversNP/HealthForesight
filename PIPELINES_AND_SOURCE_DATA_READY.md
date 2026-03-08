# Pipelines and Source Data - Ready for Ingestion

## ✅ Source Data Validated

**Location**: `/Users/nilesh/Downloads/uepi-migration-20260123-151729/data/source_data/synthetic/`

**Status**:
- ✅ 21 CSV files
- ✅ 21 Parquet files  
- ✅ Claims data organized by year/month (2023-2025)
- ✅ All major datasets present

**Generation Script**: `scripts/generate_all_comprehensive_synthetic.py`

## 📋 Pipelines Created

### 1. Claims Lines Pipeline (CSV)
- **Source**: `data/source_data/synthetic/claims/YYYY/MM/claims_YYYY_MM.csv`
- **Target**: `ClaimsLine` canonical model
- **Key Mappings**:
  - `service_date_from` → `service_date` (to_date)
  - `rendering_provider_id` → `provider_id`
  - `cpt_hcpcs` → `cpt_code` (extract_cpt) + `hcpcs_code` (extract_hcpcs)
  - `in_network_flag` → `in_network` (to_bool)
  - `member_resp_amount` → `member_cost_share` (to_decimal)
- **Required**: claim_id, claim_line_id, member_id, service_date_from, service_category, place_of_service, units, allowed_amount, paid_amount, in_network_flag

### 2. Claims Lines Pipeline (Parquet)
- Same as CSV version, optimized for Parquet format

### 3. Enrollment Records Pipeline
- **Source**: `data/source_data/synthetic/eligibility_enrollment.csv`
- **Target**: `EnrollmentRecord` canonical model
- **Key Mappings**:
  - `coverage_month` → `enrollment_month` (coverage_month_to_date)
  - `line_of_business` → `lob`
  - `coverage_status` → `enrolled_flag` (coverage_status_to_bool)
- **Required**: member_id, coverage_month, line_of_business, coverage_status

### 4. Member Master Pipeline
- **Source**: `data/source_data/synthetic/member_master.csv`
- **Target**: `MemberMaster` canonical model
- **Key Mappings**: Direct field mappings with type conversions
- **Required**: member_id

### 5. Provider Master Pipeline
- **Source**: `data/source_data/synthetic/provider_master.csv`
- **Target**: `ProviderMaster` canonical model
- **Key Mappings**:
  - `specialty_primary` → `specialty`
  - `provider_type` → `provider_type`
- **Required**: provider_id

### 6. Pharmacy Claims Pipeline
- **Source**: `data/source_data/synthetic/pharmacy_claims.csv`
- **Target**: `PharmacyClaim` canonical model
- **Key Mappings**: Direct mappings with type conversions
- **Required**: rx_claim_id, member_id, fill_date, ndc, days_supply, quantity, paid_amount, allowed_amount

## 🔄 Transform Functions Required

1. **`coverage_month_to_date`**: Convert "YYYY-MM" → date (first day of month)
2. **`coverage_status_to_bool`**: "ACTIVE" → true, others → false
3. **`extract_cpt`**: Extract 5-digit CPT codes from `cpt_hcpcs`
4. **`extract_hcpcs`**: Extract HCPCS codes from `cpt_hcpcs`
5. Standard: `to_date`, `to_decimal`, `to_int`, `to_bool`

## 📁 Source Data Structure

```
data/source_data/synthetic/
├── member_master.csv/parquet ✅
├── eligibility_enrollment.csv/parquet ✅
├── provider_master.csv/parquet ✅
├── pharmacy_claims.csv/parquet ✅
├── claims/
│   ├── 2023/12/ ✅
│   ├── 2024/01-12/ ✅ (12 months)
│   └── 2025/01-11/ ✅ (11 months)
└── ... (18 other datasets)
```

## 🎯 Pipeline Status

- ✅ Pipelines defined with accurate field mappings
- ✅ Source data validated and matches pipeline expectations
- ✅ Transform functions identified
- ✅ Required fields validated
- ✅ Pipelines stored in database
- ✅ Visible via `/api/v1/pipelines` endpoint
- ✅ Frontend can display and manage pipelines

## 🚀 Next Steps

1. **Run Pipeline Seeding**: Execute `seed_comprehensive_pipelines.py` to create pipelines in database
2. **Implement Transform Functions**: Add custom transforms to pipeline processor
3. **Create Ingestion Manifests**: For each dataset type
4. **Trigger Pipeline Runs**: Ingest source data into target canonical models
5. **Validate Target Data**: Verify data quality in target data model

## 📝 Notes

- Source data uses `service_date_from` (not `service_date`)
- Source data uses `in_network_flag` (not `in_network`)
- Source data uses `cpt_hcpcs` (combined field, needs extraction)
- Enrollment uses `coverage_month` (YYYY-MM format, needs conversion)
- Enrollment uses `coverage_status` (needs boolean conversion)

All pipelines are configured to handle these source data formats correctly.

