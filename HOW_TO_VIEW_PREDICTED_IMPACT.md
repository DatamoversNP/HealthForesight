# How to View Predicted Impact in the UI

## Location

Predicted Impact (Stage 3.5) is available on the **Policy Catalog** page.

## Step-by-Step Instructions

### 1. Navigate to Policy Catalog

- Open the application
- In the left sidebar, click **"Policies"**
- Or go directly to: `http://localhost:3050/policies`

### 2. Find the Psychology Icon Button

In the Policy Catalog table, each policy row has an **Actions** column (rightmost column).

Look for the **Psychology icon** (🧠) button in the Actions column for each policy.

The Actions column contains these buttons (in order):
1. 🧠 **Psychology Icon** - View/Generate Predicted Impact
2. ✏️ **Edit Icon** - Edit Policy
3. ▶️/⏹️ **Activate/Deactivate Icon** - Toggle policy status
4. 🗑️ **Delete Icon** - Delete Policy

### 3. Click the Psychology Icon

Click the **Psychology icon button** (🧠) for any policy to:
- **View** predicted impact if it already exists
- **Generate** predicted impact if it doesn't exist yet

### 4. View Predicted Impact Dialog

A dialog window will open titled **"Predicted Impact (Stage 3.5)"** showing:

- **Metrics**:
  - Utilization Reduction (percentage)
  - Cost Impact (PMPM - Per Member Per Month)
  - Confidence Score

- **Impact by Lever**:
  - Breakdown of impact for each policy lever
  - Estimated impact level and confidence per lever

- **Behavioral Risks**:
  - Substitution risk
  - Provider circumvention risk
  - Other behavioral considerations

- **Notes**:
  - Generation information and notes

### 5. Dialog Actions

In the dialog, you can:
- **View** the predicted impact details
- **Regenerate** predicted impact (if you want to update it)
- **Close** the dialog

## Visual Guide

```
Policy Catalog Page
├── Policies Table
│   ├── Columns: Name | Type | Status | Description | Owner Role | Updated | Actions
│   └── Actions Column (rightmost)
│       ├── 🧠 Psychology Icon ← Click this to view predicted impact
│       ├── ✏️ Edit Icon
│       ├── ▶️/⏹️ Activate/Deactivate Icon
│       └── 🗑️ Delete Icon
│
└── Top Action Buttons
    ├── "Create with Builder"
    ├── "Import Policy"
    ├── "Complete Configurations (All)" ← Use this first to add levers
    ├── "Generate Predicted Impact (All)" ← Or use this to generate for all
    └── "Quick Create"
```

## Quick Actions

### Generate Predicted Impact for All Policies

At the top of the Policy Catalog page, there's a button:
- **"Generate Predicted Impact (All)"** (with refresh icon)

Click this to generate predicted impact for all policies that don't have it yet.

### Complete Configurations First (Recommended)

Before generating predicted impact, ensure policies have complete configurations:
1. Click **"Complete Configurations (All)"** (with settings/gear icon)
2. Wait for it to complete
3. Then click **"Generate Predicted Impact (All)"**

## What You'll See

### If Predicted Impact Exists

- Dialog opens immediately
- Shows complete predicted impact metrics and breakdown
- Confidence scores and behavioral risks displayed
- All levers shown with individual impact estimates

### If Predicted Impact Doesn't Exist

- Dialog opens with loading spinner
- Automatically triggers generation
- Shows progress
- Then displays the generated predicted impact

### If Policy Has No Levers

- Warning message: "This policy does not have policy levers defined"
- Instructions to edit the policy using Policy Builder to add levers first

## Example: Viewing Predicted Impact

1. **Go to**: `http://localhost:3050/policies`
2. **Find**: "Outpatient MRI Prior Authorization" policy
3. **Click**: Psychology icon (🧠) in the Actions column
4. **View**: Dialog shows:
   - Utilization Reduction: 18.0%
   - Cost Impact: $2.50 PMPM
   - Confidence: 83%
   - Impact breakdown by lever
   - Behavioral risks

## Troubleshooting

### Can't See Predicted Impact

1. **Check if policies have levers**: Use "Complete Configurations (All)" button
2. **Generate predicted impact**: Use "Generate Predicted Impact (All)" button
3. **Or generate individually**: Click Psychology icon on each policy

### Dialog Shows "Not Found"

- This means predicted impact hasn't been generated yet
- Click "Generate Predicted Impact" button in the dialog
- Or use the "Generate Predicted Impact (All)" button at the top

### Error: "Policy does not have policy levers"

- Policy needs levers configured first
- Click "Complete Configurations (All)" button
- Or edit the policy using Policy Builder to add levers manually

## Summary

**Location**: Policy Catalog page (`/policies`)  
**Button**: Psychology icon (🧠) in Actions column  
**Action**: Click to view/generate predicted impact  
**Bulk Action**: "Generate Predicted Impact (All)" button at top of page

Predicted impact is now available for all 8 policies that were just seeded!
