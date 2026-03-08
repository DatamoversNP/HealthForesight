# Epic 3: Decision Audit & Defensibility - Quick Start Guide

## ✅ What's Implemented

Epic 3 is **~85% complete** with core functionality working:

- ✅ **Decision Storage** - Full CRUD operations
- ✅ **Audit Trail** - Complete audit trail with hashes
- ✅ **Evidence Management** - Link evidence to decisions
- ✅ **API Endpoints** - All decision workspace endpoints
- ✅ **UI Components** - DecisionManager and EvidenceManager
- ✅ **Policy Workspace Integration** - Decisions and Evidence tabs

## How to Use

### Step 1: Access Policy Workspace

1. Go to **Policies** in the sidebar
2. Click **"Open Workspace"** on any policy
3. You'll see **10 tabs** now (added Decisions and Evidence)

### Step 2: Create a Decision

1. Go to **Decisions** tab (tab 9)
2. Click **"Create Decision"**
3. Fill in:
   - **Title**: e.g., "Approve Outpatient MRI Prior Authorization"
   - **Recommendation**: e.g., "Approve policy for implementation"
   - **Rationale**: e.g., "Strong predicted impact with 15% utilization reduction"
   - **Confidence Score**: 0.0 to 1.0 (e.g., 0.85 = 85% confidence)
   - **Status**: DRAFT, PENDING_APPROVAL, APPROVED, or FINAL
4. Click **"Create"**

### Step 3: Link Evidence

1. Go to **Evidence** tab (tab 10)
2. Click **"Link Evidence"**
3. Fill in:
   - **Evidence Type**: analysis, dataset, model, or baseline
   - **Evidence ID**: UUID of the evidence
   - **Version** (optional): Version identifier
   - **Description** (optional): What this evidence supports
4. Select decision to link to
5. Click **"Link Evidence"**

### Step 4: View Decisions

- **Decisions Tab**: See all decisions linked to the policy
- **View Details**: Click the eye icon to view full decision
- **Edit**: Click edit icon (if not finalized)
- **Finalize**: Click checkmark icon to finalize decision

### Step 5: Add Approvals

1. Go to a decision
2. Add approval with role and comment
3. Decision status updates automatically

## API Endpoints Available

All endpoints are available at `/api/v1/decisions/*`:

- `GET /decisions` - List all decisions
- `POST /decisions` - Create decision
- `GET /decisions/{id}` - Get decision
- `PUT /decisions/{id}` - Update decision
- `POST /decisions/{id}/finalize` - Finalize decision
- `POST /decisions/{id}/approvals` - Add approval
- `GET /decisions/{id}/audit-trail` - Get audit trail
- `GET /decisions/{id}/evidence` - Get evidence
- `POST /decisions/{id}/evidence` - Link evidence
- `GET /decisions/{id}/reproducibility-pack` - Get export pack
- `GET /policies/{policy_id}/decisions` - Get decisions for policy

## Data Storage

All data is stored in files:

```
data/
├── decisions/{tenant_id}/
│   ├── decision-{id}.json
│   └── decisions_index.json
├── audit_trail/{tenant_id}/decision-{id}/
│   └── audit_trail.json
└── evidence/{tenant_id}/
    ├── evidence-{id}.json
    └── snapshots/{type}/{id}/{version}/snapshot.json
```

## What's Next

1. **Audit Trail Viewer** - Timeline UI component (pending)
2. **Export Pack Generator** - Download ZIP with all data (pending)
3. **Decision Detail Page** - Full decision view (pending)

## Testing

1. **Create a decision:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/decisions \
     -H "Authorization: Bearer dev-token-123" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test Decision",
       "recommendation": "Approve policy",
       "rationale": "Strong predicted impact",
       "confidence_score": 0.85,
       "policy_id": "your-policy-id"
     }'
   ```

2. **Get decisions for a policy:**
   ```bash
   curl http://localhost:8000/api/v1/policies/{policy_id}/decisions \
     -H "Authorization: Bearer dev-token-123"
   ```

3. **Get reproducibility pack:**
   ```bash
   curl http://localhost:8000/api/v1/decisions/{decision_id}/reproducibility-pack \
     -H "Authorization: Bearer dev-token-123"
   ```

---

**Epic 3 core functionality is complete and ready to use!** 🎉


