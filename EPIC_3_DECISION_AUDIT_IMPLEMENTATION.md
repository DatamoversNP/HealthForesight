# Epic 3: Decision Audit & Defensibility - Implementation Plan

## Overview

Epic 3 implements comprehensive decision audit and defensibility features:
- Decision records with full context
- Complete audit trail for reproducibility
- Evidence linking to analyses, datasets, models
- Assumptions snapshot at decision time
- Approval workflow
- Export pack generation for regulatory/board review

## Data Models (Already Defined)

From `packages/common/src/uepi_common/models_enhanced.py`:
- ✅ `Decision` - Decision record with full audit trail
- ✅ `AuditTrailEntry` - Audit trail entry for reproducibility
- ✅ `EvidenceLink` - Link to evidence supporting decision
- ✅ `UncertaintyRange` - P10/P50/P90 ranges
- ✅ `ConfidenceInterval` - Confidence intervals

## Implementation Tasks

### Phase 1: Backend Storage (File-Based)

#### Task 1.1: Decision Storage
**File:** `apps/api/src/uepi_api/storage_decisions.py`

**Functions:**
- `create_decision(tenant_id, decision_data) -> Decision`
- `get_decision(tenant_id, decision_id) -> Optional[Decision]`
- `list_decisions(tenant_id, policy_id=None, status=None) -> List[Decision]`
- `update_decision(tenant_id, decision_id, updates) -> Optional[Decision]`
- `finalize_decision(tenant_id, decision_id, finalized_by) -> Optional[Decision]`
- `add_approval(tenant_id, decision_id, approval_data) -> Optional[Decision]`

**Storage Structure:**
```
data/decisions/{tenant_id}/
  ├── decision-{decision_id}.json
  └── decisions_index.json
```

#### Task 1.2: Audit Trail Storage
**File:** `apps/api/src/uepi_api/storage_audit_trail.py`

**Functions:**
- `create_audit_entry(tenant_id, decision_id, entry_data) -> AuditTrailEntry`
- `get_audit_trail(tenant_id, decision_id) -> List[AuditTrailEntry]`
- `get_audit_trail_by_step(tenant_id, step_type, step_id) -> List[AuditTrailEntry]`
- `get_reproducibility_pack(tenant_id, decision_id) -> Dict` (all data needed to reproduce)

**Storage Structure:**
```
data/audit_trail/{tenant_id}/decision-{decision_id}/
  └── audit_trail.json (append-only log)
```

#### Task 1.3: Evidence Storage
**File:** `apps/api/src/uepi_api/storage_evidence.py`

**Functions:**
- `link_evidence(tenant_id, decision_id, evidence_link) -> EvidenceLink`
- `get_evidence_links(tenant_id, decision_id) -> List[EvidenceLink]`
- `get_evidence_snapshot(tenant_id, evidence_type, evidence_id, version=None) -> Dict`
- `create_evidence_snapshot(tenant_id, evidence_type, evidence_id, snapshot_data) -> str` (returns hash)

**Storage Structure:**
```
data/evidence/{tenant_id}/
  ├── evidence-{evidence_id}.json
  └── snapshots/{evidence_type}/{evidence_id}/{version}/snapshot.json
```

### Phase 2: Backend API Endpoints

#### Task 2.1: Decision Workspace API
**File:** `apps/api/src/uepi_api/routers/decisions_workspace.py`

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

#### Task 3.1: Decision Manager Component
**File:** `apps/web/src/components/decision/DecisionManager.tsx`

**Features:**
- Create/edit decision
- Link to policies, analyses, evidence
- Add assumptions snapshot
- Set confidence score and uncertainty ranges
- Approval workflow UI
- Finalize decision

#### Task 3.2: Audit Trail Viewer Component
**File:** `apps/web/src/components/decision/AuditTrailViewer.tsx`

**Features:**
- Timeline view of audit trail
- Show all steps (data ingestion → transformation → analysis → model → decision)
- Show input/output hashes for reproducibility
- Filter by step type
- Export audit trail

#### Task 3.3: Evidence Manager Component
**File:** `apps/web/src/components/decision/EvidenceManager.tsx`

**Features:**
- List evidence links
- Add evidence (analysis, dataset, model, baseline)
- View evidence snapshots
- Show evidence versions
- Verify snapshot hashes

#### Task 3.4: Export Pack Generator
**File:** `apps/web/src/components/decision/ExportPackGenerator.tsx`

**Features:**
- Generate reproducibility pack
- Include all data, code, models, assumptions
- Create export for board/regulator/provider
- Download as ZIP
- Include audit trail

### Phase 4: Integration

#### Task 4.1: Update Policy Workspace
- Add "Decisions" tab to Policy Workspace
- Add "Evidence" tab to Policy Workspace
- Show linked decisions in Overview tab
- Link decisions to policy versions

#### Task 4.2: Update Decision Pages
- Create Decisions page (list all decisions)
- Create Decision Detail page
- Add decision creation from Policy Workspace

#### Task 4.3: Update API Client
- Add all decision API methods to `api.ts`

## File Structure

```
apps/api/src/uepi_api/
├── storage_decisions.py          # NEW
├── storage_audit_trail.py        # NEW
├── storage_evidence.py           # NEW
└── routers/
    └── decisions_workspace.py    # NEW

apps/web/src/
├── pages/
│   ├── DecisionsPage.tsx         # UPDATE (add decision detail view)
│   └── DecisionDetailPage.tsx    # NEW
└── components/decision/
    ├── DecisionManager.tsx       # NEW
    ├── AuditTrailViewer.tsx       # NEW
    ├── EvidenceManager.tsx        # NEW
    └── ExportPackGenerator.tsx   # NEW
```

## Acceptance Criteria

1. ✅ Can create decision with full context
2. ✅ Can link evidence to decision
3. ✅ Can view complete audit trail
4. ✅ Can generate reproducibility pack
5. ✅ Can add approvals to decision
6. ✅ Can finalize decision
7. ✅ Decisions linked to policies in Policy Workspace
8. ✅ Evidence tab shows all linked evidence
9. ✅ Export pack includes all necessary data
10. ✅ Audit trail shows all steps with hashes

## Next Steps

1. Start with Task 1.1: Decision Storage
2. Then Task 1.2-1.3: Audit Trail and Evidence Storage
3. Then Task 2.1: API Endpoints
4. Then Task 3.1-3.4: Frontend Components
5. Finally Task 4.1-4.3: Integration


