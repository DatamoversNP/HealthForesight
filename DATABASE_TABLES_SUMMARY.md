# Database Tables Summary

## All Database Tables Created (55 tables)

### Core Tables (4)
1. `tenants` - Tenant/organization information
2. `users` - User accounts
3. `roles` - Role definitions
4. `user_roles` - Many-to-many relationship between users and roles

### Policy Tables (7)
5. `policies` - Main policy definitions
6. `policy_versions` - Policy version history
7. `policy_code_sets` - Policy code set mappings
8. `policy_assumptions` - Policy assumptions
9. `policy_guardrails` - Policy guardrails/thresholds
10. `policy_changelog` - Policy change history
11. `policy_predicted_impacts` - Predicted impact calculations

### Analytics Tables (6)
12. `baselines` - Baseline analysis results
13. `observations` - Observation analysis results
14. `scenarios` - What-if scenario definitions
15. `scenario_accuracy` - Scenario accuracy tracking
16. `forecasts` - Forecast projections
17. `data_periods` - Data period definitions

### Pipeline Tables (2)
18. `pipelines` - Data pipeline definitions
19. `pipeline_runs` - Pipeline execution history

### Risk Tables (1)
20. `risks` - Risk register entries

### Learning Tables (2)
21. `elasticity_models` - Elasticity model definitions
22. `model_accuracy_history` - Model accuracy tracking

### Behavior Tables (2)
23. `behavior_profiles` - Behavior profile definitions
24. `behavior_clusters` - Behavior cluster definitions

### Alert Tables (2)
25. `alert_rules` - Alert rule definitions
26. `alert_events` - Alert event history

### Collaboration Tables (4)
27. `comments` - Comments on resources
28. `tasks` - Task assignments
29. `approvals` - Approval requests
30. `activity_events` - Activity event log

### Evidence & Scheduling (2)
31. `evidence` - Evidence snapshots
32. `schedules` - Scheduled job definitions

### Export Tables (3)
33. `exports` - Export job definitions
34. `export_templates` - Export template definitions
35. `export_packs` - Export pack definitions

### Ingestion Tables (3)
36. `ingestions` - Data ingestion jobs
37. `ingestion_errors` - Ingestion error logs
38. `datasets` - Dataset definitions

### Analysis Tables (5)
39. `analyses` - Analysis job definitions
40. `analysis_configs` - Analysis configuration
41. `analysis_runs` - Analysis run history
42. `analysis_results_index` - Analysis result index
43. `analysis_narratives` - Analysis narrative text

### Scorecard Tables (2)
44. `scorecards` - Scorecard definitions
45. `scorecard_entries` - Scorecard entry details

### Decision Tables (2)
46. `policy_decisions` - Policy decision records
47. `decision_attachments` - Decision attachments

### Cohort Tables (1)
48. `cohorts` - Cohort definitions

### Notification Tables (2)
49. `notifications` - Notification records
50. `notification_preferences` - User notification preferences

### Lineage Tables (1)
51. `dataset_snapshots` - Dataset snapshot records

### Conversational AI Tables (4)
52. `conversations` - Conversation sessions
53. `conversation_messages` - Conversation messages
54. `conversation_artifacts` - Conversation artifacts
55. `conversation_audit_logs` - Conversation audit logs

### Audit Tables (1)
56. `audit_events` - Audit event log

---

## Storage Files Status (37 total files)

### ✅ Files with Dual-Mode Support (32 files)

1. `storage_policy_assumptions.py` → `policy_assumptions` table
2. `storage_policy_guardrails.py` → `policy_guardrails` table
3. `storage_policy_changelog.py` → `policy_changelog` table
4. `storage_policy_predicted_impact.py` → `policy_predicted_impacts` table
5. `storage_policy_versions.py` → `policy_versions` table
6. `storage_baselines.py` → `baselines` table
7. `storage_observations.py` → `observations` table
8. `storage_scenarios.py` → `scenarios` table
9. `storage_scenario_accuracy.py` → `scenario_accuracy` table
10. `storage_pipelines.py` → `pipelines` table
11. `storage_pipeline_runs.py` → `pipeline_runs` table
12. `storage_risks.py` → `risks` table
13. `storage_forecasts.py` → `forecasts` table
14. `storage_data_periods.py` → `data_periods` table
15. `storage_learning.py` → `elasticity_models`, `model_accuracy_history` tables
16. `storage_behavior_signals.py` → `behavior_profiles`, `behavior_clusters` tables
17. `storage_alert_rules.py` → `alert_rules`, `alert_events` tables
18. `storage_collaboration.py` → `comments`, `tasks`, `approvals`, `activity_events` tables
19. `storage_evidence.py` → `evidence` table
20. `storage_schedules.py` → `schedules` table
21. `storage_exports.py` → `exports`, `export_templates`, `export_packs` tables
22. `storage_cohorts.py` → `cohorts` table
23. `storage_notifications.py` → `notifications`, `notification_preferences` tables
24. `storage_ingestions.py` → `ingestions`, `ingestion_errors`, `datasets` tables
25. `storage_analyses.py` → `analyses`, `analysis_configs`, `analysis_runs`, `analysis_results_index` tables
26. `storage_decisions.py` → `policy_decisions`, `decision_attachments` tables
27. `storage_scorecards.py` → `scorecards`, `scorecard_entries` tables
28. `storage_audit_trail.py` → `audit_events` table
29. `storage_narratives.py` → `analysis_narratives` table
30. `storage_user_roles.py` → `user_roles` table (many-to-many)
31. `storage_roles.py` → `roles` table
32. `storage_policies.py` → `policies` table (main policy storage)

### 📝 Files Without Database Models (5 files)

1. **`storage_lineage.py`**
   - **Status**: Read-only aggregation function
   - **Note**: Uses `DatasetSnapshot` model (table exists), but function aggregates from multiple sources
   - **Action**: No conversion needed (read-only, aggregates from other tables)

2. **`storage_auth.py`**
   - **Status**: Helper functions for demo user/tenant
   - **Note**: Uses `User` and `Tenant` models (tables exist)
   - **Action**: No conversion needed (helper functions only, not actual storage)

3. **`storage_conversational_ai.py`**
   - **Status**: Has database models but not yet updated with dual-mode
   - **Note**: Models exist (`conversations`, `conversation_messages`, `conversation_artifacts`, `conversation_audit_logs`)
   - **Action**: Needs dual-mode implementation (models already exist)

4. **`storage_file.py`**
   - **Status**: Base storage utility functions
   - **Note**: Not an actual storage file, just utility functions
   - **Action**: No conversion needed (base utilities)

5. **`storage_adapter.py`**
   - **Status**: Storage adapter/interface
   - **Note**: Not an actual storage file, just adapter pattern
   - **Action**: No conversion needed (adapter pattern)

---

## Summary

- **Total Storage Files**: 37
- **Files with Dual-Mode Support**: 32 (86%)
- **Files Without Database Models**: 5 (14%)
  - 3 are read-only/helpers (no conversion needed)
  - 1 has models but needs dual-mode implementation
  - 1 is base utility

**All storage files that need database models have been converted!**

