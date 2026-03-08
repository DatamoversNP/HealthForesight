# Testing Epic 3: Decision Audit & Defensibility

## Quick Test Guide

### Option 1: Run Test Script (Recommended)

Run the comprehensive test script:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
python3 test_epic3_decisions.py
```

This will:
1. ✅ Create a decision
2. ✅ Retrieve the decision
3. ✅ List all decisions
4. ✅ Create audit trail entries
5. ✅ Get audit trail
6. ✅ Link evidence to decision
7. ✅ Create evidence snapshot
8. ✅ Add approval to decision
9. ✅ Finalize decision
10. ✅ Generate reproducibility pack

### Option 2: Test via API (If Server Running)

If your API server is running on `http://localhost:8000`, you can test via curl:

#### 1. Create a Decision

```bash
curl -X POST http://localhost:8000/api/v1/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Approve Outpatient MRI Prior Authorization",
    "recommendation": "Approve policy for implementation",
    "rationale": "Strong predicted impact with 15% utilization reduction",
    "confidence_score": 0.85,
    "policy_id": "YOUR_POLICY_ID_HERE",
    "assumptions_snapshot": {
      "elasticity": -0.15,
      "substitution_rate": 0.3
    }
  }'
```

#### 2. Get Decisions for a Policy

```bash
curl http://localhost:8000/api/v1/policies/YOUR_POLICY_ID/decisions
```

#### 3. Link Evidence

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

#### 4. Get Audit Trail

```bash
curl http://localhost:8000/api/v1/decisions/DECISION_ID/audit-trail
```

#### 5. Get Reproducibility Pack

```bash
curl http://localhost:8000/api/v1/decisions/DECISION_ID/reproducibility-pack
```

### Option 3: Test via UI

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
   - Go to **Decisions** tab (tab 9)
   - Click **"Create Decision"**
   - Fill in the form and create
   - Go to **Evidence** tab (tab 10)
   - Click **"Link Evidence"**
   - Link evidence to the decision

## Expected Results

### After Running Test Script

You should see:
- ✅ Decision created in `data/decisions/{tenant_id}/decision-{id}.json`
- ✅ Audit trail in `data/audit_trail/{tenant_id}/decision-{id}/audit_trail.json`
- ✅ Evidence snapshots in `data/evidence/{tenant_id}/snapshots/`

### File Structure Created

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
- [ ] Decision can be retrieved
- [ ] Decisions list shows new decision
- [ ] Audit trail entry created
- [ ] Audit trail can be retrieved
- [ ] Evidence linked to decision
- [ ] Evidence snapshot created
- [ ] Approval added to decision
- [ ] Decision finalized
- [ ] Reproducibility pack generated

## Troubleshooting

### Error: "No module named 'uepi_api'"

Make sure you're running from the project root and PYTHONPATH is set:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/apps/api/src:$(pwd)/packages/common/src"
python3 test_epic3_decisions.py
```

### Error: "Policy not found"

The test script will use a test UUID if no policies are found. This is fine for testing the decision functionality.

### Error: "Permission denied"

Make sure the `data/` directory is writable:

```bash
chmod -R 755 data/
```

## Next Steps

After successful testing:
1. ✅ Verify all data files are created correctly
2. ✅ Check that decisions appear in UI
3. ✅ Test evidence linking in UI
4. ✅ Verify audit trail is complete
5. ✅ Test reproducibility pack download

---

**Ready to test! Run `python3 test_epic3_decisions.py` to get started!** 🚀


