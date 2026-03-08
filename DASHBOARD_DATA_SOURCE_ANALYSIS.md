# Dashboard Data Source Analysis

## Summary

**The dashboards show a MIX of real and simulated data:**

### ✅ **REAL DATA** (From Generated Synthetic Data):
1. **Policy Names** - From `apps/api/data/policies/`
2. **Policy Performance Metrics**:
   - Utilization change percentages
   - Cost impact values
   - Policy IDs
   - Observation counts
3. **Executive Dashboard Metrics**:
   - Total cost impact (calculated from observations)
   - Average utilization change (calculated from observations)
   - Top policies (sorted by real performance data)
   - Risk indicators (derived from real metrics)
4. **Analyst Dashboard Metrics**:
   - Model accuracy (from real observations vs predictions)
   - Data coverage (real count of policies with observations)
   - Model variance (calculated from real performance data)

### ⚠️ **SIMULATED/DERIVED DATA** (Based on Real Data but Structured):
1. **Analysis Queue** (`generateAnalysisQueue()`):
   - Uses **real policy names and IDs**
   - But simulates analysis types, statuses, priorities
   - Creates synthetic analysis items for each policy
2. **Cost Trend Chart** (`generateCostTrend()`):
   - Uses **real cost impact data** as base
   - But generates historical trend with hardcoded base cost ($1M)
   - Forecast bands are calculated from real trends
3. **Sensitivity Runs** (`generateSensitivityRuns()`):
   - Uses **real policy performance data**
   - But adds simulated parameter ranges
   - Results are derived from real utilization/cost changes
4. **Decision Recommendations**:
   - Based on **real performance data**
   - Filters real policies by actual metrics
   - But recommendation text is templated

## Data Flow

```
Generated Synthetic Data Files
    ↓
API Endpoints (dashboard.py, dashboards_persona.py)
    ↓
Loads: policies, observations, analyses from file storage
    ↓
Calculates: metrics, performance metrics
    ↓
Frontend Dashboard Components
    ↓
Transforms real data into visualizations
    ↓
Some visualization structure is simulated (dates, queue items)
```

## What You're Seeing

**Executive Dashboard:**
- ✅ Savings: $2,268,695.6 - **REAL** (from observations)
- ✅ Reduction: 89.09% - **REAL** (from observations)
- ✅ "12 of 17 total" - **REAL** (actual policy count)
- ✅ Policy names in recommendations - **REAL**
- ✅ Utilization % and cost $ in recommendations - **REAL**
- ⚠️ Recommendation structure/template - **SIMULATED**

**Analyst Dashboard:**
- ✅ Policy names in queue - **REAL**
- ✅ Policy IDs - **REAL**
- ✅ "6 of 10 total" - **REAL** (based on actual policies)
- ✅ Model Accuracy - **REAL** (if observations exist)
- ✅ Data Coverage - **REAL** (actual count)
- ⚠️ Analysis queue items structure - **SIMULATED** (but uses real policies)
- ⚠️ Status, priority, dates - **SIMULATED** (for presentation)

## Conclusion

**The core metrics, policy data, and performance numbers are 100% REAL** from your generated synthetic data.

**The visualization structure** (like analysis queue items, cost trend historical data, recommendation cards) is **simulated for presentation** but **based on real data**.

This is a common pattern in dashboards - use real data for metrics, but structure the presentation layer for better UX.

## To Make It 100% Real

If you want everything to be from actual data:
1. Generate actual analysis records (not just policies)
2. Generate actual cost trend historical data
3. Generate actual sensitivity run records
4. Store these in files and load from API

But for now, **the important metrics and policy data you see are real!** ✅


