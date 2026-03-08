# Database-Only Refactor Plan

## Step 1: Inventory of File-Based Persistence

### Storage Files with Dual-Mode (37 files)
All `storage_*.py` files currently have dual-mode logic. Need to remove file paths:

1. **Core Entities:**
   - `storage_policies.py` - Policies (main entity)
   - `storage_policy_versions.py` - Policy versions
   - `storage_policy_assumptions.py` - Policy assumptions
   - `storage_policy_guardrails.py` - Policy guardrails
   - `storage_policy_changelog.py` - Policy changelog
   - `storage_policy_predicted_impact.py` - Predicted impacts

2. **Analytics:**
   - `storage_baselines.py` - Baseline analyses
   - `storage_observations.py` - Observations
   - `storage_scenarios.py` - What-if scenarios
   - `storage_scenario_accuracy.py` - Scenario accuracy tracking
   - `storage_forecasts.py` - Forecasts
   - `storage_analyses.py` - Analysis runs

3. **Data Management:**
   - `storage_pipelines.py` - Data pipelines
   - `storage_pipeline_runs.py` - Pipeline execution runs
   - `storage_ingestions.py` - Data ingestions
   - `storage_data_periods.py` - Data periods
   - `storage_risks.py` - Risk register

4. **Learning & Behavior:**
   - `storage_learning.py` - Elasticity models, accuracy history
   - `storage_behavior_signals.py` - Behavior profiles, clusters

5. **Collaboration:**
   - `storage_collaboration.py` - Comments, tasks, approvals, activity
   - `storage_decisions.py` - Policy decisions

6. **Operations:**
   - `storage_audit_trail.py` - Audit events
   - `storage_evidence.py` - Evidence snapshots
   - `storage_scorecards.py` - Scorecards
   - `storage_schedules.py` - Schedules
   - `storage_exports.py` - Exports
   - `storage_narratives.py` - Analysis narratives
   - `storage_notifications.py` - Notifications
   - `storage_cohorts.py` - Saved cohorts
   - `storage_alert_rules.py` - Alert rules
   - `storage_roles.py` - Roles
   - `storage_user_roles.py` - User role assignments
   - `storage_conversational_ai.py` - Conversational AI state
   - `storage_lineage.py` - Dataset snapshots

### File Storage Infrastructure (to remove/deprecate)
- `storage_file.py` - FileStorage instances
- `storage/policy_storage.py` - Policy storage adapter (has file fallback)
- `storage/azure_file_storage.py` - Azure file storage (keep for blob storage, not persistence)
- `storage_adapter.py` - Storage adapter abstraction
- `uepi_common/storage/file_storage.py` - Common file storage class

### Routers Using File Storage
- `routers/policies_file.py` - File-based policy routes (deprecated)
- `routers/analyses_file.py` - File-based analysis routes (deprecated)
- `routers/ingestions_file.py` - File-based ingestion routes (deprecated)
- `routers/exports_file.py` - File-based export routes (deprecated)
- `routers/decisions_file.py` - File-based decision routes (deprecated)
- `routers/notifications_file.py` - File-based notification routes (deprecated)
- `routers/datasets_file.py` - File-based dataset routes (deprecated)
- `routers/rbac_file.py` - File-based RBAC routes (deprecated)
- `routers/cohorts_file.py` - File-based cohort routes (deprecated)
- `routers/lineage_file.py` - File-based lineage routes (deprecated)

## Step 2: Database Schema Status

### ✅ Already Created Models (30+ models)
All models exist in `models/` directory. Need to verify completeness.

### ⚠️ Missing Models (if any)
- Check for any entities stored in files but not in models

## Step 3: Implementation Plan

### Phase 1: Remove File Storage Paths from storage_*.py
- Remove all `if USE_FILE_STORAGE:` branches
- Keep only database code
- Remove file I/O operations

### Phase 2: Create Repository Layer
- Create `repositories/` directory
- One repository per entity type
- Standard CRUD + query methods

### Phase 3: Update Routers
- Remove all `*_file.py` router files
- Update main routers to use repositories only
- Remove file storage imports

### Phase 4: Migration Script
- Read all existing file data
- Import into database
- Handle conflicts/idempotency

### Phase 5: Cleanup
- Remove file storage modules
- Update config to remove USE_FILE_STORAGE
- Update documentation

