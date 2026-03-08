# Stage 4 Data Generation Workflow

## Overview
Generate synthetic data from **today onwards** that reflects policy impacts, to be compared against historical baseline data.

## Concept
- **Historical Data (up to yesterday)**: Baseline/pre-policy period
- **New Synthetic Data (from today onwards)**: Post-policy period with policy impacts

## Workflow

### Step 1: Generate Post-Policy Synthetic Data

Run the post-policy data generator:

```bash
python scripts/generate_post_policy_synthetic_data.py \
  --out data/post_policy \
  --months 6 \
  --start-date 2025-01-12  # Or omit to use today's date
```

**What it does:**
- Generates synthetic claims data from the start date (today) onwards
- Applies policy impact scenarios to all generated data (since policies are effective from start date)
- Creates CSV files by month
- Creates a manifest.json file for ingestion

### Step 2: Ingest Post-Policy Data

1. Use the ingestion API or UI to upload the generated data
2. Point to the manifest.json file: `data/post_policy/manifest.json`
3. The data will be ingested and partitioned by date/lob/market

### Step 3: Run Stage 4 Impact Analysis

1. Create an impact analysis via `POST /api/v1/analyses/impact`
2. The analysis will:
   - Use historical data (before policy effective date) as baseline/pre-period
   - Use new synthetic data (from policy effective date) as observed/post-period
   - Compare observed impact against:
     - **Baseline** (Stage 3) - from historical data
     - **Predicted Impact** (Stage 3.5) - from policy metadata
     - **Observed Impact** (Stage 4) - from new synthetic data

### Step 4: View Results

Results will include:
- Observed impact metrics (effect size, percent change, confidence intervals)
- Comparison vs predicted impact (prediction accuracy, error analysis)
- Comparison vs baseline (change from baseline metrics)
- Confidence scores and data sufficiency checks
- Warnings and limitations

## Data Structure

```
Historical Data (Baseline):
- Data up to yesterday (pre-policy period)
- Used for baseline metrics (Stage 3)

Post-Policy Synthetic Data (Observed):
- Data from today onwards
- Reflects policy impacts (all scenarios applied)
- Used for observed impact analysis (Stage 4)
```

## Policy Impact Scenarios Applied

The generator applies these policy impacts to all generated data:

1. **PA for Outpatient MRI**: 30% reduction in outpatient MRI, 40% increase in ER imaging
2. **Site-of-Care for Infusion**: Hospital OP down 40%, Freestanding up 50%
3. **Coverage Relaxation for PT**: PT utilization up 30%
4. **Step Therapy for Biologic**: Infusion down 20%, Specialty visits up 20%
5. **Urgent Care Copay Increase**: Urgent care down 30%, ER up 30%

## Example Usage

```bash
# Generate 6 months of post-policy data starting today
python scripts/generate_post_policy_synthetic_data.py --months 6

# Generate 12 months starting from a specific date
python scripts/generate_post_policy_synthetic_data.py \
  --start-date 2025-01-12 \
  --months 12 \
  --out data/stage4_post_policy
```

## Notes

- The start date should be today or a future date (when policies become effective)
- All generated data reflects policy impacts (since policies are active from start date)
- Historical data remains unchanged (baseline period)
- Stage 4 analysis compares the two periods to measure observed policy impact
