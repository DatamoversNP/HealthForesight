# How to Improve Confidence Score

## Understanding Confidence Score (0-100)

The confidence score reflects how reliable your scenario projections are. A score of **15-25%** indicates low confidence, while **80%+** is considered high confidence.

## Factors Affecting Confidence Score

The confidence score starts at **100** and is reduced based on several factors:

### 1. **Baseline Data Size** (-30 points if insufficient)
   - **Penalty:** -30 points if `claim_count < 100`
   - **What it means:** You don't have enough historical claims data
   - **How to fix:**
     - ✅ Upload more historical claims data
     - ✅ Increase the baseline period (e.g., 18-24 months instead of 12)
     - ✅ Ensure you're including all relevant claims for the policy scope
     - **Target:** At least 500+ claims for higher confidence

### 2. **Projection Horizon Length** (-10 points if too long)
   - **Penalty:** -10 points if `projection_months > 12`
   - **What it means:** Longer projections have more uncertainty
   - **How to fix:**
     - ✅ Use shorter projection periods (6-12 months)
     - ✅ For longer-term projections (18-24 months), expect lower confidence
     - **Target:** 12 months or less for optimal confidence

### 3. **Confidence Interval Width** (-15 points per metric if too wide)
   - **Penalty:** -15 points per metric if confidence interval width > 50%
   - **What it means:** High uncertainty in projections (wide ranges)
   - **How to fix:**
     - ✅ Use learned elasticity models instead of defaults
       - Run elasticity analysis on your historical data
       - This provides more accurate projections
     - ✅ Ensure baseline data has sufficient variation
     - ✅ Use policies with historical analogs (similar policies from past)
     - **Target:** Confidence interval width < 30% for better scores

## Quick Actions to Improve Confidence

### Immediate (Easy Wins)

1. **Reduce Projection Horizon**
   - Change from 20 months to 12 months → **+10 points**
   - This alone could move you from 15% to 25%

2. **Ensure Sufficient Baseline Data**
   - Verify you have at least 500+ claims in baseline
   - Extend baseline period if needed

### Medium-term (More Impact)

3. **Run Elasticity Analysis**
   - Navigate to "Elasticity Curves" tab
   - Click "Create Elasticity Analysis"
   - Wait for it to complete (uses your historical data)
   - Re-run your scenario → Better projections → Narrower intervals → **+15-30 points**

4. **Improve Data Quality**
   - Ensure claims data has complete information
   - Include longer historical periods (18-24 months)
   - Clean any data quality issues

### Long-term (Best Results)

5. **Build Historical Knowledge**
   - Run baseline analysis regularly
   - Track actual vs predicted impacts (Stage 3.5)
   - System learns and improves over time

## Example Confidence Score Breakdown

For a scenario with **15% confidence**:
- Starting score: 100
- Low claim count (<100): -30 → 70
- Long projection (>12 months): -10 → 60
- Wide confidence intervals (2 metrics): -30 → 30
- Final: **30%** (or lower if other factors)

**To reach 80%:**
- Start: 100
- Sufficient data (500+ claims): -0 → 100
- Short projection (≤12 months): -0 → 100
- Narrow intervals (from elasticity model): -15 → **85%** ✅

## Recommendations for Your Current Scenario

Based on your **15-25% confidence**:

1. **Check baseline data:**
   ```bash
   # Check if you have sufficient claims data
   # Look at the baseline metrics - claim_count should be > 500
   ```

2. **Reduce projection horizon:**
   - Change from 20 months to 12 months
   - This alone can improve confidence significantly

3. **Run elasticity analysis:**
   - Go to "Elasticity Curves" tab
   - Create elasticity analysis for your policies
   - This will use historical data to learn better models
   - Re-run scenarios → Should see improvement

4. **Verify data quality:**
   - Ensure you have at least 12+ months of historical data
   - Check that claims data includes all necessary fields
   - More complete data = better projections = higher confidence

## Summary

**Low confidence (15-25%)** typically means:
- ❌ Insufficient baseline data (<100 claims)
- ❌ Long projection horizon (>12 months)
- ❌ Wide uncertainty intervals (>50%)

**High confidence (80%+)** requires:
- ✅ Sufficient baseline data (500+ claims)
- ✅ Reasonable projection horizon (≤12 months)
- ✅ Learned elasticity models from your data
- ✅ Narrow confidence intervals (<30% width)

The **biggest impact** comes from:
1. Running elasticity analysis (learns from your data)
2. Ensuring sufficient baseline data
3. Using shorter projection horizons
