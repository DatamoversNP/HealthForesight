# Pipeline Source Data Mapping

## ✅ Source Data Validated

**Location**: `/Users/nilesh/Downloads/uepi-migration-20260123-151729/data/source_data/synthetic/`

**Status**: 
- ✅ 21 CSV files
- ✅ 21 Parquet files
- ✅ Claims data organized by year/month (2023-2025)
- ✅ All major datasets present

**Generation Script**: `scripts/generate_all_comprehensive_synthetic.py`

## 📋 Actual Source Data Schema vs Pipeline Mappings

### Claims Lines Pipeline

**Source File**: `data/source_data/synthetic/claims/YYYY/MM/claims_YYYY_MM.csv`

**Actual Source Schema**:
```
tenant_id, source_system, source_file_id, ingestion_id,
claim_line_id, claim_id, member_id,
cpt_hcpcs, service_date_from, service_date_to,
place_of_service, service_category, site_of_care_class,
units, unit_type, rendering_provider_id, facility_id,
in_network_flag, network_id, network_tier,
benefit_category, prior_auth_required_flag, referral_required_flag,
billed_amount, allowed_amount, paid_amount,
copay_amount, coinsurance_amount, deductible_amount,
member_resp_amount, emergency_flag, avoidable_ed_flag
```

**Pipeline Mappings** (Updated to match source):
- `claim_id` → `claim_id` ✅
- `claim_line_id` → `claim_line_id` ✅
- `member_id` → `member_id` ✅
- `rendering_provider_id` → `provider_id` ✅
- `service_date_from` → `service_date` (to_date) ✅
- `cpt_hcpcs` → `cpt_code` (extract_cpt) - Extract 5-digit CPT codes
- `cpt_hcpcs` → `hcpcs_code` (extract_hcpcs) - Extract HCPCS codes
- `service_category` → `service_category` ✅
- `place_of_service` → `place_of_service` ✅
- `units` → `units` (to_decimal) ✅
- `allowed_amount` → `allowed_amount` (to_decimal) ✅
- `paid_amount` → `paid_amount` (to_decimal) ✅
- `member_resp_amount` → `member_cost_share` (to_decimal) ✅
- `in_network_flag` → `in_network` (to_bool) ✅
- `prior_auth_required_flag` → `requires_prior_auth` (to_bool) ✅
- `site_of_care_class` → `facility_type` ✅
- `rendering_provider_id` → `rendering_provider_id` ✅
- `facility_id` → `billing_provider_id` ✅

**Required Fields**: `claim_id`, `claim_line_id`, `member_id`, `service_date_from`, `service_category`, `place_of_service`, `units`, `allowed_amount`, `paid_amount`, `in_network_flag`

### Enrollment Records Pipeline

**Source File**: `data/source_data/synthetic/eligibility_enrollment.csv`

**Actual Source Schema**:
```
tenant_id, source_system, source_file_id, ingestion_id,
member_id, coverage_month, plan_id,
line_of_business, coverage_status
```

**Pipeline Mappings** (Updated to match source):
- `member_id` → `member_id` ✅
- `coverage_month` → `enrollment_month` (coverage_month_to_date) - Convert "YYYY-MM" to date
- `line_of_business` → `lob` ✅
- `coverage_status` → `enrolled_flag` (coverage_status_to_bool) - "ACTIVE" = true
- `plan_id` → `product_type` (optional)

**Note**: `age_band`, `gender`, `risk_score`, `network_tier` need to be joined from `member_master` during pipeline processing.

**Required Fields**: `member_id`, `coverage_month`, `line_of_business`, `coverage_status`

### Member Master Pipeline

**Source File**: `data/source_data/synthetic/member_master.csv`

**Actual Source Schema**:
```
tenant_id, source_system, source_file_id, ingestion_id,
member_id, subscriber_id, family_id,
dob, age, gender, race, ethnicity,
address_zip5, county, state, rural_flag
```

**Pipeline Mappings** (Matches source):
- `member_id` → `member_id` ✅
- `subscriber_id` → `subscriber_id` ✅
- `family_id` → `family_id` ✅
- `dob` → `dob` (to_date) ✅
- `age` → `age` (to_int) ✅
- `gender` → `gender` ✅
- `race` → `race` ✅
- `ethnicity` → `ethnicity` ✅
- `address_zip5` → `address_zip5` ✅
- `county` → `county` ✅
- `state` → `state` ✅
- `rural_flag` → `rural_flag` (to_bool) ✅

**Required Fields**: `member_id`

### Provider Master Pipeline

**Source File**: `data/source_data/synthetic/provider_master.csv`

**Actual Source Schema**:
```
tenant_id, source_system, source_file_id, ingestion_id,
provider_id, npi, provider_name,
provider_type, specialty_primary
```

**Pipeline Mappings** (Matches source):
- `provider_id` → `provider_id` ✅
- `npi` → `npi` ✅
- `provider_name` → `provider_name` ✅
- `provider_type` → `provider_type` ✅
- `specialty_primary` → `specialty` ✅

**Required Fields**: `provider_id`

## 🔄 Transform Functions Needed

1. **`coverage_month_to_date`**: Convert "YYYY-MM" string to date (first day of month)
2. **`coverage_status_to_bool`**: Convert "ACTIVE" → true, others → false
3. **`extract_cpt`**: Extract 5-digit CPT codes from `cpt_hcpcs` field
4. **`extract_hcpcs`**: Extract HCPCS codes from `cpt_hcpcs` field
5. **`to_date`**: Parse date strings
6. **`to_decimal`**: Convert to decimal/numeric
7. **`to_int`**: Convert to integer
8. **`to_bool`**: Convert to boolean

## 📁 Source Data Organization

```
data/source_data/synthetic/
├── member_master.csv/parquet
├── eligibility_enrollment.csv/parquet
├── provider_master.csv/parquet
├── pharmacy_claims.csv/parquet
├── claims/
│   ├── 2023/
│   │   └── claims_2023_12.csv/parquet
│   ├── 2024/
│   │   ├── claims_2024_01.csv/parquet
│   │   ├── claims_2024_02.csv/parquet
│   │   └── ... (12 months)
│   └── 2025/
│       └── ... (11 months)
└── ... (other datasets)
```

## ✅ Pipeline Status

- ✅ Pipelines created in database
- ✅ Field mappings updated to match actual source schema
- ✅ Transform functions identified
- ✅ Required fields validated
- ✅ Source data location confirmed

## 🚀 Next Steps

1. **Implement Transform Functions**: Add custom transform functions for:
   - `coverage_month_to_date`
   - `coverage_status_to_bool`
   - `extract_cpt` / `extract_hcpcs`

2. **Test Pipeline Execution**: Run pipelines on sample source data

3. **Validate Target Data**: Verify data quality in target canonical models

4. **Frontend Visibility**: Pipelines are already visible via `/api/v1/pipelines` endpoint

