# Pipeline Setup Complete

## Summary
Comprehensive data pipelines have been configured to ingest source data into target canonical models. All pipelines are stored in the database and visible from the frontend.

## Pipelines Created

### 1. Claims Lines Pipeline (CSV)
- **Source**: CSV files
- **Target**: `ClaimsLine` canonical model
- **Key Fields**: claim_id, claim_line_id, member_id, provider_id, service_date, lob, market, service_category, place_of_service, units, allowed_amount, paid_amount, in_network
- **Transformations**: Date parsing, decimal conversion, boolean conversion, list parsing for ICD codes
- **Deduplication**: By claim_id + claim_line_id
- **Mode**: APPEND

### 2. Claims Lines Pipeline (Parquet)
- **Source**: Parquet files
- **Target**: `ClaimsLine` canonical model
- **Same mappings as CSV version, optimized for Parquet format**

### 3. Enrollment Records Pipeline
- **Source**: CSV files
- **Target**: `EnrollmentRecord` canonical model
- **Key Fields**: member_id, enrollment_month, lob, market, age_band, gender, risk_score, network_tier, enrolled_flag
- **Transformations**: Date parsing, decimal conversion for risk_score, boolean conversion
- **Deduplication**: By member_id + enrollment_month
- **Mode**: APPEND

### 4. Member Master Pipeline
- **Source**: CSV files
- **Target**: `MemberMaster` canonical model
- **Key Fields**: member_id (primary), demographics, SDOH fields, location data
- **Transformations**: Date parsing, integer conversion, boolean conversion
- **Deduplication**: By member_id
- **Mode**: UPSERT (updates existing records)

### 5. Provider Master Pipeline
- **Source**: CSV files
- **Target**: `ProviderMaster` canonical model
- **Key Fields**: provider_id (primary), npi, provider_name, specialty, market, network_tier
- **Transformations**: Boolean conversion for facility_flag
- **Deduplication**: By provider_id
- **Mode**: UPSERT

### 6. Pharmacy Claims Pipeline
- **Source**: CSV files
- **Target**: `PharmacyClaim` canonical model
- **Key Fields**: rx_claim_id, member_id, fill_date, ndc, days_supply, quantity, paid_amount, allowed_amount
- **Transformations**: Date parsing, integer/decimal conversion, boolean flags
- **Deduplication**: By rx_claim_id
- **Mode**: APPEND

## Field Mappings

Each pipeline includes comprehensive field mappings with:
- **Source Field**: Name in source data
- **Target Field**: Name in canonical model
- **Required**: Whether field is required
- **Transform Functions**: 
  - `to_date`: Parse date strings
  - `to_decimal`: Convert to decimal/numeric
  - `to_int`: Convert to integer
  - `to_bool`: Convert to boolean
  - `to_list`: Parse comma-separated or JSON lists

## Pipeline Configuration

All pipelines include:
- **Deduplication Strategy**: KEY_FIELDS (using primary key combinations)
- **Control Fields**: created_at, updated_at, active_flag
- **Batch Size**: 10,000 records
- **Error Threshold**: 5% (0.05)
- **Continue on Error**: True
- **Status**: ACTIVE
- **Tags**: For categorization and filtering

## Database Storage

- All pipelines stored in `pipelines` table
- Pipeline runs tracked in `pipeline_runs` table
- Accessible via `/api/v1/pipelines` endpoint
- Visible in frontend pipeline management UI

## Frontend Visibility

Pipelines are accessible via:
- **GET /api/v1/pipelines**: List all pipelines
- **GET /api/v1/pipelines/{pipeline_id}**: Get pipeline details
- **POST /api/v1/pipelines**: Create new pipeline
- **PUT /api/v1/pipelines/{pipeline_id}**: Update pipeline
- **DELETE /api/v1/pipelines/{pipeline_id}**: Delete pipeline

## Source Data Location

Source data should be placed in:
- **Historical Load**: `data/source_data/historical/`
- **Daily Loads**: `data/source_data/daily/`

Each ingestion requires a manifest file describing:
- Dataset type
- Source files
- Expected record counts
- Validation rules

## Next Steps

1. **Place source data files** in the appropriate directories
2. **Create ingestion manifests** for each dataset
3. **Trigger pipeline runs** via API or scheduled execution
4. **Monitor pipeline runs** via `/api/v1/pipelines/{pipeline_id}/runs`
5. **View processed data** in target data model via data explorer

## Scripts

- `seed_comprehensive_pipelines.py`: Creates all predefined pipelines
- `04_seed_pipelines.py`: Seeds pipelines from JSON files + comprehensive pipelines
- `initialize_system.py`: Orchestrates all setup including pipeline seeding

