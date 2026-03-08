# Testing Epic 3: Decision Audit & Defensibility

## Quick Start

I've created a comprehensive test script and guide for testing Epic 3. Here's how to test:

### Method 1: Run Test Script (Recommended)

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="${PYTHONPATH}:$(pwd)/apps/api/src:$(pwd)/packages/common/src"
python3 test_epic3_decisions.py
```

This will test:
- ✅ Decision creation
- ✅ Decision retrieval
- ✅ Listing decisions
- ✅ Audit trail creation
- ✅ Evidence linking
- ✅ Evidence snapshots
- ✅ Approvals
- ✅ Decision finalization
- ✅ Reproducibility pack generation

### Method 2: Test via UI (Easiest)

1. **Start API Server:**
   ```bash
   ./START_API_SERVER.sh
   ```

2. **Start Frontend:**
   ```bash
   cd apps/web
   npm run dev
   ```

3. **Test in Browser:**
   - Go to http://localhost:3050
   - Navigate to **Policies**
   - Click **"Open Workspace"** on any policy
   - Go to **Decisions** tab (9th tab)
   - Click **"Create Decision"**
   - Fill in:
     - Title: "Approve Outpatient MRI Prior Authorization"
     - Recommendation: "Approve policy for implementation"
     - Rationale: "Strong predicted impact with 15% utilization reduction"
     - Confidence Score: 0.85
     - Status: DRAFT
   - Click **"Create"**
   - Go to **Evidence** tab (10th tab)
   - Click **"Link Evidence"**
   - Fill in evidence details and link

### Method 3: Test via API (curl)

If API server is running on `http://localhost:8000`:

#### Create a Decision

```bash
curl -X POST http://localhost:8000/api/v1/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Approve Outpatient MRI Prior Authorization",
    "recommendation": "Approve policy for implementation",
    "rationale": "Strong predicted impact with 15% utilization reduction",
    "confidence_score": 0.85,
    "policy_id": "YOUR_POLICY_ID",
    "assumptions_snapshot": {
      "elasticity": -0.15,
      "substitution_rate": 0.3
    }
  }'
```

#### Get Decisions for Policy

```bash
curl http://localhost:8000/api/v1/policies/YOUR_POLICY_ID/decisions
```

#### Link Evidence

```bash
curl -X POST http://localhost:8000/api/v1/decisions/DECISION_ID/evidence \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_type": "analysis",
    "evidence_id": "ANALYSIS_ID",
    "evidence_version": "1.0",
    "description": "Difference-in-Differences analysis"
  }'
```

#### Get Audit Trail

```bash
curl http://localhost:8000/api/v1/decisions/DECISION_ID/audit-trail
```

#### Get Reproducibility Pack

```bash
curl http://localhost:8000/api/v1/decisions/DECISION_ID/reproducibility-pack
```

## What Gets Created

After testing, you should see:

```
data/
├── decisions/
│   └── 00000000-0000-0000-0000-000000000001/
│       ├── decision-{uuid}.json
│       └── decisions_index.json
├── audit_trail/
│   └── 00000000-0000-0000-0000-000000000001/
│       └── decision-{uuid}/
│           └── audit_trail.json
└── evidence/
    └── 00000000-0000-0000-0000-000000000001/
        └── snapshots/
            └── analysis/
                └── {uuid}/
                    └── 1.0/
                        └── snapshot.json
```

## Verification Checklist

- [ ] Decision created successfully
- [ ] Decision appears in Decisions tab
- [ ] Evidence can be linked
- [ ] Audit trail entries are created
- [ ] Reproducibility pack can be generated
- [ ] Data files are created in `data/` directory

## Troubleshooting

### If test script fails with boto3 error:
The script has been updated to avoid boto3 imports. If you still see errors, use Method 2 (UI testing) instead.

### If API server not running:
```bash
./START_API_SERVER.sh
```

### If frontend not running:
```bash
cd apps/web
npm run dev
```

## Expected Results

After successful testing:
- ✅ Decision JSON file created
- ✅ Audit trail JSON file created
- ✅ Evidence snapshot created
- ✅ Decisions visible in UI
- ✅ Evidence links visible in UI
- ✅ All API endpoints working

---

**Ready to test! Start with Method 2 (UI) for the easiest testing experience!** 🚀


