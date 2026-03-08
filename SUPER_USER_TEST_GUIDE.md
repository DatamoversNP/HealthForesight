# Super User / Agent End-to-End Test Guide

## Overview

This guide provides step-by-step instructions for testing the complete product flow as a super user/agent, covering all functionalities from data generation to dashboard display.

## Prerequisites

1. Python 3.8+ with all dependencies installed
2. Node.js and npm (for frontend)
3. API server can start on port 8000
4. Frontend can start on port 3050

## Complete Test Flow

### Phase 1: Data Generation & Setup

#### Step 1.1: Generate Policies with Lifecycle Data

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 scripts/generate_complete_payer_synthetic_data.py --tenant-id 00000000-0000-0000-0000-000000000001
```

**Expected Output:**
- 5 policies generated
- Each policy has: version, assumptions, guardrails, changelog, predicted impact
- Files created in:
  - `apps/api/data/policies/policy-*.json`
  - `data/policy_versions/{tenant_id}/`
  - `data/policy_assumptions/{tenant_id}/`
  - `data/policy_guardrails/{tenant_id}/`
  - `data/policy_changelog/{tenant_id}/`
  - `data/predicted_impacts/{tenant_id}/`

**Verify:**
```bash
ls -la apps/api/data/policies/ | wc -l  # Should show policy files
find data/policy_versions -name "*.json" | wc -l  # Should show version files
```

#### Step 1.2: Generate Source Data & Ingest to Target Model

```bash
python3 scripts/regenerate_complete_workflow.py \
  --tenant-id 00000000-0000-0000-0000-000000000001 \
  --months 24 \
  --post-days 30
```

**Expected Output:**
- Members, providers, claims generated
- Data ingested to `apps/api/data/target_data_model/{tenant_id}/`
- Structure:
  - `CLAIMS_LINES/claims_lines.csv`
  - `ELIGIBILITY_ENROLLMENT/enrollment.csv`
  - `PROVIDER_MASTER/providers.csv`

**Verify:**
```bash
ls -la apps/api/data/target_data_model/00000000-0000-0000-0000-000000000001/
```

#### Step 1.3: Generate Observations

```bash
python3 scripts/generate_observations_from_synthetic_data.py \
  --tenant-id 00000000-0000-0000-0000-000000000001 \
  --days 30
```

**Expected Output:**
- Observations generated for each policy
- Files in `data/observations/{tenant_id}/policy-*.json`

**Verify:**
```bash
find data/observations -name "*.json" | wc -l
```

### Phase 2: Start Services

#### Step 2.1: Start API Server

**Terminal 1:**
```bash
cd apps/api
python -m uvicorn uepi_api.main:app --reload --port 8000
```

**Verify API is running:**
```bash
curl http://localhost:8000/docs
# Should show Swagger UI
```

#### Step 2.2: Start Frontend

**Terminal 2:**
```bash
cd apps/web
npm run dev
```

**Verify Frontend is running:**
- Open browser: `http://localhost:3050`
- Should see login page or auto-login

### Phase 3: Test Core Functionalities

#### Test 3.1: Authentication

1. **Auto-login**: Should automatically log in as demo user
2. **User Info**: Check user email, roles in top navigation
3. **Session**: Verify session persists

**API Test:**
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 3.2: Role Selection

1. **Role Switcher**: Click role switcher in top navigation
2. **Available Roles**: Should show Executive, Policy Owner, Analyst, Ops/Clinical
3. **Switch Role**: Select different role, verify navigation changes
4. **Dashboard Route**: Should navigate to persona-specific dashboard

**Verify:**
- Role switcher visible in AppBar
- All 4 personas available
- Navigation updates when role changes

#### Test 3.3: Executive Dashboard

1. **Navigate**: Select "Executive" role or go to `/dashboard/executive`
2. **Verify Data**:
   - Cost trend forecast (with confidence bands)
   - Decision recommendations
   - Risk register
   - "What changed" insights
   - Top policy performance
3. **Data Source**: All data from API (no mock data)

**API Test:**
```bash
curl http://localhost:8000/api/v1/dashboards/executive \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 3.4: Policy Owner Dashboard

1. **Navigate**: Select "Policy Owner" role or go to `/dashboard/policy-owner`
2. **Verify Data**:
   - Policies by state (DRAFT, PROPOSED, APPROVED, ACTIVE, etc.)
   - Policies in flight
   - Assumptions pending
   - Approvals pending
   - Compliance signals
3. **Interactions**: Click "View Policy" buttons, verify navigation

**API Test:**
```bash
curl http://localhost:8000/api/v1/dashboards/policy-owner \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 3.5: Analyst Dashboard

1. **Navigate**: Select "Analyst" role or go to `/dashboard/analyst`
2. **Verify Data**:
   - Analysis queue
   - Model diagnostics
   - Cohort shortcuts
   - Sensitivity runs
   - Data quality metrics
3. **Cohort Builder**: Click "Build Cohort", verify dialog opens

**API Test:**
```bash
curl http://localhost:8000/api/v1/dashboards/analyst \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 3.6: Ops/Clinical Dashboard

1. **Navigate**: Select "Ops/Clinical" role or go to `/dashboard/ops-clinical`
2. **Verify Data**:
   - Provider behavior clusters
   - Appeals volume
   - Patient deferral signals
   - Access risk flags
   - Behavioral patterns
   - Clinical impact metrics

**API Test:**
```bash
curl http://localhost:8000/api/v1/dashboards/ops-clinical \
  -H "Authorization: Bearer dev-token-123"
```

### Phase 4: Policy Management

#### Test 4.1: Policy Catalog

1. **Navigate**: Click "Policies" in sidebar
2. **Verify**:
   - All generated policies listed
   - Policy name, type, status visible
   - "Open Workspace" icon visible
3. **Actions**:
   - Click policy name → Navigate to policy builder
   - Click workspace icon → Navigate to workspace

**API Test:**
```bash
curl http://localhost:8000/api/v1/policies \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 4.2: Policy Workspace

1. **Navigate**: Click "Open Workspace" icon on any policy
2. **Verify Tabs**:
   - **Overview**: Policy summary, metrics, lifecycle state
   - **Scope**: Policy scope (read-only)
   - **Levers**: Policy levers (read-only)
   - **Assumptions**: List of assumptions, Add/Edit/Delete
   - **Guardrails**: List of guardrails, Add/Edit/Delete
   - **Monitoring**: Performance metrics
   - **Versions**: Version history with comparison
   - **Changelog**: Change timeline with filters

**API Test:**
```bash
# Get a policy ID first
POLICY_ID=$(curl -s http://localhost:8000/api/v1/policies \
  -H "Authorization: Bearer dev-token-123" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['id'] if isinstance(d, list) else d['items'][0]['id'])")

# Test workspace endpoint
curl http://localhost:8000/api/v1/policies/$POLICY_ID/workspace \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 4.3: Policy Lifecycle Features

**Versions:**
```bash
curl http://localhost:8000/api/v1/policies/$POLICY_ID/versions \
  -H "Authorization: Bearer dev-token-123"
```

**Assumptions:**
```bash
curl http://localhost:8000/api/v1/policies/$POLICY_ID/assumptions \
  -H "Authorization: Bearer dev-token-123"
```

**Guardrails:**
```bash
curl http://localhost:8000/api/v1/policies/$POLICY_ID/guardrails \
  -H "Authorization: Bearer dev-token-123"
```

**Changelog:**
```bash
curl http://localhost:8000/api/v1/policies/$POLICY_ID/changelog \
  -H "Authorization: Bearer dev-token-123"
```

### Phase 5: Baseline & Analysis

#### Test 5.1: Baseline Analysis

1. **Navigate**: Go to "Analyses" or use API
2. **Create Baseline**:
   - POST to `/api/v1/analyses/baseline`
   - Specify baseline period (e.g., 12 months)
3. **Verify**:
   - Baseline computed from target data model
   - Metrics include utilization, cost, mix
   - Confidence scores calculated

**API Test:**
```bash
curl -X POST http://localhost:8000/api/v1/analyses/baseline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-token-123" \
  -d '{"baseline_period_months": 12, "tenant_id": "00000000-0000-0000-0000-000000000001"}'
```

#### Test 5.2: Predicted Impact

1. **Navigate**: Policy workspace → Overview tab
2. **Verify**: Predicted impact displayed
3. **Data**: From `data/predicted_impacts/{tenant_id}/`

**API Test:**
```bash
curl http://localhost:8000/api/v1/policies/$POLICY_ID/predicted-impact \
  -H "Authorization: Bearer dev-token-123"
```

#### Test 5.3: Observations

1. **Navigate**: Policy workspace → Monitoring tab
2. **Verify**: Observations displayed
3. **Data**: From `data/observations/{tenant_id}/`

**API Test:**
```bash
curl http://localhost:8000/api/v1/observations \
  -H "Authorization: Bearer dev-token-123"
```

### Phase 6: Cohorts

#### Test 6.1: Cohort Builder

1. **Navigate**: Analyst Dashboard → Cohort Builder
2. **Actions**:
   - Select filter criteria
   - Preview matching policies
   - Name and save cohort
3. **Verify**: Cohort saved and appears in list

#### Test 6.2: Cohorts Page

1. **Navigate**: Click "Cohorts" in sidebar
2. **Verify**:
   - All saved cohorts listed
   - Member counts displayed
   - Actions: View, Edit, Delete

**API Test:**
```bash
curl http://localhost:8000/api/v1/cohorts \
  -H "Authorization: Bearer dev-token-123"
```

### Phase 7: Data Verification

#### Test 7.1: Verify No Hardcoded Data

**Check Code:**
- ✅ No hardcoded policies in code
- ✅ No hardcoded observations
- ✅ No hardcoded predicted impacts
- ✅ All dashboards use API data

**Verify Files:**
```bash
# All data should be in files
find apps/api/data/policies -name "*.json" | wc -l
find data/policy_versions -name "*.json" | wc -l
find data/observations -name "*.json" | wc -l
find data/predicted_impacts -name "*.json" | wc -l
```

#### Test 7.2: Verify Target Data Model

**Check Structure:**
```bash
ls -la apps/api/data/target_data_model/00000000-0000-0000-0000-000000000001/
```

**Should have:**
- `CLAIMS_LINES/claims_lines.csv`
- `ELIGIBILITY_ENROLLMENT/enrollment.csv`
- `PROVIDER_MASTER/providers.csv`

### Phase 8: Complete Flow Verification

#### Test 8.1: End-to-End Flow

1. **Data Generation** → ✅ Policies, source data, observations
2. **Data Ingestion** → ✅ Target data model populated
3. **Baseline** → ✅ Computed from target data
4. **Policies** → ✅ Loaded from files
5. **Predicted Impact** → ✅ Generated from assumptions
6. **Observations** → ✅ Generated from post-policy data
7. **Dashboards** → ✅ Display real data from API

#### Test 8.2: All Personas

- ✅ Executive: Strategic view, decisions, risk
- ✅ Policy Owner: Lifecycle management, approvals
- ✅ Analyst: Analysis, cohorts, diagnostics
- ✅ Ops/Clinical: Operational metrics, provider behavior

## Troubleshooting

### API Server Not Starting
- Check port 8000 is available
- Verify Python dependencies installed
- Check API logs for errors

### Frontend Not Loading
- Check port 3050 is available
- Verify Node.js dependencies installed (`npm install`)
- Check browser console for errors

### Data Not Loading
- Verify data files exist in expected locations
- Check API logs for file path issues
- Verify tenant ID matches

### Dashboards Empty
- Check API endpoints return data
- Verify policies have predicted impacts
- Check observations were generated

## Success Criteria

✅ All data generated successfully
✅ API server running and responding
✅ Frontend loading and functional
✅ All persona dashboards show real data
✅ Policy workspace fully functional
✅ All Epic 2 features working
✅ No hardcoded data in code
✅ Complete end-to-end flow verified

## Next Steps

Once all tests pass:
1. Document any issues found
2. Verify all functionalities work as expected
3. Test edge cases
4. Performance testing
5. User acceptance testing


