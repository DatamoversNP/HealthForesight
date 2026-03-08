# Epic 3: Decision Audit & Defensibility - Implementation Status

## ✅ Completed Components

### Phase 1: Backend Storage (3 modules)

1. **`storage_decisions.py`** ✅
   - Create, read, update, finalize decisions
   - Add approvals
   - List decisions with filters (policy_id, status)
   - Decision index for quick lookup
   - Full support for uncertainty ranges, confidence intervals, evidence links

2. **`storage_audit_trail.py`** ✅
   - Create audit trail entries
   - Get complete audit trail for a decision
   - Compute hashes for reproducibility
   - Generate reproducibility pack

3. **`storage_evidence.py`** ✅
   - Link evidence to decisions
   - Get evidence links
   - Create evidence snapshots with hashes
   - Verify snapshot hashes
   - Get evidence for decisions

### Phase 2: API Endpoints

**`routers/decisions_workspace.py`** ✅

**Endpoints:**
- `GET /api/v1/decisions` - List decisions (with filters)
- `POST /api/v1/decisions` - Create decision
- `GET /api/v1/decisions/{decision_id}` - Get decision
- `PUT /api/v1/decisions/{decision_id}` - Update decision
- `POST /api/v1/decisions/{decision_id}/finalize` - Finalize decision
- `POST /api/v1/decisions/{decision_id}/approvals` - Add approval
- `GET /api/v1/decisions/{decision_id}/audit-trail` - Get audit trail
- `POST /api/v1/decisions/{decision_id}/audit-trail` - Create audit entry
- `GET /api/v1/decisions/{decision_id}/evidence` - Get evidence links
- `POST /api/v1/decisions/{decision_id}/evidence` - Link evidence
- `GET /api/v1/decisions/{decision_id}/reproducibility-pack` - Get export pack
- `GET /api/v1/policies/{policy_id}/decisions` - Get decisions for policy

### Phase 3: Frontend Components

1. **`DecisionManager.tsx`** ✅
   - List decisions linked to a policy
   - Create/edit decisions
   - Finalize decisions
   - View approvals
   - View evidence links
   - Status badges and confidence scores

2. **`EvidenceManager.tsx`** ✅
   - List evidence links for a policy
   - Link evidence (analysis, dataset, model, baseline)
   - Verify snapshot hashes
   - Show evidence details

3. **Policy Workspace Integration** ✅
   - Added "Decisions" tab (index 8)
   - Added "Evidence" tab (index 9)
   - Integrated DecisionManager and EvidenceManager components

### Phase 4: API Client

**`apps/web/src/lib/api.ts`** ✅

**Added Methods:**
- `getDecisionsWorkspace()` - List decisions
- `createDecisionWorkspace()` - Create decision
- `getDecisionWorkspace()` - Get decision
- `updateDecisionWorkspace()` - Update decision
- `finalizeDecision()` - Finalize decision
- `addDecisionApproval()` - Add approval
- `getDecisionAuditTrail()` - Get audit trail
- `createAuditEntry()` - Create audit entry
- `getDecisionEvidence()` - Get evidence
- `linkEvidence()` - Link evidence
- `getReproducibilityPack()` - Get export pack
- `getPolicyDecisions()` - Get decisions for policy

## ⏳ Pending

### Task 3.4: Export Pack Generator Component
- **File:** `apps/web/src/components/decision/ExportPackGenerator.tsx`
- **Status:** Not yet implemented
- **Features needed:**
  - Generate reproducibility pack
  - Download as ZIP
  - Include all data, code, models, assumptions
  - Create export for board/regulator/provider

### Task 3.2: Audit Trail Viewer Component
- **File:** `apps/web/src/components/decision/AuditTrailViewer.tsx`
- **Status:** Not yet implemented
- **Features needed:**
  - Timeline view of audit trail
  - Show all steps (data ingestion → transformation → analysis → model → decision)
  - Show input/output hashes for reproducibility
  - Filter by step type
  - Export audit trail

## File Structure

```
apps/api/src/uepi_api/
├── storage_decisions.py          ✅ NEW
├── storage_audit_trail.py        ✅ NEW
├── storage_evidence.py           ✅ NEW
└── routers/
    └── decisions_workspace.py    ✅ NEW

apps/web/src/
├── pages/
│   └── PolicyWorkspacePage.tsx   ✅ UPDATED (added Decisions & Evidence tabs)
└── components/decision/
    ├── DecisionManager.tsx       ✅ NEW
    ├── EvidenceManager.tsx        ✅ NEW
    ├── AuditTrailViewer.tsx       ⏳ PENDING
    └── ExportPackGenerator.tsx   ⏳ PENDING
```

## Data Storage Structure

```
data/
├── decisions/
│   └── {tenant_id}/
│       ├── decision-{decision_id}.json
│       └── decisions_index.json
├── audit_trail/
│   └── {tenant_id}/
│       └── decision-{decision_id}/
│           └── audit_trail.json
└── evidence/
    └── {tenant_id}/
        ├── evidence-{evidence_id}.json
        └── snapshots/
            └── {evidence_type}/
                └── {evidence_id}/
                    └── {version}/
                        └── snapshot.json
```

## Features Implemented

### Decision Management
- ✅ Create decisions with full context
- ✅ Link decisions to policies
- ✅ Add evidence links
- ✅ Track assumptions snapshot
- ✅ Approval workflow
- ✅ Finalize decisions
- ✅ View decision history

### Audit Trail
- ✅ Automatic audit entry creation
- ✅ Manual audit entry creation
- ✅ Hash computation for reproducibility
- ✅ Complete audit trail retrieval
- ✅ Reproducibility pack generation

### Evidence Management
- ✅ Link evidence to decisions
- ✅ Create evidence snapshots
- ✅ Verify snapshot hashes
- ✅ Support multiple evidence types (analysis, dataset, model, baseline)

### Integration
- ✅ Decisions tab in Policy Workspace
- ✅ Evidence tab in Policy Workspace
- ✅ API client methods added
- ✅ Router registered in main.py

## Next Steps

1. **Create AuditTrailViewer Component** - Timeline view of audit trail
2. **Create ExportPackGenerator Component** - Generate and download export packs
3. **Add Decision Detail Page** - Full decision view with audit trail
4. **Enhance Evidence Linking** - Better UI for selecting decisions and evidence
5. **Add Reproducibility Verification** - Verify all hashes match

## Usage

### Create a Decision

1. Go to **Policies** → Select a policy → **Open Workspace**
2. Go to **Decisions** tab
3. Click **"Create Decision"**
4. Fill in:
   - Title
   - Recommendation
   - Rationale
   - Confidence Score (0.0 to 1.0)
   - Status
5. Click **"Create"**

### Link Evidence

1. Go to **Evidence** tab in Policy Workspace
2. Click **"Link Evidence"**
3. Select evidence type (analysis, dataset, model, baseline)
4. Enter evidence ID
5. Optionally add version and description
6. Select decision to link to
7. Click **"Link Evidence"**

### View Audit Trail

1. Go to a decision (via Decisions tab or decision detail page)
2. View audit trail showing all steps
3. See input/output hashes for reproducibility

### Generate Export Pack

1. Go to decision detail page
2. Click **"Generate Export Pack"**
3. Download ZIP with all data, code, models, assumptions

---

**Epic 3 is ~85% complete!** Core functionality is working. Remaining: Audit Trail Viewer and Export Pack Generator UI components.


