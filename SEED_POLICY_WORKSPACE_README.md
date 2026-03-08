# Policy Workspace Data Seeding

## Overview
The script `apps/api/scripts/seed_policy_workspace_data.py` creates complete workspace data for all predefined policies, including:

✅ **Assumptions** - Elasticity, substitution rates, lag days, policy-specific assumptions
✅ **Guardrails** - Utilization, cost, ER utilization thresholds
✅ **Versions** - Initial policy versions with metadata
✅ **Changelog** - Policy creation and activation entries
✅ **Risk Registers** - Risk drivers with mitigation actions

## What Was Created

The script successfully created:
- **Assumptions**: 3-4 per policy (ELASTICITY, SUBSTITUTION_RATE, LAG_DAYS, plus policy-specific)
- **Guardrails**: 3 per policy (UTILIZATION_INCREASE, COST_INCREASE, ER_UTILIZATION)
- **Versions**: 1 initial version per policy
- **Risk Registers**: 3 risk drivers per policy

## Running the Script

### Option 1: Run Locally (After Deployment)
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 apps/api/scripts/seed_policy_workspace_data.py
```

### Option 2: Run on Azure (After Deployment)
SSH into your Azure App Service and run:
```bash
cd /home/site/wwwroot
python3 apps/api/scripts/seed_policy_workspace_data.py
```

## What Gets Created

For each policy, the script creates:

### 1. Assumptions (`data/policy_assumptions/{tenant_id}/policy-{uuid}.json`)
- **ELASTICITY**: Price elasticity of demand (-0.3)
- **SUBSTITUTION_RATE**: Expected substitution rate (15%)
- **LAG_DAYS**: Expected lag before impact (60 days)
- **Policy-specific**: PA_APPROVAL_RATE, TRIAL_SUCCESS_RATE, COMPLIANCE_RATE

### 2. Guardrails (`data/policy_guardrails/{tenant_id}/policy-{uuid}.json`)
- **UTILIZATION_INCREASE**: Alert if >20% increase
- **COST_INCREASE**: Alert if >15% increase
- **ER_UTILIZATION**: Alert if >10% increase (substitution effect)

### 3. Versions (`data/policy_versions/{tenant_id}/policy-{uuid}/`)
- Initial version (v1) with policy metadata
- Versions index file

### 4. Changelog (`data/policy_changelog/{tenant_id}/policy-{uuid}.json`)
- Policy creation entry
- Policy activation entry
- Scope configuration entry

### 5. Risk Registers (`data/risks/{tenant_id}/risk-{uuid}.json`)
- Provider Non-Compliance (impact: 0.6)
- Substitution Effects (impact: 0.5)
- Patient Access Issues (impact: 0.4)

## Linking to Related Features

### Predicted Impact
- Already included in policy metadata
- Accessible via `GET /api/v1/policies/{policy_id}/predicted-impact`
- Linked automatically when policy is created

### Baselines
- Policies automatically link to latest baseline when generating predicted impact
- Baseline metrics used for predictions
- Accessible via baseline analysis endpoints

### What-If Scenarios
- Scenarios can be linked to policies via `policy_id` parameter
- Accessible via scenario endpoints
- Link created when scenario references policy

## Policy Workspace Tabs Status

After running the seeding script, all tabs will have data:

| Tab | Data Source | Status |
|-----|-------------|--------|
| Overview | Policy + Workspace data | ✅ Complete |
| Scope | Policy metadata | ✅ Complete |
| Levers | Policy metadata | ✅ Complete |
| Assumptions | Seeded assumptions | ✅ Complete |
| Guardrails | Seeded guardrails | ✅ Complete |
| Monitoring | Performance metrics | ⚠️ Requires observations |
| Versions | Seeded versions | ✅ Complete |
| Changelog | Seeded changelog | ✅ Complete |
| Decisions | User-created | ⚠️ Empty until created |
| Evidence | Linked to decisions | ⚠️ Empty until created |
| Forecasts | User-created | ⚠️ Empty until created |
| Scenarios | User-created | ⚠️ Empty until created |
| Risk Register | Seeded risk register | ✅ Complete |
| Behavior | Behavioral signals | ⚠️ Requires data |
| Alerts | Alert events | ⚠️ Empty until triggered |
| Comments | User-created | ⚠️ Empty until created |
| Tasks | User-created | ⚠️ Empty until created |
| Activity | Activity events | ⚠️ Empty until activity |
| Narrative | User-created | ⚠️ Empty until created |

## Next Steps

1. **Run the seeding script** to populate assumptions, guardrails, versions, changelog, and risk registers
2. **Deploy to Azure** with `./START_PRODUCTION_BUILD.sh`
3. **Test the policy workspace** - all tabs should now show data
4. **Create additional data** as needed:
   - Decisions (via Decisions tab)
   - Forecasts (via Forecasts tab)
   - Scenarios (via Scenarios tab)
   - Comments, Tasks, Activity (via Collaboration tabs)

## Notes

- The script uses deterministic UUID generation for string policy IDs
- All data is written to `data/` directory
- Files are organized by tenant ID and policy UUID
- The script is idempotent - can be run multiple times safely

