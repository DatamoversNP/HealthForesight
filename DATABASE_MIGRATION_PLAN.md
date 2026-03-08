# Database Migration Implementation Plan

## Phase 1: Backup & Branch Setup ✅

### Step 1: Create Backup
- [x] Document current state
- [ ] Create git branch: `database-migration`
- [ ] Tag current state: `file-storage-v1.0`

### Step 2: Branch Structure
- [ ] Create branch: `database-migration`
- [ ] Keep file-based code intact
- [ ] Add database implementation alongside

## Phase 2: Database Models (30+ tables)

### Priority 1: Policy Workspace (3 tables)
- [ ] `PolicyAssumption` model
- [ ] `PolicyGuardrail` model
- [ ] `PolicyChangelog` model

### Priority 2: Analytics (5 tables)
- [ ] `PolicyPredictedImpact` model
- [ ] `Baseline` model
- [ ] `Observation` model
- [ ] `Scenario` model
- [ ] `ScenarioAccuracy` model

### Priority 3: Pipelines (2 tables)
- [ ] `Pipeline` model
- [ ] `PipelineRun` model

### Priority 4: Data Management (1 table)
- [ ] `DataPeriod` model

### Priority 5: Risk & Forecasting (2 tables)
- [ ] `Risk` model
- [ ] `Forecast` model

### Priority 6: Learning (2 tables)
- [ ] `ElasticityModel` model
- [ ] `ModelAccuracyHistory` model

### Priority 7: Behavior (2 tables)
- [ ] `BehaviorProfile` model
- [ ] `BehaviorCluster` model

### Priority 8: Alerts (2 tables)
- [ ] `AlertRule` model
- [ ] `AlertEvent` model

### Priority 9: Collaboration (4 tables)
- [ ] `Comment` model
- [ ] `Task` model
- [ ] `Approval` model
- [ ] `ActivityEvent` model

### Priority 10: Supporting (4 tables)
- [ ] `Evidence` model
- [ ] `Schedule` model
- [ ] `ExportTemplate` model
- [ ] `ExportPack` model

## Phase 3: Alembic Migrations

- [ ] Create migration for all 30+ tables
- [ ] Add indexes and foreign keys
- [ ] Test migrations up/down

## Phase 4: Storage Layer Updates (39 files)

### Strategy: Dual-Mode Support
- Keep file-based functions working
- Add database functions
- Use `USE_FILE_STORAGE` flag to switch

### Files to Update:
1. `storage_policies.py`
2. `storage_policy_assumptions.py`
3. `storage_policy_guardrails.py`
4. `storage_policy_versions.py`
5. `storage_policy_changelog.py`
6. `storage_policy_predicted_impact.py`
7. `storage_analyses.py`
8. `storage_baselines.py`
9. `storage_observations.py`
10. `storage_scenario_accuracy.py`
11. `storage_pipelines.py`
12. `storage_pipeline_runs.py`
13. `storage_ingestions.py`
14. `storage_data_periods.py`
15. `storage_decisions.py`
16. `storage_risks.py`
17. `storage_scenarios.py`
18. `storage_forecasts.py`
19. `storage_learning.py`
20. `storage_behavior_signals.py`
21. `storage_alert_rules.py`
22. `storage_collaboration.py`
23. `storage_narratives.py`
24. `storage_audit_trail.py`
25. `storage_evidence.py`
26. `storage_schedules.py`
27. `storage_exports.py`
28. `storage_cohorts.py`
29. `storage_scorecards.py`
30. `storage_lineage.py`
31. `storage_notifications.py`
32. `storage_roles.py`
33. `storage_user_roles.py`
34. `storage_auth.py`
35. `storage_conversational_ai.py`
36. `storage_file.py` (base utilities)
37. `storage_adapter.py`
38. `storage/policy_storage.py`
39. Others as needed

## Phase 5: Data Migration Scripts

- [ ] Policy workspace data migration
- [ ] Predicted impacts migration
- [ ] Baselines migration
- [ ] Observations migration
- [ ] Scenarios migration
- [ ] Risks migration
- [ ] Pipelines migration
- [ ] All other data migrations

## Phase 6: Testing & Validation

- [ ] Unit tests for all storage functions
- [ ] Integration tests
- [ ] Data integrity validation
- [ ] Performance testing
- [ ] Functionality parity testing

## Phase 7: Configuration & Deployment

- [ ] Update configuration docs
- [ ] Create deployment scripts
- [ ] Update Azure App Service settings
- [ ] Migration runbook

## Implementation Approach

### Dual-Mode Pattern:
```python
def get_policy(policy_id, tenant_id):
    if USE_FILE_STORAGE:
        return _get_policy_from_file(policy_id, tenant_id)
    else:
        return _get_policy_from_db(policy_id, tenant_id)
```

### No Breaking Changes:
- All existing APIs work the same
- Same data structures returned
- Same error handling
- Same validation logic

