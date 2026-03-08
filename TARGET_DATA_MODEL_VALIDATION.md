# Target Data Model Validation & Record Counting

## ✅ Target Data Model Structure

The target data model definitions are available at **http://localhost:3050/data-mode** and are defined in `apps/web/src/pages/DataModelViewerPage.tsx`.

### Key Models Validated:

1. **ClaimLine** - Primary analytical table for utilization
2. **ClaimHeader** - Institutional/professional claim headers
3. **EligibilityEnrollment** - Coverage fact table
4. **MemberMaster** - Member dimension with SDOH
5. **MemberRiskStratification** - Risk scores and predictions
6. **ProviderMaster** - Provider dimension
7. **FacilityMaster** - Facility dimension
8. **PharmacyClaim** - Pharmacy utilization
9. **MemberAccumulator** - Benefit accumulators
10. **BenefitDesign** - Plan benefit structure
11. **MemberDiagnosis** - Diagnosis history
12. **ProblemList** - Problem list/registry
13. **EpisodeOfCare** - Episode grouping
14. **PriorAuthorizationRequest** - PA tracking
15. **ConcurrentReview** - Admission review
16. **AppealGrievance** - Appeals tracking
17. **Referral** - Referral tracking
18. **CareManagementEnrollment** - Care management programs
19. **CallCenterContact** - Member contacts
20. **MarketEvent** - External context
21. **NetworkConfiguration** - Provider-network relationships
22. **ProviderContract** - Contract and rates

## 🔍 Validation Scripts Created

### 1. `validate_target_data_model.py`
Validates that pipelines match target data model structures:
- Checks target model names match definitions
- Validates required fields
- Verifies deduplication key fields

**Run:**
```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
python3 apps/api/scripts/validate_target_data_model.py
```

### 2. `validate_pipelines_deduplication.py`
Validates deduplication configuration:
- Checks all pipelines have deduplication strategy
- Verifies KEY_FIELDS have key_fields specified
- Confirms HASH strategy is properly configured

**Run:**
```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
python3 apps/api/scripts/validate_pipelines_deduplication.py
```

## 📊 Record Counting Scripts

### 3. `count_source_records.py`
Counts records in source data files **before** pipeline runs:
- Counts all CSV/Parquet files in `data/source_data/synthetic/`
- Handles claims files organized by year/month
- Saves counts to `data/source_record_counts.json`

**Run:**
```bash
python3 apps/api/scripts/count_source_records.py
```

**Output:**
- Prints record counts for each dataset
- Saves JSON file with timestamp and counts
- Shows total source records

### 4. `count_target_records.py`
Counts records in target data model **after** pipeline runs:
- Counts Parquet files in `data/target_data_model/{tenant_id}/`
- Organized by dataset type
- Saves counts to `data/target_record_counts.json`

**Run:**
```bash
python3 apps/api/scripts/count_target_records.py
```

**Output:**
- Prints record counts for each target dataset
- Saves JSON file with timestamp and counts
- Shows total target records

### 5. `compare_source_target_counts.py`
Compares source vs target counts:
- Loads both source and target count files
- Shows before/after comparison
- Calculates deduplication rate
- Identifies datasets not yet ingested

**Run:**
```bash
python3 apps/api/scripts/compare_source_target_counts.py
```

**Output:**
- Side-by-side comparison table
- Difference calculation
- Deduplication analysis
- Status indicators (✅ Match, ⚠️ Not Run, etc.)

## 🔄 Deduplication Strategy

All pipelines are configured with deduplication:

### KEY_FIELDS Strategy
- Uses specified key fields to identify duplicates
- Example: `["claim_id", "claim_line_id"]` for Claims Lines
- Drops duplicates, keeps first occurrence

### HASH Strategy
- Uses `record_hash` field for deduplication
- Computed from record content (excluding metadata)
- Ensures exact duplicate detection

### Pipeline Engine Behavior
The `PipelineEngine._deduplicate()` method:
1. Checks deduplication strategy
2. Removes duplicates based on strategy
3. Returns deduplicated DataFrame and duplicate count
4. Logs duplicate removal in pipeline run metadata

## 📋 Workflow

### Before Pipeline Runs:
```bash
# 1. Count source records
python3 apps/api/scripts/count_source_records.py

# 2. Validate pipelines
python3 apps/api/scripts/validate_target_data_model.py
python3 apps/api/scripts/validate_pipelines_deduplication.py
```

### After Pipeline Runs:
```bash
# 3. Count target records
python3 apps/api/scripts/count_target_records.py

# 4. Compare counts
python3 apps/api/scripts/compare_source_target_counts.py
```

## ✅ Expected Results

### Source Data:
- All 21+ datasets counted
- Claims files by year/month
- Total source record count

### Target Data:
- Records organized by dataset type
- Deduplicated records (target ≤ source)
- Total target record count

### Comparison:
- Source count: Total records in source files
- Target count: Total records after deduplication
- Difference: Number of duplicates removed
- Deduplication rate: Percentage of duplicates removed

## 🎯 Key Points

1. **Deduplication is Automatic**: Pipelines handle duplicates during ingestion
2. **Key Fields Defined**: Each pipeline has appropriate key fields for deduplication
3. **Record Counting**: Scripts track before/after counts
4. **Validation**: Scripts ensure pipelines match target data model
5. **Target Structure**: Matches definitions at http://localhost:3050/data-mode

All scripts are ready to use!

