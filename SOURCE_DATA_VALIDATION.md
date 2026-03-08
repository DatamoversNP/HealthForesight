# Source Data Validation and Pipeline Configuration

## ✅ Source Data Location

Source data exists in: `/Users/nilesh/Downloads/uepi-migration-20260123-151729/data/source_data/synthetic/`

## 📊 Available Source Data Files

### Core Datasets (CSV & Parquet)
1. **member_master.csv/parquet** - Member demographic and SDOH data
2. **eligibility_enrollment.csv/parquet** - Enrollment records
3. **provider_master.csv/parquet** - Provider directory
4. **facility_master.csv/parquet** - Facility information
5. **pharmacy_claims.csv/parquet** - Pharmacy claims
6. **claim_header.csv/parquet** - Claim headers
7. **risk_stratification.csv/parquet** - Member risk scores
8. **member_accumulator.csv/parquet** - Member benefit accumulators
9. **member_diagnosis.csv/parquet** - Member diagnoses
10. **network_configuration.csv/parquet** - Network configuration
11. **provider_contract.csv/parquet** - Provider contracts
12. **benefit_design.csv/parquet** - Benefit design
13. **prior_authorization_request.csv/parquet** - Prior authorization requests
14. **concurrent_review.csv/parquet** - Concurrent reviews
15. **appeal_grievance.csv/parquet** - Appeals and grievances
16. **referral.csv/parquet** - Referrals
17. **care_management_enrollment.csv/parquet** - Care management enrollment
18. **call_center_contact.csv/parquet** - Call center contacts
19. **episode_of_care.csv/parquet** - Episodes of care
20. **problem_list.csv/parquet** - Problem lists
21. **market_event.csv/parquet** - Market events

### Claims Data (Organized by Year/Month)
Located in: `data/source_data/synthetic/claims/`
- **2023**: December (claims_2023_12.csv/parquet)
- **2024**: January through December (12 months)
- **2025**: January through November (11 months)
- **2026**: (empty, ready for future data)

## 🔧 Data Generation Script

**Main Script**: `scripts/generate_all_comprehensive_synthetic.py`

This script generates all comprehensive synthetic datasets for:
- Member Master
- Eligibility Enrollment
- Provider Master
- Facility Master
- Claims (by month)
- Pharmacy Claims
- And all other canonical models

### Usage:
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 scripts/generate_all_comprehensive_synthetic.py \
  --members 10000 \
  --providers 1000 \
  --months 24 \
  --out data/source_data/synthetic
```

## 📋 Source Data Schema Validation

### Member Master Schema
- `member_id` (required)
- `subscriber_id`, `family_id`
- `dob`, `age`, `gender`, `race`, `ethnicity`
- `address_zip5`, `county`, `state`, `rural_flag`
- `tenant_id`, `source_system`, `source_file_id`, `ingestion_id`

### Eligibility Enrollment Schema
- `member_id` (required)
- `coverage_month` (required)
- `plan_id` (required)
- `line_of_business` (required)
- `coverage_status` (required)
- `tenant_id`, `source_system`, `source_file_id`, `ingestion_id`

### Provider Master Schema
- `provider_id` (required)
- `npi`, `provider_name`
- `provider_type`, `specialty_primary`
- `tenant_id`, `source_system`, `source_file_id`, `ingestion_id`

### Claims Lines Schema (from claims/YYYY/MM files)
- `claim_id`, `claim_line_id`, `member_id`, `provider_id`
- `service_date`, `paid_date`
- `lob`, `market`
- `cpt_code`, `hcpcs_code`
- `service_category`, `place_of_service`
- `units`, `allowed_amount`, `paid_amount`
- `in_network_flag`

## 🔄 Pipeline Mappings

### 1. Claims Lines Pipeline
**Source**: `data/source_data/synthetic/claims/YYYY/MM/claims_YYYY_MM.csv` or `.parquet`
**Target**: `ClaimsLine` canonical model
**Key Mappings**:
- `claim_id` → `claim_id`
- `claim_line_id` → `claim_line_id`
- `member_id` → `member_id`
- `provider_id` → `provider_id`
- `service_date` → `service_date` (to_date)
- `paid_date` → `paid_date` (to_date)
- `lob` → `lob`
- `market` → `market`
- `cpt_code` → `cpt_code`
- `service_category` → `service_category`
- `place_of_service` → `place_of_service`
- `units` → `units` (to_decimal)
- `allowed_amount` → `allowed_amount` (to_decimal)
- `paid_amount` → `paid_amount` (to_decimal)
- `in_network_flag` → `in_network` (to_bool)

### 2. Enrollment Records Pipeline
**Source**: `data/source_data/synthetic/eligibility_enrollment.csv` or `.parquet`
**Target**: `EnrollmentRecord` canonical model
**Key Mappings**:
- `member_id` → `member_id`
- `coverage_month` → `enrollment_month` (to_date, first day of month)
- `line_of_business` → `lob`
- `market` → `market` (may need derivation)
- `plan_id` → (may map to product_type)
- `coverage_status` → `enrolled_flag` (ACTIVE = true)

### 3. Member Master Pipeline
**Source**: `data/source_data/synthetic/member_master.csv` or `.parquet`
**Target**: `MemberMaster` canonical model
**Key Mappings**:
- `member_id` → `member_id`
- `dob` → `dob` (to_date)
- `age` → `age` (to_int)
- `gender` → `gender`
- `race` → `race`
- `ethnicity` → `ethnicity`
- `address_zip5` → `address_zip5`
- `county` → `county`
- `state` → `state`
- `rural_flag` → `rural_flag` (to_bool)

### 4. Provider Master Pipeline
**Source**: `data/source_data/synthetic/provider_master.csv` or `.parquet`
**Target**: `ProviderMaster` canonical model
**Key Mappings**:
- `provider_id` → `provider_id`
- `npi` → `npi`
- `provider_name` → `provider_name`
- `specialty_primary` → `specialty`
- `provider_type` → `provider_type`

### 5. Pharmacy Claims Pipeline
**Source**: `data/source_data/synthetic/pharmacy_claims.csv` or `.parquet`
**Target**: `PharmacyClaim` canonical model
**Key Mappings**:
- `rx_claim_id` → `rx_claim_id`
- `member_id` → `member_id`
- `fill_date` → `fill_date` (to_date)
- `ndc` → `ndc`
- `days_supply` → `days_supply` (to_int)
- `quantity` → `quantity` (to_decimal)
- `paid_amount` → `paid_amount` (to_decimal)
- `allowed_amount` → `allowed_amount` (to_decimal)

## 📁 Directory Structure

```
data/source_data/
├── synthetic/
│   ├── member_master.csv/parquet
│   ├── eligibility_enrollment.csv/parquet
│   ├── provider_master.csv/parquet
│   ├── pharmacy_claims.csv/parquet
│   ├── claims/
│   │   ├── 2023/
│   │   │   └── claims_2023_12.csv/parquet
│   │   ├── 2024/
│   │   │   ├── claims_2024_01.csv/parquet
│   │   │   └── ... (12 months)
│   │   └── 2025/
│   │       └── ... (11 months)
│   └── ... (other datasets)
└── 00000000-0000-0000-0000-000000000001/
    ├── daily/
    └── historical/
```

## ✅ Validation Status

- ✅ Source data files exist
- ✅ Both CSV and Parquet formats available
- ✅ Claims data organized by year/month
- ✅ All major datasets present
- ✅ Data generation script identified
- ✅ Pipelines configured for mappings

## 🚀 Next Steps

1. **Verify Pipeline Mappings**: Ensure field mappings match source data schema
2. **Create Ingestion Manifests**: For each dataset type
3. **Run Pipelines**: Ingest source data into target canonical models
4. **Validate Target Data**: Check data quality in target data model

