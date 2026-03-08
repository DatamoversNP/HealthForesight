# Generate Predicted Impact for All Policies

## Overview
Predicted impact generation has been set up and is available in both the UI and via API/script.

## Method 1: Using the UI (Recommended)

1. **Navigate to Policies Page**
   - Go to: http://localhost:3050/policies

2. **Click "Generate Predicted Impact (All)" Button**
   - Located at the top of the policies table
   - This will generate predicted impact for all policies that don't already have it

3. **View Predicted Impact**
   - Click the **Psychology icon** (🧠) next to any policy to view its predicted impact
   - Or click "View Predicted Impact" button if available

4. **View in Dialog**
   - A dialog will open with three tabs:
     - **Predicted Impact**: Shows utilization change, cost impact, confidence, etc.
     - **Traceability**: Shows links to baseline, data periods, policy versions
     - **Learning Metrics**: Shows prediction accuracy and elasticity models

## Method 2: Using Python Script

Run the script I created:

```bash
python3 scripts/generate_predicted_impact_all.py
```

This script:
- Uses the batch endpoint `/api/v1/policies/generate-predicted-impact`
- Generates predicted impact for all policies
- Shows status for each policy (generated/skipped/error)

## Method 3: Using API Directly

**Endpoint:** `POST /api/v1/policies/generate-predicted-impact`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer dev-token-123
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/policies/generate-predicted-impact" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-token-123"
```

**Response:**
```json
{
  "total_policies": 5,
  "generated": 3,
  "skipped": 2,
  "errors": 0,
  "details": [
    {
      "policy_id": "...",
      "policy_name": "Policy 1",
      "status": "generated"
    },
    ...
  ]
}
```

## What Gets Generated

For each policy, predicted impact includes:

1. **Utilization Metrics**
   - `utilization_change_per_1k`: Expected change in utilization per 1,000 members
   - `estimated_utilization_reduction_percent`: Percentage reduction in utilization

2. **Cost Metrics**
   - `cost_impact_pmpm`: Expected cost impact per member per month
   - `annual_cost_impact`: Annual cost impact (estimated)

3. **Confidence Metrics**
   - `confidence_score`: Prediction confidence (0-100)
   - `confidence_interval`: Upper and lower bounds for predictions

4. **Behavioral Predictions**
   - Substitution patterns
   - Site of care shifts
   - Provider impact

5. **Elasticity-Based Calculations**
   - Uses policy type elasticity coefficients
   - Considers service category and market factors

## UI Features

### Policy Catalog Page
- **"Generate Predicted Impact (All)"** button: Generates for all policies
- **Psychology icon** (🧠) per policy: Generate/view predicted impact for that policy
- **Predicted Impact Dialog**: Shows comprehensive predicted impact with tabs

### Predicted Impact Display
- **Metrics Cards**: Utilization change, cost impact, confidence
- **Scope Display**: Shows policy scope (LOB, markets, networks, etc.)
- **Traceability Links**: Links to baseline, data periods, policy versions
- **Learning Metrics**: Accuracy tracking and elasticity models

## Next Steps

After generating predicted impact:

1. **View in UI**: Click the Psychology icon next to any policy
2. **Run Observation Analysis**: Compare predicted vs observed impact
3. **Check Learning Metrics**: See how accurate predictions are over time
4. **Generate Scorecards**: Create policy scorecards with predicted impact

## Troubleshooting

### If generation fails:
1. **Check API server is running**: `http://localhost:8000/docs`
2. **Check baseline analysis**: Predicted impact requires baseline to exist
3. **Check logs**: `tail -f api-server.log`
4. **Verify policies exist**: Policies must be loaded first

### Common errors:
- **404 Policy Not Found**: Policy doesn't exist or wrong tenant
- **500 Internal Error**: Check server logs for details
- **Missing baseline**: Run baseline analysis first

## Notes

- Predicted impact is stored in policy metadata
- Generation is idempotent (won't regenerate if already exists unless forced)
- Uses elasticity models based on policy type and service category
- Confidence scores are based on data sufficiency and model quality
