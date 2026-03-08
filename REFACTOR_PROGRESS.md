# Database-Only Refactor Progress

## Completed
- ✅ `database.py` - Removed USE_FILE_STORAGE, always uses PostgreSQL
- ✅ `storage_baselines.py` - Removed all file storage code, database only

## In Progress
- 🔄 Remaining 36 storage_*.py files need refactoring

## Remaining Storage Files to Refactor
1. storage_policies.py
2. storage_policy_versions.py
3. storage_policy_assumptions.py
4. storage_policy_guardrails.py
5. storage_policy_changelog.py
6. storage_policy_predicted_impact.py
7. storage_observations.py
8. storage_scenarios.py
9. storage_scenario_accuracy.py
10. storage_forecasts.py
11. storage_analyses.py
12. storage_pipelines.py
13. storage_pipeline_runs.py
14. storage_ingestions.py
15. storage_data_periods.py
16. storage_risks.py
17. storage_learning.py
18. storage_behavior_signals.py
19. storage_collaboration.py
20. storage_decisions.py
21. storage_audit_trail.py
22. storage_evidence.py
23. storage_scorecards.py
24. storage_schedules.py
25. storage_exports.py
26. storage_narratives.py
27. storage_notifications.py
28. storage_cohorts.py
29. storage_alert_rules.py
30. storage_roles.py
31. storage_user_roles.py
32. storage_conversational_ai.py
33. storage_lineage.py
34. storage_auth.py

## Pattern for Refactoring
Each storage file should:
1. Remove all file I/O imports (json, pathlib, open, etc.)
2. Remove USE_FILE_STORAGE checks
3. Remove all `_*_in_file` functions
4. Keep only `_*_in_db` functions (rename to remove `_in_db` suffix)
5. Update public functions to call database functions directly
6. Remove file storage initialization code

## Next Steps
1. Continue refactoring storage files systematically
2. Update routers to remove file storage imports
3. Remove deprecated `*_file.py` router files
4. Create migration script
5. Update config to remove use_file_storage setting
6. Clean up dead code

