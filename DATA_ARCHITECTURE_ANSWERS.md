# Data Architecture - Complete Answers

## 1. Where is Source Data Stored?

**Answer:** Source data is stored in **file system directories**, not in database tables.

**Location:**
- Primary location: `apps/data/source_data/synthetic/` (for synthetic/generated data)
- Alternative: `data/source_data/` (legacy location)
- Structure: Organized by dataset type (e.g., `claims/`, `enrollment.csv`, `providers.csv`)

**Evidence:**
- `scripts/run_all_pipelines.py` line 22: `SYNTHETIC_DATA_DIR = Path(__file__).parent.parent / "data" / "source_data" / "synthetic"`
- Pipelines read from these file locations when executed

---

## 2. How Much Data and What Date Ranges?

**Answer:** Data volume and date ranges vary by dataset:

**Claims Data:**
- **Volume:** ~1.17 million claim lines (from data quality report)
- **Format:** CSV files, partitioned by year/month (e.g., `claims/2024/01/claims_2024_01.csv`)
- **Date Range:** Typically 24 months of historical data (configurable)

**Enrollment Data:**
- **Volume:** ~50,000 enrollment records
- **Format:** CSV or Parquet files

**Provider Data:**
- **Volume:** ~5,000 provider records
- **Format:** CSV or Parquet files

**Other Datasets:**
- Various volumes (100-3,600 rows) for additional datasets like PHARMACY_CLAIMS, MEMBER_MASTER, etc.

**Note:** Exact date ranges depend on when synthetic data was generated. The system supports configurable date ranges (typically 24 months).

---

## 3. Source and Target Locations for Pipelines?

**Answer:**

**Source Location (Input):**
- `apps/data/source_data/synthetic/` or `data/source_data/synthetic/`
- Files can be uploaded via frontend (temporary upload) or provided via `source_uri`
- When pipelines run from frontend, files are uploaded to a temporary location first

**Target Location (Output):**
- `apps/data/target_data_model/{tenant_id}/{dataset_type}/`
- Example: `apps/data/target_data_model/00000000-0000-0000-0000-000000000001/CLAIMS_LINES/claims_lines.parquet`
- **Format:** Parquet files (preferred) or CSV files
- **Structure:** One consolidated file per dataset type (not timestamped)

**Evidence:**
- `apps/api/src/uepi_api/routers/pipelines.py` lines 252-257:
  ```python
  output_dir = project_data_root / "target_data_model" / str(current_user.tenant_id) / pipeline_metadata.target_dataset_type
  output_path = output_dir / f"{pipeline_metadata.target_dataset_type.lower()}.parquet"
  ```

---

## 4. Are Pipelines Loading Data to Database Tables?

**Answer:** **NO** - Pipelines currently write to **file system (Parquet/CSV)**, NOT database tables.

**Current Behavior:**
- Pipelines transform and validate source data
- Output is written to `apps/data/target_data_model/{tenant_id}/{dataset_type}/` as Parquet or CSV files
- **No database tables are created or populated by pipelines**

**Evidence:**
- `packages/common/src/uepi_common/ingestion/pipeline_engine.py` - The `execute()` method writes to file paths, not database
- `apps/api/src/uepi_api/routers/pipelines.py` lines 252-262 - Output path is a file path, not a database table

**Note:** This is a **critical gap** - the system should load data into database tables, but currently only writes to files.

---

## 5. Where Does Baseline Analysis Take Data From?

**Answer:** Baseline analysis reads from **target data model files** (Parquet/CSV), NOT database.

**Data Source:**
- `apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/claims_lines.csv` (or `.parquet`)
- `apps/data/target_data_model/{tenant_id}/ENROLLMENT/enrollment.csv`
- `apps/data/target_data_model/{tenant_id}/PROVIDER_MASTER/provider_master.csv`
- Additional datasets from target data model directory

**Evidence:**
- `apps/api/src/uepi_api/routers/analyses.py` lines 762-866:
  ```python
  target_data_root = apps_dir / "data" / "target_data_model" / str(current_user.tenant_id)
  claims_dir = target_data_root / "CLAIMS_LINES"
  # Looks for .csv or .parquet files
  ```

---

## 6. Is Baseline Using Database or Files as Source?

**Answer:** **FILES** - Baseline analysis uses **file system** as source, NOT database.

**Current Implementation:**
- Baseline analysis engine (`BaselineAnalysisEngine`) accepts file paths
- It reads from Parquet/CSV files in the target data model directory
- Results are stored in database (`BaselineAnalysisResult` table), but input data comes from files

**Evidence:**
- `apps/api/src/uepi_api/routers/analyses.py` line 910: `engine.run_baseline_analysis(claims_data_path=claims_path, ...)` - file paths, not database queries
- `packages/common/src/uepi_common/analytics/baseline.py` - `run_baseline_analysis()` method accepts file paths

**Note:** This is another **critical gap** - baseline should read from database tables, not files.

---

## 7. Where Does Policy Impact Take Data From?

**Answer:** Policy impact analysis reads from **target data model files** (via worker tasks), NOT database.

**Data Source:**
- Worker tasks (`apps/worker/src/uepi_worker/tasks.py`) load data from files
- Similar to baseline - reads from `apps/data/target_data_model/` directory
- Uses file-based data loading functions

**Evidence:**
- `apps/worker/src/uepi_worker/impact_analysis.py` - Impact analysis functions likely read from files
- Worker tasks are triggered from API but execute file-based data loading

**Note:** This is also a **critical gap** - policy impact should read from database tables.

---

## 8. Where is Data Quality Validated Against (Database Tables or Files, Source or Target)?

**Answer:** Data quality is validated against **TARGET data model files** (Parquet/CSV), NOT database tables.

**Validation Target:**
- `apps/data/target_data_model/{tenant_id}/` directory
- Validates all datasets in target data model (CLAIMS_LINES, ENROLLMENT, PROVIDERS, etc.)
- Reads from Parquet and CSV files

**Evidence:**
- `scripts/comprehensive_data_quality_check.py` line 29: `TARGET_DATA_DIR = PROJECT_ROOT / "apps" / "data" / "target_data_model" / TENANT_ID`
- Lines 487-489: Data paths point to target data model files
- Lines 444-478: `load_data_from_database_or_file()` function tries database first, but falls back to files (and files are what actually exist)

**Current Behavior:**
- Script attempts to load from database tables first (lines 444-478)
- But since pipelines don't write to database, it falls back to files
- **Actual validation is against target data model files**

**Note:** This is a **critical gap** - data quality should validate against database tables, not files.

---

## 9. Are Pipelines Configured on Frontend Used to Load Data or Scripts?

**Answer:** **Both** - Pipelines can be triggered from:
1. **Frontend UI** - User uploads file and runs pipeline via API
2. **Scripts** - Automated scripts can call pipeline API endpoints

**Frontend Execution:**
- User selects pipeline in UI (`apps/web/src/pages/PipelinesPage.tsx`)
- Uploads source file via file picker
- Calls `POST /api/v1/pipelines/{pipeline_id}/run` with file upload
- Pipeline executes and writes to target data model directory

**Script Execution:**
- `scripts/run_all_pipelines.py` - Runs pipelines via API calls
- Can be automated or run manually

**Evidence:**
- `apps/web/src/pages/PipelinesPage.tsx` lines 134-164: Frontend pipeline execution
- `apps/api/src/uepi_api/routers/pipelines.py` lines 175-267: API endpoint for running pipelines
- `scripts/run_all_pipelines.py`: Script-based execution

**Note:** Regardless of how pipelines are triggered, they **always write to files**, not database.

---

## 10. Where Are Observations Running From (Database or Files)?

**Answer:** Observations likely read from **files** (similar to baseline and impact analysis), NOT database.

**Current Implementation:**
- Observation analysis follows similar pattern to baseline/impact
- Reads from target data model files
- Results stored in database, but input data from files

**Evidence:**
- `apps/api/src/uepi_api/routers/analyses_file.py` - File-based observation analysis (legacy)
- `apps/web/src/pages/ObservationAnalysisPage.tsx` - Frontend for observations
- Worker tasks likely use file-based data loading

**Note:** This is also a **critical gap** - observations should read from database tables.

---

## Summary of Critical Gaps

### ❌ **Current State (File-Based):**
1. **Pipelines** → Write to files (`apps/data/target_data_model/`)
2. **Baseline Analysis** → Reads from files
3. **Policy Impact** → Reads from files
4. **Data Quality** → Validates files
5. **Observations** → Reads from files

### ✅ **Target State (Database-Based):**
1. **Pipelines** → Should write to database tables
2. **Baseline Analysis** → Should read from database tables
3. **Policy Impact** → Should read from database tables
4. **Data Quality** → Should validate database tables
5. **Observations** → Should read from database tables

### 🔧 **What Needs to Be Done:**
1. **Modify Pipeline Engine** to write to database tables instead of files
2. **Modify Baseline Analysis** to read from database tables
3. **Modify Policy Impact** to read from database tables
4. **Modify Data Quality** to validate database tables
5. **Modify Observations** to read from database tables

**Current Architecture:** File-based storage with database for metadata/results only
**Target Architecture:** Database-first with files as optional export/backup

