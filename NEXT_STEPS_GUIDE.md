# Next Steps Guide 🚀

## Current Status ✅
- ✅ Data regenerated (288,180 claims with valid dates)
- ✅ Post-policy data created (Dec 27-31, 2025)
- ✅ Baseline analysis running perfectly

## Next Steps (In Order)

### Step 1: Generate Predicted Impact for All Policies

**Option A: Via UI (Recommended)**
1. Open: http://localhost:3050/policies
2. For each policy in the list:
   - Click the **"Generate Predicted Impact"** button (or icon)
   - Wait for it to complete (should take 10-30 seconds per policy)
3. Verify: Each policy should now show predicted impact metrics when you click "View Predicted Impact"

**Option B: Via API (If you want to automate)**
```bash
# List all policies first
curl http://localhost:8000/api/v1/policies

# Generate predicted impact for each policy ID
# Replace {policy_id} with actual policy IDs from the list above
curl -X POST http://localhost:8000/api/v1/policies/{policy_id}/predicted-impact

# OR use bulk endpoint if available:
curl -X POST http://localhost:8000/api/v1/policies/predicted-impact/all
```

**What This Does:**
- Uses elasticity models to predict policy impacts
- Calculates expected utilization changes, cost changes, substitution patterns
- Stores predicted impact with each policy for later comparison

---

### Step 2: Run Observation Analysis

**After predicted impact is generated**, you can run observation analysis to compare:
- **Baseline**: Pre-policy historical metrics (from baseline analysis)
- **Predicted**: Expected impact (from predicted impact generation)
- **Observed**: Actual outcomes from post-policy data (Dec 27-31, 2025)

**Via UI:**
1. Navigate to the **Impact Analysis** or **Observations** page
2. Select a policy
3. Click **"Run Observation Analysis"** or **"Compare Observed vs Predicted"**
4. Review the comparison:
   - How accurate were the predictions?
   - What actually happened vs. what was predicted?
   - What behavioral changes occurred?

**What This Shows:**
- Prediction accuracy (predicted vs observed)
- Actual policy effects
- Behavioral explanations (substitution, volume shifts, etc.)
- Learning metrics for model improvement

---

## Quick Command Reference

```bash
# Check API server is running
curl http://localhost:8000/health

# List all policies
curl http://localhost:8000/api/v1/policies | jq '.[] | {id: .id, name: .name}'

# Generate predicted impact for a specific policy (replace POLICY_ID)
curl -X POST http://localhost:8000/api/v1/policies/POLICY_ID/predicted-impact

# Check baseline analysis results
curl http://localhost:8000/api/v1/analyses?analysis_type=BASELINE | jq '.[] | {id: .id, status: .status}'
```

---

## Expected Timeline

- **Step 1 (Predicted Impact)**: 5-10 minutes for all policies
- **Step 2 (Observation Analysis)**: 2-5 minutes per policy

---

## Troubleshooting

**If predicted impact generation fails:**
- Check API logs: `tail -f api-server.log`
- Verify policy has levers configured
- Ensure elasticity models are available

**If observation analysis fails:**
- Verify baseline analysis completed successfully
- Verify predicted impact was generated for the policy
- Check that post-policy data is in the date range

---

## Success Criteria

✅ **After Step 1**, you should see:
- Predicted impact metrics displayed in policy catalog
- Confidence factors shown for each prediction
- Expected utilization/cost changes visible

✅ **After Step 2**, you should see:
- Comparison charts (baseline vs predicted vs observed)
- Prediction accuracy metrics
- Behavioral explanations for observed changes
- Learning metrics for model refinement

---

## Ready to Start?

**Start with Step 1: Generate Predicted Impact**
👉 Go to: http://localhost:3050/policies

Then proceed to Step 2 once predicted impact is generated for all policies.
