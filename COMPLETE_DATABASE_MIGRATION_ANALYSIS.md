# Complete Database Migration Analysis - Entire Product

## Current State: File-Based Storage

### All File-Based Storage Modules (39 storage files found):

1. **Policies & Workspace Data:**
   - `storage_policies.py` - Main policy storage
   - `storage_policy_assumptions.py` - Policy assumptions
   - `storage_policy_guardrails.py` - Policy guardrails
   - `storage_policy_versions.py` - Policy versions
   - `storage_policy_changelog.py` - Policy changelog
   - `storage_policy_predicted_impact.py` - Predicted impacts

2. **Analyses & Results:**
   - `storage_analyses.py` - Analysis definitions
   - `storage_baselines.py` - Baseline metrics
   - `storage_observations.py` - Observation data
   - `storage_scenario_accuracy.py` - Scenario accuracy metrics

3. **Pipelines & Data Processing:**
   - `storage_pipelines.py` - Pipeline definitions
   - `storage_pipeline_runs.py` - Pipeline execution runs
   - `storage_ingestions.py` - Data ingestion records
   - `storage_data_periods.py` - Data period definitions

4. **Decisions & Workflows:**
   - `storage_decisions.py` - Policy decisions
   - `storage_risks.py` - Risk registers
   - `storage_scenarios.py` - What-if scenarios
   - `storage_forecasts.py` - Forecasts

5. **Collaboration & Social:**
   - `storage_collaboration.py` - Comments, activity events
   - `storage_narratives.py` - Executive narratives
   - `storage_audit_trail.py` - Audit logs

6. **Behavior & Alerts:**
   - `storage_behavior_signals.py` - Behavior detection
   - `storage_alert_rules.py` - Alert rules
   - (Alert events likely in behavior_signals)

7. **Learning & AI:**
   - `storage_learning.py` - ML models, accuracy history
   - `storage_conversational_ai.py` - Chat conversations

8. **Other:**
   - `storage_cohorts.py` - Cohorts
   - `storage_scorecards.py` - Scorecards
   - `storage_exports.py` - Exports
   - `storage_schedules.py` - Scheduled tasks
   - `storage_lineage.py` - Data lineage
   - `storage_evidence.py` - Evidence documents
   - `storage_notifications.py` - Notifications
   - `storage_roles.py` - Roles
   - `storage_user_roles.py` - User-role assignments
   - `storage_auth.py` - Auth data

## Database Models That Already Exist

### ✅ Already in Database (from `models/__init__.py`):

1. **Core:**
   - `Tenant`, `User`, `Role` (tenant.py)
   - `AuditEvent` (audit.py)

2. **Policies:**
   - `Policy` (with `policy_metadata_json` JSONB)
   - `PolicyVersion` (with `version_metadata_json` JSONB)
   - `PolicyCodeSet`

3. **Analyses:**
   - `Analysis`
   - `AnalysisRun`
   - `AnalysisResultIndex`
   - `AnalysisNarrative`
   - `AnalysisConfig`

4. **Decisions:**
   - `PolicyDecision`
   - `DecisionAttachment`

5. **Other:**
   - `Ingestion`, `IngestionError`, `Dataset` (ingestion.py)
   - `Scorecard`, `ScorecardEntry` (scorecard.py)
   - `Export` (export.py)
   - `Cohort` (cohort.py)
   - `DatasetSnapshot` (lineage.py)
   - `Notification`, `NotificationPreference` (notification.py)
   - `Conversation`, `ConversationMessage`, `ConversationArtifact`, `ConversationAuditLog` (conversational_ai.py)

## Missing Database Models (Currently Only in Files)

### 1. Policy Workspace Data (3 tables needed):
- ❌ `PolicyAssumption` - Currently in `policy.metadata.assumptions[]`
- ❌ `PolicyGuardrail` - Currently in `policy.metadata.guardrails[]`
- ❌ `PolicyChangelog` - Currently in `policy.metadata.changelog[]`

### 2. Predicted Impact (1 table needed):
- ❌ `PolicyPredictedImpact` - Currently in `data/predicted_impacts/{tenant_id}/{policy_id}.json`
  - Fields: `policy_id`, `metrics` (JSONB), `predicted_at`, `model_version`, `confidence`, etc.

### 3. Baselines (1 table needed):
- ❌ `Baseline` - Currently in `data/baselines/{tenant_id}/{baseline_id}.json`
  - Fields: `baseline_id`, `tenant_id`, `name`, `description`, `data_period_id`, `metrics` (JSONB), `created_at`, etc.

### 4. Observations (1 table needed):
- ❌ `Observation` - Currently in `data/observations/{tenant_id}/{observation_id}.json`
  - Fields: `observation_id`, `tenant_id`, `policy_id`, `baseline_id`, `observation_date`, `metrics` (JSONB), `vs_baseline` (JSONB), `vs_predicted` (JSONB), etc.

### 5. Scenarios (1 table needed):
- ❌ `Scenario` - Currently in `data/scenarios/{tenant_id}/{scenario_id}.json`
  - Fields: `scenario_id`, `tenant_id`, `name`, `description`, `policy_id`, `assumptions` (JSONB), `results` (JSONB), `created_at`, etc.

### 6. Risks (1 table needed):
- ❌ `RiskRegister` or `PolicyRisk` - Currently in `data/risks/{tenant_id}/{risk_id}.json`
  - Fields: `risk_id`, `tenant_id`, `policy_id`, `risk_driver`, `probability`, `impact`, `mitigation`, `status`, etc.

### 7. Pipelines (2 tables needed):
- ❌ `Pipeline` - Currently in `data/pipelines/{pipeline_id}.json`
  - Fields: `pipeline_id`, `tenant_id`, `name`, `description`, `steps` (JSONB), `schedule`, `status`, etc.
- ❌ `PipelineRun` - Currently in `data/pipeline_runs/{run_id}.json`
  - Fields: `run_id`, `tenant_id`, `pipeline_id`, `status`, `started_at`, `ended_at`, `logs_uri`, `metrics` (JSONB), etc.

### 8. Data Periods (1 table needed):
- ❌ `DataPeriod` - Currently in `data/periods/{tenant_id}/{period_id}.json`
  - Fields: `period_id`, `tenant_id`, `name`, `start_date`, `end_date`, `data_snapshot_id`, etc.

### 9. Scenario Accuracy (1 table needed):
- ❌ `ScenarioAccuracy` - Currently in `data/scenario_accuracy/{tenant_id}/{accuracy_id}.json`
  - Fields: `accuracy_id`, `tenant_id`, `scenario_id`, `actual_vs_predicted` (JSONB), `metrics` (JSONB), etc.

### 10. Forecasts (1 table needed):
- ❌ `Forecast` - Currently in `data/forecasts/{tenant_id}/{forecast_id}.json`
  - Fields: `forecast_id`, `tenant_id`, `policy_id`, `forecast_date`, `projections` (JSONB), `confidence_intervals` (JSONB), etc.

### 11. Learning Models (2 tables needed):
- ❌ `ElasticityModel` - Currently in `data/learning/elasticity_models/{model_id}.json`
  - Fields: `model_id`, `tenant_id`, `policy_id`, `model_type`, `parameters` (JSONB), `accuracy_metrics` (JSONB), `trained_at`, etc.
- ❌ `ModelAccuracyHistory` - Currently in `data/learning/accuracy_history/{tenant_id}/{history_id}.json`
  - Fields: `history_id`, `tenant_id`, `model_id`, `evaluation_date`, `metrics` (JSONB), etc.

### 12. Behavior Detection (2 tables needed):
- ❌ `BehaviorProfile` - Currently in `data/behavior_profiles/{profile_id}.json`
  - Fields: `profile_id`, `tenant_id`, `member_id`, `provider_id`, `behavior_type`, `signals` (JSONB), `detected_at`, etc.
- ❌ `BehaviorCluster` - Currently in `data/behavior_clusters/{cluster_id}.json`
  - Fields: `cluster_id`, `tenant_id`, `cluster_type`, `members` (JSONB), `characteristics` (JSONB), etc.

### 13. Alert Rules & Events (2 tables needed):
- ❌ `AlertRule` - Currently in `data/alert_rules/{rule_id}.json`
  - Fields: `rule_id`, `tenant_id`, `name`, `condition` (JSONB), `action`, `enabled`, etc.
- ❌ `AlertEvent` - Currently in `data/alert_events/{event_id}.json`
  - Fields: `event_id`, `tenant_id`, `rule_id`, `policy_id`, `severity`, `triggered_at`, `resolved_at`, `details` (JSONB), etc.

### 14. Collaboration (4 tables needed):
- ❌ `Comment` - Currently in `data/comments/{comment_id}.json`
  - Fields: `comment_id`, `tenant_id`, `resource_type`, `resource_id`, `user_id`, `content`, `created_at`, etc.
- ❌ `Task` - Currently in `data/tasks/{task_id}.json`
  - Fields: `task_id`, `tenant_id`, `resource_type`, `resource_id`, `assigned_to`, `status`, `due_date`, etc.
- ❌ `Approval` - Currently in `data/approvals/{approval_id}.json`
  - Fields: `approval_id`, `tenant_id`, `resource_type`, `resource_id`, `requested_by`, `approved_by`, `status`, etc.
- ❌ `ActivityEvent` - Currently in `data/activity/{event_id}.json`
  - Fields: `event_id`, `tenant_id`, `resource_type`, `resource_id`, `user_id`, `action`, `details` (JSONB), `created_at`, etc.

### 15. Evidence (1 table needed):
- ❌ `Evidence` - Currently in `data/evidence/{tenant_id}/{evidence_id}.json`
  - Fields: `evidence_id`, `tenant_id`, `resource_type`, `resource_id`, `evidence_type`, `uri`, `metadata` (JSONB), etc.

### 16. Schedules (1 table needed):
- ❌ `Schedule` - Currently in `data/schedules/{tenant_id}/{schedule_id}.json`
  - Fields: `schedule_id`, `tenant_id`, `name`, `schedule_type`, `cron_expression`, `enabled`, `last_run_at`, `next_run_at`, etc.

### 17. Export Templates & Packs (2 tables needed):
- ❌ `ExportTemplate` - Currently in `data/export_templates/{template_id}.json`
  - Fields: `template_id`, `tenant_id`, `name`, `template_type`, `configuration` (JSONB), etc.
- ❌ `ExportPack` - Currently in `data/export_packs/{pack_id}.json`
  - Fields: `pack_id`, `tenant_id`, `name`, `exports` (JSONB array of export IDs), `created_at`, etc.

## Summary: Database Migration Requirements

### Total Missing Tables: **30+ tables**

### Categories:

1. **Policy Workspace** (3 tables): Assumptions, Guardrails, Changelog
2. **Analytics** (5 tables): PredictedImpact, Baseline, Observation, Scenario, ScenarioAccuracy
3. **Pipelines** (2 tables): Pipeline, PipelineRun
4. **Data Management** (1 table): DataPeriod
5. **Risk & Forecasting** (2 tables): Risk, Forecast
6. **Learning** (2 tables): ElasticityModel, ModelAccuracyHistory
7. **Behavior** (2 tables): BehaviorProfile, BehaviorCluster
8. **Alerts** (2 tables): AlertRule, AlertEvent
9. **Collaboration** (4 tables): Comment, Task, Approval, ActivityEvent
10. **Evidence** (1 table): Evidence
11. **Scheduling** (1 table): Schedule
12. **Exports** (2 tables): ExportTemplate, ExportPack

### What Already Exists in Database:

- ✅ Core entities (Tenant, User, Role)
- ✅ Policies (Policy, PolicyVersion, PolicyCodeSet)
- ✅ Analyses (Analysis, AnalysisRun, AnalysisResultIndex, etc.)
- ✅ Decisions (PolicyDecision, DecisionAttachment)
- ✅ Ingestion (Ingestion, IngestionError, Dataset)
- ✅ Scorecards (Scorecard, ScorecardEntry)
- ✅ Exports (Export)
- ✅ Cohorts (Cohort)
- ✅ Lineage (DatasetSnapshot)
- ✅ Notifications (Notification, NotificationPreference)
- ✅ Conversational AI (Conversation, ConversationMessage, etc.)

### Migration Strategy:

1. **Phase 1: Core Policy Workspace** (3 tables)
   - PolicyAssumption, PolicyGuardrail, PolicyChangelog
   - Highest priority - currently blocking metadata loading

2. **Phase 2: Analytics & Results** (5 tables)
   - PredictedImpact, Baseline, Observation, Scenario, ScenarioAccuracy
   - Critical for policy analysis workflows

3. **Phase 3: Pipelines & Data** (3 tables)
   - Pipeline, PipelineRun, DataPeriod
   - Important for data processing workflows

4. **Phase 4: Risk & Learning** (4 tables)
   - Risk, Forecast, ElasticityModel, ModelAccuracyHistory
   - Advanced features

5. **Phase 5: Behavior & Alerts** (4 tables)
   - BehaviorProfile, BehaviorCluster, AlertRule, AlertEvent
   - Monitoring features

6. **Phase 6: Collaboration** (4 tables)
   - Comment, Task, Approval, ActivityEvent
   - Social features

7. **Phase 7: Supporting** (4 tables)
   - Evidence, Schedule, ExportTemplate, ExportPack
   - Supporting features

### Estimated Effort:

- **Database Models:** 30+ model classes = 8-10 hours
- **Alembic Migrations:** 30+ migration files = 10-12 hours
- **Data Migration Scripts:** 30+ migration scripts = 20-30 hours
- **Storage Function Updates:** 39 storage files to update = 40-60 hours
- **Testing:** Comprehensive testing = 20-30 hours
- **Total:** **98-142 hours** (~2.5-3.5 weeks full-time)

### Critical Dependencies:

1. **PostgreSQL Database** - Must be set up and accessible
2. **Connection Pooling** - Already configured in `database.py`
3. **JSONB Support** - PostgreSQL required for JSONB columns
4. **Migration Tooling** - Alembic already configured
5. **Storage Adapter Pattern** - Already exists, needs DB implementation

### Configuration Changes Needed:

```bash
# Environment Variables
USE_FILE_STORAGE=false
DATABASE_URL=postgresql://user:password@host:port/dbname

# Azure App Service Settings
az webapp config appsettings set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --settings \
    USE_FILE_STORAGE=false \
    DATABASE_URL="postgresql://..."
```

## Next Steps:

1. **Start with Phase 1** (Policy Workspace) - 3 tables, highest priority
2. **Create database models** for all 30+ missing tables
3. **Create Alembic migrations** for all tables
4. **Create data migration scripts** to move data from files to database
5. **Update storage functions** to query database when `USE_FILE_STORAGE=false`
6. **Test thoroughly** before switching over

This is a **major migration** affecting the entire product architecture.

