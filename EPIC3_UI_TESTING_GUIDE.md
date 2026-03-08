# Epic 3 UI Testing Guide - Step by Step

## Prerequisites

1. ✅ API server running on http://localhost:8000
2. ✅ Frontend running on http://localhost:3050
3. ✅ Browser ready

## Step-by-Step Testing

### Step 1: Start the Servers

**Terminal 1 - API Server:**
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_API_SERVER.sh
```

Wait for: `INFO: Uvicorn running on http://127.0.0.1:8000`

**Terminal 2 - Frontend:**
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

Wait for: `Local: http://localhost:3050/`

### Step 2: Open Browser

1. Open your browser
2. Navigate to: **http://localhost:3050**
3. You should see the login page or dashboard

### Step 3: Navigate to Policies

1. Click **"Policies"** in the sidebar menu
2. You should see a list of policies
3. If no policies appear, that's okay - we can still test decision creation

### Step 4: Open Policy Workspace

1. Find any policy in the list (or create one if needed)
2. Click **"Open Workspace"** button (or click on the policy name)
3. You should see the **Policy Workspace** page with **10 tabs**:
   - Overview
   - Scope
   - Levers
   - Assumptions
   - Guardrails
   - Monitoring
   - Versions
   - Changelog
   - **Decisions** ← Epic 3 (Tab 9)
   - **Evidence** ← Epic 3 (Tab 10)

### Step 5: Test Decision Creation

1. Click on the **"Decisions"** tab (9th tab)
2. You should see:
   - "No decisions linked to this policy yet" message
   - **"Create Decision"** button
3. Click **"Create Decision"**
4. Fill in the form:
   - **Title**: `Approve Outpatient MRI Prior Authorization`
   - **Recommendation**: `Approve policy for implementation based on strong predicted impact`
   - **Rationale**: `Predicted impact shows 15% utilization reduction with minimal access risk. Confidence score of 0.85 based on historical data and elasticity models.`
   - **Confidence Score**: `0.85` (0.0 to 1.0)
   - **Status**: `DRAFT` (dropdown)
5. Click **"Create"**
6. ✅ **Expected Result**: 
   - Decision appears in the list
   - Shows title, status badge, confidence score
   - Shows creation date

### Step 6: Test Decision Actions

1. **View Decision**: Click the eye icon (👁️) to view full decision details
2. **Edit Decision**: Click the edit icon (✏️) to modify the decision
3. **Finalize Decision**: Click the checkmark icon (✓) to finalize (if not already finalized)

### Step 7: Test Evidence Linking

1. Click on the **"Evidence"** tab (10th tab)
2. You should see:
   - "No evidence linked to this policy yet" message
   - **"Link Evidence"** button
3. Click **"Link Evidence"**
4. Fill in the form:
   - **Evidence Type**: Select `analysis` (dropdown)
   - **Evidence ID**: Enter a UUID (e.g., `12345678-1234-1234-1234-123456789012`)
   - **Version** (optional): `1.0`
   - **Description** (optional): `Difference-in-Differences analysis showing 15% utilization reduction`
5. When prompted for decision ID, enter the decision ID from Step 5
6. Click **"Link Evidence"**
7. ✅ **Expected Result**:
   - Evidence appears in the list
   - Shows evidence type badge
   - Shows evidence ID
   - Shows verification status (if snapshot hash matches)

### Step 8: Verify Data Files

After creating decisions and linking evidence, verify the data files were created:

```bash
# Check decisions
ls -la data/decisions/*/decision-*.json

# Check audit trail
ls -la data/audit_trail/*/decision-*/audit_trail.json

# Check evidence
ls -la data/evidence/*/snapshots/
```

### Step 9: Test Additional Features

1. **Add Approval**:
   - Go back to Decisions tab
   - Click on a decision
   - Add an approval with role and comment

2. **View Audit Trail**:
   - Decisions automatically create audit entries
   - Check that audit trail is being created

3. **Finalize Decision**:
   - Finalize a decision
   - Verify status changes to "FINAL"

## Verification Checklist

- [ ] API server running on port 8000
- [ ] Frontend running on port 3050
- [ ] Can navigate to Policies page
- [ ] Can open Policy Workspace
- [ ] Can see Decisions tab (9th tab)
- [ ] Can see Evidence tab (10th tab)
- [ ] Can create a decision
- [ ] Decision appears in list
- [ ] Can link evidence
- [ ] Evidence appears in list
- [ ] Data files created in `data/` directory

## Troubleshooting

### API Server Not Starting

```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill process if needed
kill -9 $(lsof -ti:8000)

# Start API server
./START_API_SERVER.sh
```

### Frontend Not Starting

```bash
# Check if port 3050 is in use
lsof -ti:3050

# Kill process if needed
kill -9 $(lsof -ti:3050)

# Start frontend
cd apps/web
npm run dev
```

### No Policies Showing

- Policies might not be loaded
- Check API logs for errors
- Try refreshing the page
- You can still test decisions even without policies (use a test policy ID)

### Decisions Tab Not Showing

- Make sure you're on the Policy Workspace page
- Check that you have 10 tabs (Decisions is 9th, Evidence is 10th)
- Refresh the page if needed

### Errors in Browser Console

- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed API calls
- Share error messages for debugging

## Expected UI Behavior

### Decisions Tab:
- ✅ Shows list of decisions (or empty state)
- ✅ "Create Decision" button works
- ✅ Decision form opens in dialog
- ✅ Created decisions appear immediately
- ✅ Status badges show correct colors
- ✅ Confidence scores display correctly
- ✅ Action buttons (view, edit, finalize, delete) work

### Evidence Tab:
- ✅ Shows list of evidence (or empty state)
- ✅ "Link Evidence" button works
- ✅ Evidence form opens in dialog
- ✅ Linked evidence appears immediately
- ✅ Evidence type badges show correctly
- ✅ Verification status shows (if applicable)

## Success Criteria

✅ **Epic 3 is working correctly if:**
1. Decisions tab is visible and functional
2. Evidence tab is visible and functional
3. Can create decisions successfully
4. Can link evidence successfully
5. Data files are created in `data/` directory
6. No errors in browser console
7. API endpoints respond correctly

---

**Ready to test! Follow the steps above to validate Epic 3 functionality!** 🚀


