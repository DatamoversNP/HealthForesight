# How to Use Epic 2: Policy Lifecycle Management

## Overview

Epic 2 provides comprehensive policy lifecycle management with:
- ✅ **Policy Versioning** - Track all changes with version history
- ✅ **Lifecycle States** - DRAFT → PROPOSED → APPROVED → ACTIVE → MONITORING → ITERATING → SUNSET
- ✅ **Assumptions Management** - Document policy assumptions (elasticity, substitution, etc.)
- ✅ **Guardrails** - Set rollback triggers and alerts
- ✅ **Changelog** - Complete audit trail of all changes

## How to Access

### Step 1: Navigate to Policies
1. Go to **Policies** in the sidebar menu
2. You'll see all your policies listed

### Step 2: Open Policy Workspace
1. Find the policy you want to manage
2. Click the **"Open Workspace"** button (or click on the policy name)
3. This opens the **Policy Workspace** page

## Policy Workspace Tabs

The Policy Workspace has **8 tabs**:

### 1. **Overview Tab**
- **What it shows:**
  - Policy summary (name, type, description)
  - Current lifecycle state (DRAFT, ACTIVE, etc.)
  - Key metrics (if available)
  - Policy status

- **How to use:**
  - View policy information
  - See current state
  - Check if policy needs attention

### 2. **Scope Tab**
- **What it shows:**
  - Policy scope configuration (read-only)
  - Who/what the policy applies to
  - Geographic, demographic, clinical filters

- **How to use:**
  - Review policy scope
  - To edit scope, go to Policy Builder

### 3. **Levers Tab**
- **What it shows:**
  - Policy levers (read-only)
  - Configuration settings that drive policy behavior

- **How to use:**
  - Review policy levers
  - To edit levers, go to Policy Builder

### 4. **Assumptions Tab** ⭐
- **What it shows:**
  - List of all policy assumptions
  - Assumption type, description, value/range
  - Confidence scores
  - Source information

- **How to use:**
  - **Add Assumption:**
    1. Click **"Add Assumption"** button
    2. Fill in:
       - **Type**: Elasticity, Substitution Rate, Lag Months, etc.
       - **Description**: What this assumption represents
       - **Value or Range**: Single value OR min/max/best estimate
       - **Source**: Where this assumption came from
       - **Confidence**: 0.0 to 1.0 (how confident you are)
    3. Click **"Save"**

  - **Edit Assumption:**
    1. Click the **edit icon** (pencil) next to an assumption
    2. Modify fields
    3. Click **"Save"**

  - **Delete Assumption:**
    1. Click the **delete icon** (trash) next to an assumption
    2. Confirm deletion

- **Example Assumptions:**
  - **Elasticity**: -0.15 (15% reduction in utilization per 10% cost increase)
  - **Substitution Rate**: 0.3 (30% of denied services will be substituted)
  - **Lag Months**: 3 (3 months before full effect)

### 5. **Guardrails Tab** ⭐
- **What it shows:**
  - List of all guardrails/rollback triggers
  - Metric being monitored
  - Threshold value
  - Action to take if triggered
  - Current status (triggered/not triggered)

- **How to use:**
  - **Add Guardrail:**
    1. Click **"Add Guardrail"** button
    2. Fill in:
       - **Metric Name**: utilization_change_pct, cost_impact, etc.
       - **Threshold Type**: max, min, or change_pct
       - **Threshold Value**: The value that triggers the guardrail
       - **Action**: alert, suspend, or rollback
       - **Description**: What this guardrail monitors
    3. Click **"Save"**

  - **Edit Guardrail:**
    1. Click the **edit icon** next to a guardrail
    2. Modify fields
    3. Click **"Save"**

  - **Delete Guardrail:**
    1. Click the **delete icon** next to a guardrail
    2. Confirm deletion

- **Example Guardrails:**
  - **Max Utilization Drop**: If utilization drops > 20%, send alert
  - **Min Cost Savings**: If cost savings < $10,000, suspend policy
  - **Change Threshold**: If utilization changes > 15% in either direction, rollback

- **Guardrail Status:**
  - 🟢 **Green**: Not triggered (within safe range)
  - 🔴 **Red**: Triggered (action needed)

### 6. **Monitoring Tab**
- **What it shows:**
  - Performance metrics (placeholder for now)
  - Guardrail status
  - Policy health indicators

- **How to use:**
  - View policy performance
  - Check if guardrails are triggered
  - Monitor policy health

### 7. **Versions Tab** ⭐
- **What it shows:**
  - Complete version history
  - Version number, effective dates
  - State per version
  - Change summary
  - Approval information

- **How to use:**
  - **View Versions:**
    - See all versions in chronological order
    - Latest version at top

  - **View Version Details:**
    - Click on a version to see details
    - See what changed in that version

  - **Compare Versions:**
    - Select two versions to compare
    - See diff of changes

- **Automatic Version Creation:**
  - When you save a policy in Policy Builder, version 1 is automatically created
  - Each subsequent save creates a new version

### 8. **Changelog Tab** ⭐
- **What it shows:**
  - Complete audit trail of all changes
  - Who made the change
  - When it was made
  - What changed (old value → new value)
  - Reason for change

- **How to use:**
  - **View Changes:**
    - Scroll through all changes
    - Filter by change type
    - Search for specific changes

  - **Filter Changes:**
    - Filter by: STATE_CHANGE, ASSUMPTION_UPDATE, GUARDRAIL_UPDATE, etc.
    - Filter by date range
    - Search by keyword

- **Automatic Logging:**
  - All changes are automatically logged
  - No manual entry needed

## Lifecycle States

### State Flow:
```
DRAFT → PROPOSED → APPROVED → ACTIVE → MONITORING → ITERATING → SUNSET
```

### How States Work:
1. **DRAFT**: Policy is being created/edited
2. **PROPOSED**: Policy is ready for review
3. **APPROVED**: Policy has been approved
4. **ACTIVE**: Policy is live and active
5. **MONITORING**: Policy is being monitored for performance
6. **ITERATING**: Policy is being adjusted based on data
7. **SUNSET**: Policy has been retired

### Changing State:
- Currently, state changes happen automatically when you:
  - Create a policy → Sets to DRAFT
  - Save a policy → May change state based on configuration
- Future: State promotion workflow UI will be added

## Complete Workflow Example

### Scenario: Create a Policy with Assumptions and Guardrails

1. **Create Policy:**
   - Go to **Policy Builder**
   - Fill in policy details
   - Save → Creates version 1, sets state to DRAFT

2. **Add Assumptions:**
   - Go to **Policies** page
   - Click **"Open Workspace"** on your policy
   - Go to **Assumptions** tab
   - Click **"Add Assumption"**
   - Add: Type="Elasticity", Value=-0.15, Confidence=0.8
   - Save

3. **Add Guardrails:**
   - Go to **Guardrails** tab
   - Click **"Add Guardrail"**
   - Add: Metric="utilization_change_pct", Threshold Type="max", Value=-20, Action="alert"
   - Save

4. **Review Versions:**
   - Go to **Versions** tab
   - See version 1 with all your changes

5. **Check Changelog:**
   - Go to **Changelog** tab
   - See all changes logged automatically

6. **Monitor Policy:**
   - Go to **Monitoring** tab
   - Check if guardrails are triggered
   - View performance metrics

## API Endpoints (For Reference)

All functionality is available via API:

- `GET /api/v1/policies/{policy_id}/workspace` - Get all workspace data
- `GET /api/v1/policies/{policy_id}/versions` - List versions
- `POST /api/v1/policies/{policy_id}/versions` - Create version
- `GET /api/v1/policies/{policy_id}/assumptions` - List assumptions
- `POST /api/v1/policies/{policy_id}/assumptions` - Create assumption
- `PUT /api/v1/policies/{policy_id}/assumptions/{id}` - Update assumption
- `DELETE /api/v1/policies/{policy_id}/assumptions/{id}` - Delete assumption
- `GET /api/v1/policies/{policy_id}/guardrails` - List guardrails
- `POST /api/v1/policies/{policy_id}/guardrails` - Create guardrail
- `PUT /api/v1/policies/{policy_id}/guardrails/{id}` - Update guardrail
- `DELETE /api/v1/policies/{policy_id}/guardrails/{id}` - Delete guardrail
- `GET /api/v1/policies/{policy_id}/changelog` - Get changelog

## Data Storage

All data is stored in files:

```
data/
├── policy_versions/
│   └── {tenant_id}/
│       └── policy-{policy_id}/
│           ├── version-1.json
│           ├── version-2.json
│           └── versions_index.json
├── policy_assumptions/
│   └── {tenant_id}/
│       └── policy-{policy_id}.json
├── policy_guardrails/
│   └── {tenant_id}/
│       └── policy-{policy_id}.json
└── policy_changelog/
    └── {tenant_id}/
        └── policy-{policy_id}.json
```

## Tips

1. **Always add assumptions** when creating policies - they help with accuracy
2. **Set guardrails early** - catch issues before they become problems
3. **Review changelog regularly** - understand what changed and why
4. **Use versions** to track policy evolution over time
5. **Monitor guardrails** - they'll alert you if something goes wrong

## Troubleshooting

**Q: I don't see "Open Workspace" button?**
- Make sure you're on the Policies page
- The button should be in the actions column

**Q: Assumptions/Guestrails not saving?**
- Check browser console for errors
- Verify API is running
- Check network tab for API calls

**Q: Versions not showing?**
- Versions are created automatically when you save a policy
- If you don't see versions, the policy may not have been saved yet

**Q: Changelog is empty?**
- Changelog entries are created automatically
- If empty, no changes have been made yet

---

**You're all set! Start managing your policy lifecycle! 🚀**


