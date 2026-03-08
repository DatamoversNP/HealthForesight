# Quick Start: Complete Product Flow

## Overview

This guide provides quick steps to generate data, ingest it, and test the complete product flow.

## Prerequisites

- Python 3.8+ with required packages
- Node.js and npm (for frontend)
- All dependencies installed

## Step 1: Generate All Data

Run the complete product flow script:

```bash
./scripts/complete_product_flow.sh
```

This will:
1. Generate policies with full lifecycle data (versions, assumptions, guardrails, changelogs)
2. Generate source data (members, providers, claims) and ingest to target data model
3. Generate observations from synthetic data
4. Verify all data is available

## Step 2: Start Services

### Terminal 1: API Server
```bash
cd apps/api
python -m uvicorn uepi_api.main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd apps/web
npm run dev
```

## Step 3: Access Application

Open browser: `http://localhost:3050`

## Step 4: Verify Complete Flow

### 1. Login
- Use demo user (automatically logged in)
- No hardcoded business data

### 2. Select Role
- Use RoleSwitcher in top navigation
- Select: Executive, Policy Owner, Analyst, or Ops/Clinical

### 3. View Persona Dashboard
- Should show real data from files
- No mock data
- All metrics calculated from actual data

### 4. Navigate to Policies
- Click "Policies" in sidebar
- Should see all generated policies
- Each policy has full lifecycle data

### 5. Open Policy Workspace
- Click "Open Workspace" icon on any policy
- Verify all tabs work:
  - Overview: Policy summary and metrics
  - Scope: Policy scope (read-only)
  - Levers: Policy levers (read-only)
  - Assumptions: View and manage assumptions
  - Guardrails: View and manage guardrails
  - Monitoring: Performance metrics
  - Versions: Version history
  - Changelog: Change timeline

### 6. Verify Data Sources
- All data comes from files
- No hardcoded values in code
- Policies from `apps/api/data/policies/`
- Lifecycle data from `data/policy_*` directories
- Observations from `data/observations/`
- Predicted impacts from `data/predicted_impacts/`
- Source data from `apps/api/data/target_data_model/`

## Data Locations

After running the flow, data will be in:

```
apps/api/data/
├── policies/
│   └── policy-*.json (policies)
└── target_data_model/
    └── {tenant_id}/
        ├── CLAIMS_LINES/claims_lines.csv
        ├── ELIGIBILITY_ENROLLMENT/enrollment.csv
        └── PROVIDER_MASTER/providers.csv

data/
├── policy_versions/{tenant_id}/policy-{policy_id}/
├── policy_assumptions/{tenant_id}/
├── policy_guardrails/{tenant_id}/
├── policy_changelog/{tenant_id}/
├── observations/{tenant_id}/
└── predicted_impacts/{tenant_id}/
```

## Troubleshooting

### Data Not Loading
- Check API server is running on port 8000
- Verify data files exist in expected locations
- Check API logs for errors

### Dashboards Empty
- Ensure data generation completed successfully
- Check that policies have predicted impacts
- Verify observations were generated

### Permission Errors
- Some directories may need manual creation
- Check file permissions
- Ensure scripts have execute permissions

## Next Steps

Once the flow is working:
1. Test all persona dashboards
2. Test policy workspace features
3. Test policy creation and editing
4. Test cohort creation
5. Verify all Epic 2 features work

All functionality is implemented and ready to test!


