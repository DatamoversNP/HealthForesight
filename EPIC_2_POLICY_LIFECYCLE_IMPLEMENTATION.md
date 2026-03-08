# Epic 2: Policy Lifecycle Management - Implementation Plan

## Overview

Epic 2 implements comprehensive policy lifecycle management, including:
- Policy versioning with change tracking
- Lifecycle state management (DRAFT → PROPOSED → APPROVED → ACTIVE → MONITORING → ITERATING → SUNSET)
- Policy assumptions tracking
- Policy guardrails/rollback triggers
- Policy changelog/audit trail
- Policy workspace UI with tabs

## Data Models (Already Defined)

From `packages/common/src/uepi_common/models_enhanced.py`:
- ✅ `PolicyLifecycleState` (enum)
- ✅ `PolicyVersion`
- ✅ `PolicyAssumption`
- ✅ `PolicyGuardrail`
- ✅ `PolicyChangeLog`
- ✅ `ElasticityRange`

## Implementation Tasks

### Phase 1: Backend Storage (File-Based)

#### Task 1.1: Policy Version Storage
**File:** `apps/api/src/uepi_api/storage_policy_versions.py`

**Functions:**
- `create_policy_version(tenant_id, policy_id, version_data) -> PolicyVersion`
- `get_policy_version(tenant_id, policy_id, version_number) -> Optional[PolicyVersion]`
- `list_policy_versions(tenant_id, policy_id) -> List[PolicyVersion]`
- `get_latest_version(tenant_id, policy_id) -> Optional[PolicyVersion]`
- `update_policy_version(tenant_id, policy_id, version_number, updates) -> Optional[PolicyVersion]`

**Storage Structure:**
```
data/policy_versions/{tenant_id}/policy-{policy_id}/
  ├── version-1.json
  ├── version-2.json
  └── versions_index.json
```

#### Task 1.2: Policy Assumptions Storage
**File:** `apps/api/src/uepi_api/storage_policy_assumptions.py`

**Functions:**
- `create_assumption(tenant_id, policy_id, assumption_data) -> PolicyAssumption`
- `get_assumptions(tenant_id, policy_id) -> List[PolicyAssumption]`
- `update_assumption(tenant_id, policy_id, assumption_id, updates) -> Optional[PolicyAssumption]`
- `delete_assumption(tenant_id, policy_id, assumption_id) -> bool`

**Storage Structure:**
```
data/policy_assumptions/{tenant_id}/policy-{policy_id}/
  └── assumptions.json
```

#### Task 1.3: Policy Guardrails Storage
**File:** `apps/api/src/uepi_api/storage_policy_guardrails.py`

**Functions:**
- `create_guardrail(tenant_id, policy_id, guardrail_data) -> PolicyGuardrail`
- `get_guardrails(tenant_id, policy_id) -> List[PolicyGuardrail]`
- `update_guardrail(tenant_id, policy_id, guardrail_id, updates) -> Optional[PolicyGuardrail]`
- `delete_guardrail(tenant_id, policy_id, guardrail_id) -> bool`
- `check_guardrails(tenant_id, policy_id, metrics) -> List[Dict]` (check if any triggered)

**Storage Structure:**
```
data/policy_guardrails/{tenant_id}/policy-{policy_id}/
  └── guardrails.json
```

#### Task 1.4: Policy Changelog Storage
**File:** `apps/api/src/uepi_api/storage_policy_changelog.py`

**Functions:**
- `create_changelog_entry(tenant_id, policy_id, entry_data) -> PolicyChangeLog`
- `get_changelog(tenant_id, policy_id, limit=100) -> List[PolicyChangeLog]`
- `get_changelog_by_version(tenant_id, policy_id, version_number) -> List[PolicyChangeLog]`

**Storage Structure:**
```
data/policy_changelog/{tenant_id}/policy-{policy_id}/
  └── changelog.json (append-only log)
```

#### Task 1.5: Update Policy Storage
**File:** `apps/api/src/uepi_api/storage_policies.py`

**Updates:**
- Add `update_policy_state(tenant_id, policy_id, new_state, reason, user_id) -> bool`
- Add `get_policy_with_versions(tenant_id, policy_id) -> Dict` (policy + versions)
- Update `update_policy()` to create changelog entry automatically

### Phase 2: Backend API Endpoints

#### Task 2.1: Policy Workspace API
**File:** `apps/api/src/uepi_api/routers/policy_workspace.py`

**Endpoints:**
- `GET /api/v1/policies/{policy_id}/workspace` - Get complete workspace data
- `GET /api/v1/policies/{policy_id}/versions` - List all versions
- `POST /api/v1/policies/{policy_id}/versions` - Create new version
- `GET /api/v1/policies/{policy_id}/versions/{version_number}` - Get specific version
- `PUT /api/v1/policies/{policy_id}/state` - Update lifecycle state
- `GET /api/v1/policies/{policy_id}/assumptions` - Get assumptions
- `POST /api/v1/policies/{policy_id}/assumptions` - Create assumption
- `PUT /api/v1/policies/{policy_id}/assumptions/{assumption_id}` - Update assumption
- `DELETE /api/v1/policies/{policy_id}/assumptions/{assumption_id}` - Delete assumption
- `GET /api/v1/policies/{policy_id}/guardrails` - Get guardrails
- `POST /api/v1/policies/{policy_id}/guardrails` - Create guardrail
- `PUT /api/v1/policies/{policy_id}/guardrails/{guardrail_id}` - Update guardrail
- `DELETE /api/v1/policies/{policy_id}/guardrails/{guardrail_id}` - Delete guardrail
- `GET /api/v1/policies/{policy_id}/changelog` - Get changelog
- `POST /api/v1/policies/{policy_id}/changelog` - Create changelog entry (usually automatic)

### Phase 3: Frontend Components

#### Task 3.1: Policy Workspace Page
**File:** `apps/web/src/pages/PolicyWorkspacePage.tsx`

**Features:**
- Tabbed interface with:
  1. **Overview** - Policy summary, current state, key metrics
  2. **Scope** - Policy scope configuration (reuse ScopeSelectorEnhanced)
  3. **Levers** - Policy levers (reuse LeverList)
  4. **Assumptions** - Assumptions management UI
  5. **Guardrails** - Guardrails/rollback triggers UI
  6. **Monitoring** - Performance metrics, guardrail status
  7. **Versions** - Version history and comparison
  8. **Decisions** - Linked decisions (Epic 3)
  9. **Evidence** - Evidence links (Epic 3)

**State Promotion Workflow:**
- State transition buttons (DRAFT → PROPOSED → APPROVED → ACTIVE)
- Confirmation dialogs for state changes
- Required fields validation before state promotion
- Approval workflow UI (if PROPOSED → APPROVED)

#### Task 3.2: Assumptions Management Component
**File:** `apps/web/src/components/policy/AssumptionsManager.tsx`

**Features:**
- List of assumptions with type, description, range/value
- Add/Edit/Delete assumptions
- Assumption types: elasticity, substitution, lag, etc.
- Confidence scoring UI
- Source tracking

#### Task 3.3: Guardrails Management Component
**File:** `apps/web/src/components/policy/GuardrailsManager.tsx`

**Features:**
- List of guardrails with metric, threshold, action
- Add/Edit/Delete guardrails
- Guardrail types: max, min, change_pct
- Actions: alert, suspend, rollback
- Real-time guardrail status (triggered/not triggered)

#### Task 3.4: Policy Versions Component
**File:** `apps/web/src/components/policy/PolicyVersionsList.tsx`

**Features:**
- Version history table
- Version comparison (diff view)
- Version details modal
- Restore to version functionality

#### Task 3.5: Policy Changelog Component
**File:** `apps/web/src/components/policy/PolicyChangelog.tsx`

**Features:**
- Timeline view of changes
- Filter by change type, user, date range
- Change details with old/new values
- Link to version if applicable

### Phase 4: Integration

#### Task 4.1: Update Policy Builder
- After saving policy, create initial version (v1)
- Create changelog entry for creation
- Set initial state to DRAFT

#### Task 4.2: Update Policy Catalog
- Show lifecycle state badge
- Add "Open Workspace" button
- Show version number
- Show guardrail alerts if any triggered

#### Task 4.3: Update Persona Dashboards
- Policy Owner: Show policies by lifecycle state
- Show assumptions pending review
- Show guardrails triggered
- Show approvals pending

## API Client Updates

**File:** `apps/web/src/lib/api.ts`

Add methods:
- `getPolicyWorkspace(policyId)`
- `getPolicyVersions(policyId)`
- `createPolicyVersion(policyId, versionData)`
- `updatePolicyState(policyId, newState, reason)`
- `getPolicyAssumptions(policyId)`
- `createAssumption(policyId, assumptionData)`
- `updateAssumption(policyId, assumptionId, updates)`
- `deleteAssumption(policyId, assumptionId)`
- `getPolicyGuardrails(policyId)`
- `createGuardrail(policyId, guardrailData)`
- `updateGuardrail(policyId, guardrailId, updates)`
- `deleteGuardrail(policyId, guardrailId)`
- `checkGuardrails(policyId, metrics)`
- `getPolicyChangelog(policyId)`

## File Structure

```
apps/api/src/uepi_api/
├── storage_policy_versions.py      # NEW
├── storage_policy_assumptions.py   # NEW
├── storage_policy_guardrails.py    # NEW
├── storage_policy_changelog.py     # NEW
├── routers/
│   └── policy_workspace.py          # NEW
└── storage_policies.py              # UPDATE

apps/web/src/
├── pages/
│   └── PolicyWorkspacePage.tsx      # NEW
└── components/policy/
    ├── AssumptionsManager.tsx       # NEW
    ├── GuardrailsManager.tsx        # NEW
    ├── PolicyVersionsList.tsx       # NEW
    └── PolicyChangelog.tsx          # NEW
```

## Acceptance Criteria

1. ✅ Can create policy versions with change tracking
2. ✅ Can update policy lifecycle state (with validation)
3. ✅ Can manage policy assumptions (CRUD)
4. ✅ Can manage policy guardrails (CRUD)
5. ✅ Can view policy changelog
6. ✅ Can view version history and compare versions
7. ✅ Guardrails automatically check against metrics
8. ✅ State promotion workflow enforces required fields
9. ✅ All changes logged in changelog
10. ✅ Policy workspace UI shows all tabs with data

## Next Steps

1. Start with Task 1.1: Policy Version Storage
2. Then Task 1.2-1.4: Other storage modules
3. Then Task 2.1: API endpoints
4. Then Task 3.1-3.5: Frontend components
5. Finally Task 4.1-4.3: Integration


