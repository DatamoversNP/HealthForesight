# Database Migration Status Report
## Validation: Is Product 100% on Database (Except Source Data Files)?

**Date**: 2025-01-23  
**Status**: ⚠️ **MIXED - NOT 100% DATABASE**

---

## Executive Summary

The product is **NOT 100% on database**. There is a **dual-mode architecture** where:
- **Primary routers** use **PostgreSQL database** ✅
- **Legacy file-based routers** still exist (with `_file` suffix) ⚠️
- **File storage modules** (37 storage_*.py files) still exist but are **NOT actively used** by main routers
- **Source data files** are correctly handled as temporary files during ingestion ✅

---

## 1. Database Configuration Status

### ✅ Database Mode is Active
- **File**: `apps/api/src/uepi_api/database.py`
- **Status**: `USE_FILE_STORAGE = False` (line 11)
- **Database**: PostgreSQL (required, validated on startup)
- **All models registered**: 40+ database models including:
  - Core: Tenant, User, Role, AuditEvent
  - Policies: Policy, PolicyVersion, PolicyCodeSet, PolicyAssumption, PolicyGuardrail
  - Data: ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB
  - Analysis: Analysis, AnalysisRun, AnalysisResultIndex, BaselineAnalysisResult, ImpactAnalysisResult
  - And 30+ more models

---

## 2. Active Routers Analysis

### ✅ Database-Based Routers (Primary - ACTIVE)

These routers use `get_db()` and database models:

| Router | Status | Uses Database |
|--------|--------|---------------|
| `policies.py` | ✅ Active | ✅ Yes - Uses Policy, PolicyVersion models |
| `analyses.py` | ✅ Active | ✅ Yes - Uses Analysis, AnalysisResultIndex models |
| `ingestions.py` | ✅ Active | ✅ Yes - Uses Ingestion, Dataset models |
| `pipelines.py` | ✅ Active | ✅ Yes - Uses Pipeline, PipelineRun models |
| `datasets.py` | ✅ Active | ✅ Yes - Uses Dataset, ClaimsLineDB models |
| `data_quality.py` | ✅ Active | ✅ Yes - Uses DataQualityReport models |
| `data_health.py` | ✅ Active | ✅ Yes - Uses Dataset, Ingestion models |
| `observations.py` | ✅ Active | ✅ Yes - Uses Observation model |
| `baselines.py` | ✅ Active | ✅ Yes - Uses Baseline model |
| `access.py` | ✅ Active | ✅ Yes - Uses User, Role models |
| `auth.py` | ✅ Active | ✅ Yes - Uses User, Tenant models |
| `admin.py` | ✅ Active | ✅ Yes - Uses database models |
| `scorecards.py` | ✅ Active | ✅ Yes - Uses Scorecard models |
| `exports.py` | ✅ Active | ✅ Yes - Uses Export models |
| `lineage.py` | ✅ Active | ✅ Yes - Uses DatasetSnapshot models |
| `notifications.py` | ✅ Active | ✅ Yes - Uses Notification models |
| `decisions.py` | ✅ Active | ✅ Yes - Uses PolicyDecision models |
| `cohorts.py` | ✅ Active | ✅ Yes - Uses Cohort model |
| `schedules.py` | ✅ Active | ✅ Yes - Uses Schedule model |
| `policy_import.py` | ✅ Active | ✅ Yes - Uses Policy models |

**Total Active Database Routers**: ~20+

---

### ⚠️ File-Based Routers (Legacy - EXIST BUT NOT REGISTERED)

These routers use file storage (`storage_*.py` modules) but are **NOT registered in main.py**:

| Router | Status | Uses File Storage |
|--------|--------|-------------------|
| `policies_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_policies |
| `analyses_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_analyses |
| `ingestions_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_ingestions |
| `datasets_file.py` | ⚠️ Exists | ✅ Yes - Uses file storage |
| `exports_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_exports |
| `lineage_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_lineage |
| `notifications_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_notifications |
| `decisions_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_decisions |
| `cohorts_file.py` | ⚠️ Exists | ✅ Yes - Uses storage_cohorts |
| `rbac_file.py` | ⚠️ Exists | ✅ Yes - Uses file storage |

**Total Legacy File Routers**: 10 (NOT active in main.py)

---

## 3. File Storage Modules Status

### ⚠️ File Storage Modules Still Exist (37 files)

**Location**: `apps/api/src/uepi_api/storage_*.py`

These modules exist but are **NOT used by active routers**:
- `storage_policies.py`
- `storage_analyses.py`
- `storage_baselines.py`
- `storage_observations.py`
- `storage_pipelines.py`
- `storage_pipeline_runs.py`
- `storage_ingestions.py`
- `storage_lineage.py`
- `storage_notifications.py`
- `storage_exports.py`
- `storage_scorecards.py`
- `storage_schedules.py`
- `storage_learning.py`
- `storage_policy_predicted_impact.py`
- `storage_scenario_accuracy.py`
- `storage_data_periods.py`
- `storage_policy_versions.py`
- `storage_forecasts.py`
- `storage_risks.py`
- `storage_scenarios.py`
- `storage_evidence.py`
- `storage_decisions.py`
- `storage_cohorts.py`
- `storage_collaboration.py`
- `storage_audit_trail.py`
- `storage_user_roles.py`
- `storage_roles.py`
- `storage_auth.py`
- `storage_conversational_ai.py`
- `storage_narratives.py`
- `storage_behavior_signals.py`
- `storage_policy_assumptions.py`
- `storage_policy_guardrails.py`
- `storage_policy_changelog.py`
- `storage_alert_rules.py`
- `storage_file.py` (base utilities)
- `storage_adapter.py` (Azure/local adapter)

**Status**: These are **dead code** - not imported by active routers.

---

## 4. Source Data Files Handling ✅

### ✅ Correctly Using Temporary Files

**Source data files** are correctly handled as **temporary files** during ingestion:

1. **File Upload Endpoints**:
   - `/ingestions/upload` - Accepts file uploads, saves to temp file
   - `/pipelines/{id}/run` - Accepts file uploads for pipeline execution
   - `/policy_import/upload` - Accepts policy package files

2. **Temporary File Usage**:
   - Files are saved to `tempfile.NamedTemporaryFile()` 
   - Processed and loaded into database
   - Temporary files are deleted after processing
   - **Source data is NOT stored in file system** - only in database

3. **Canonical Data Storage**:
   - `ClaimsLineDB` - Stored in PostgreSQL `claims_lines` table ✅
   - `EnrollmentRecordDB` - Stored in PostgreSQL `enrollment_records` table ✅
   - `ProviderRecordDB` - Stored in PostgreSQL `provider_records` table ✅

**Status**: ✅ **Source data handling is correct** - files are temporary, data goes to database.

---

## 5. Data Storage Summary

### ✅ In Database (PostgreSQL)

| Data Type | Model | Table | Status |
|-----------|-------|-------|--------|
| **Core Entities** |
| Tenants | Tenant | `tenants` | ✅ Database |
| Users | User | `users` | ✅ Database |
| Roles | Role | `user_roles` | ✅ Database |
| **Policies** |
| Policies | Policy | `policies` | ✅ Database |
| Policy Versions | PolicyVersion | `policy_versions` | ✅ Database |
| Policy Code Sets | PolicyCodeSet | `policy_code_sets` | ✅ Database |
| Policy Assumptions | PolicyAssumption | `policy_assumptions` | ✅ Database |
| Policy Guardrails | PolicyGuardrail | `policy_guardrails` | ✅ Database |
| Policy Changelog | PolicyChangelog | `policy_changelogs` | ✅ Database |
| Policy Predicted Impact | PolicyPredictedImpact | `policy_predicted_impacts` | ✅ Database |
| **Canonical Data** |
| Claims Lines | ClaimsLineDB | `claims_lines` | ✅ Database |
| Enrollment Records | EnrollmentRecordDB | `enrollment_records` | ✅ Database |
| Provider Records | ProviderRecordDB | `provider_records` | ✅ Database |
| **Analyses** |
| Analyses | Analysis | `analyses` | ✅ Database |
| Analysis Runs | AnalysisRun | `analysis_runs` | ✅ Database |
| Analysis Results | BaselineAnalysisResult, ImpactAnalysisResult | `baseline_analysis_results`, `impact_analysis_results` | ✅ Database |
| **Ingestions** |
| Ingestions | Ingestion | `ingestions` | ✅ Database |
| Datasets | Dataset | `datasets` | ✅ Database |
| Ingestion Errors | IngestionError | `ingestion_errors` | ✅ Database |
| **Pipelines** |
| Pipelines | Pipeline | `pipelines` | ✅ Database |
| Pipeline Runs | PipelineRun | `pipeline_runs` | ✅ Database |
| **Other Entities** |
| Baselines | Baseline | `baselines` | ✅ Database |
| Observations | Observation | `observations` | ✅ Database |
| Scenarios | Scenario | `scenarios` | ✅ Database |
| Data Quality Reports | DataQualityReport | `data_quality_reports` | ✅ Database |
| Scorecards | Scorecard | `scorecards` | ✅ Database |
| Exports | Export | `exports` | ✅ Database |
| Cohorts | Cohort | `cohorts` | ✅ Database |
| Decisions | PolicyDecision | `policy_decisions` | ✅ Database |
| Notifications | Notification | `notifications` | ✅ Database |
| Schedules | Schedule | `schedules` | ✅ Database |
| And 20+ more... | | | ✅ Database |

### ❌ NOT In Database (File Storage - Legacy/Unused)

| Data Type | Storage Module | Status |
|-----------|----------------|--------|
| **Legacy File Storage** (NOT USED) |
| Policies (legacy) | `storage_policies.py` | ⚠️ Exists but NOT used |
| Analyses (legacy) | `storage_analyses.py` | ⚠️ Exists but NOT used |
| All other entities (legacy) | 35+ storage_*.py files | ⚠️ Exist but NOT used |

---

## 6. Main Application Router Registration

### ✅ Active Routers (from main.py)

**File**: `apps/api/src/uepi_api/main.py`

**Registered Routers** (all use database):
- ✅ `auth.router` - Database
- ✅ `access.router` - Database  
- ✅ `policies.router` - Database (NOT policies_file)
- ✅ `analyses.router` - Database (NOT analyses_file)
- ✅ `ingestions.router` - Database (NOT ingestions_file)
- ✅ `pipelines.router` - Database
- ✅ `datasets.router` - Database (NOT datasets_file)
- ✅ `data_quality.router` - Database
- ✅ `data_health.router` - Database
- ✅ `observations.router` - Database
- ✅ `baselines.router` - Database
- ✅ `scorecards.router` - Database
- ✅ `exports.router` - Database (NOT exports_file)
- ✅ `lineage.router` - Database (NOT lineage_file)
- ✅ `notifications.router` - Database (NOT notifications_file)
- ✅ `decisions.router` - Database (NOT decisions_file)
- ✅ `cohorts.router` - Database (NOT cohorts_file)
- ✅ `schedules.router` - Database
- ✅ `policy_import.router` - Database
- ✅ Plus 10+ more database routers

**NOT Registered** (file-based routers):
- ❌ `policies_file.router` - NOT registered
- ❌ `analyses_file.router` - NOT registered
- ❌ `ingestions_file.router` - NOT registered
- ❌ `datasets_file.router` - NOT registered
- ❌ `exports_file.router` - NOT registered
- ❌ `lineage_file.router` - NOT registered
- ❌ `notifications_file.router` - NOT registered
- ❌ `decisions_file.router` - NOT registered
- ❌ `cohorts_file.router` - NOT registered
- ❌ `rbac_file.router` - NOT registered

---

## 7. Conclusion

### Current State: **~95% Database, 5% Legacy Code**

✅ **What's in Database**:
- All active routers use PostgreSQL
- All canonical data (ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB) in database
- All business entities (Policies, Analyses, Ingestions, etc.) in database
- Source data files are correctly handled as temporary files

⚠️ **What's NOT in Database**:
- **Legacy file storage modules** (37 storage_*.py files) - exist but NOT used
- **Legacy file-based routers** (10 routers with `_file` suffix) - exist but NOT registered
- These are **dead code** that should be removed

### Recommendation

**To achieve 100% database (except source data files)**:

1. ✅ **Already Done**: All active routers use database
2. ✅ **Already Done**: Source data files are temporary only
3. ⚠️ **Cleanup Needed**: Remove legacy file storage modules (37 files)
4. ⚠️ **Cleanup Needed**: Remove legacy file-based routers (10 files)

**The product IS functionally 100% on database** - the file storage code is just legacy/unused code that should be cleaned up.

---

## 8. Verification Checklist

- [x] Database mode is active (`USE_FILE_STORAGE = False`)
- [x] All active routers use `get_db()` dependency
- [x] All canonical data models exist (ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB)
- [x] Source data files are temporary only
- [x] No active routers use file storage
- [ ] Legacy file storage modules removed (cleanup needed)
- [ ] Legacy file-based routers removed (cleanup needed)

---

**Report Generated**: 2025-01-23  
**Status**: ✅ **Functionally 100% Database** (legacy code cleanup recommended)
