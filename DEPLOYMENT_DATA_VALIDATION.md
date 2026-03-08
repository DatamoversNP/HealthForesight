# Deployment Data Validation

## ✅ All Data Files Included

The deployment script has been updated to include **ALL data files** - an exact replica of your local environment.

## 📦 What's Included

### Complete Data Directory
- ✅ **source_data** (443M) - All source data files
- ✅ **predicted_impacts** - All predicted impact calculations
- ✅ **analyses** (412K) - All analysis results
- ✅ **analysis_results** (132K) - Analysis result data
- ✅ **observations** - Observation data
- ✅ **baselines** (84K) - Baseline analysis data
- ✅ **pipelines** (92K) - Pipeline definitions
- ✅ **pipeline_runs** (7.8M) - Pipeline execution data
- ✅ **scenarios** - What-if scenarios
- ✅ **decisions** - Decision data
- ✅ **scorecards** (64K) - Scorecard data
- ✅ **target_data_model** (75M) - Target data model files
- ✅ **cohorts** (80K) - Cohort definitions
- ✅ **cost_tracking** - Cost tracking data
- ✅ **learning** - Learning model data
- ✅ **periods** - Data periods
- ✅ **ingestions** - Ingestion records
- ✅ **exports** - Export data
- ✅ **scenario_accuracy** - Scenario accuracy tracking
- ✅ **forecasts** - Forecast data
- ✅ **evidence** - Evidence data
- ✅ **conversations** (484K) - Conversation data
- ✅ **notifications** - Notification data
- ✅ **schedules** - Schedule data
- ✅ **activity** - Activity logs
- ✅ **alert_events** - Alert events
- ✅ **alert_rules** - Alert rules
- ✅ **approvals** - Approval data
- ✅ **audit_trail** - Audit trail
- ✅ **behavior_clusters** - Behavior cluster data
- ✅ **behavior_profiles** - Behavior profile data
- ✅ **comments** - Comments data
- ✅ **narratives** - Narrative data
- ✅ **tasks** - Task data
- ✅ **roles** - Role definitions
- ✅ **user_roles** - User role assignments
- ✅ **users** - User data
- ✅ **tenants** - Tenant data
- ✅ **risks** (120K) - Risk register
- ✅ **policies** (208K) - Policy files
- ✅ **policy_assumptions** (172K) - Policy assumptions (now in metadata)
- ✅ **policy_guardrails** (172K) - Policy guardrails (now in metadata)
- ✅ **policy_versions** (1.1M) - Policy versions (now in metadata)
- ✅ **policy_changelog** - Policy changelog (now in metadata)
- ✅ **demo** (14M) - Demo data
- ✅ **qa_test_results** (416K) - QA test results

## 🔍 Validation

The deployment script will:
1. ✅ Copy entire `data/` directory from project root
2. ✅ Preserve all subdirectories and files
3. ✅ Verify key data directories are present
4. ✅ Show summary of what was copied
5. ✅ Include everything in the ZIP file

## 📊 Deployment Package Contents

**API Package includes:**
- All source code
- `packages/common`
- **Complete `data/` directory** (all subdirectories)
- `requirements.txt`
- `startup.sh`

**Total data size:** ~600MB+ (all data files)

## ✅ Verification After Deployment

After deployment, verify data is present:

```bash
# SSH into Azure App Service
az webapp ssh --resource-group [RESOURCE_GROUP] --name [API_APP_NAME]

# Check data directory
ls -la /home/site/wwwroot/data/

# Verify key directories
ls -la /home/site/wwwroot/data/source_data/
ls -la /home/site/wwwroot/data/predicted_impacts/
ls -la /home/site/wwwroot/data/analyses/
```

## 🎯 Summary

**Everything is included:**
- ✅ All source data
- ✅ All predicted impacts
- ✅ All analyses
- ✅ All observations
- ✅ All baselines
- ✅ All pipelines
- ✅ All scenarios
- ✅ All decisions
- ✅ All dashboards data
- ✅ Everything else in data/

**This is an exact replica of your local environment!**

