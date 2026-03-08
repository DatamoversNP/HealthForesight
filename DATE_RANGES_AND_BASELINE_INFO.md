# Date Ranges and Baseline Analysis Information

## Available Date Ranges in Database

### Claims Data
- **Date Range**: 2023-01-01 to 2024-12-28
- **Total Claims**: 1,059,980 claims
- **Available for**: Baseline computation and observation analysis

### Observations
- **Period Range**: 2024-12-01 to 2024-12-31
- **Computed Range**: 2026-02-07 13:37:45 to 2026-02-07 13:40:12
- **Total Observations**: 35

### Policies
- **Total Policies**: 45
- **Policies with Effective Dates**: 44
- **Common Effective Start Dates**:
  - 2024-01-01 (most policies)
  - 2024-04-01 (some policies)
- **End Dates**: Mostly null (ongoing policies)

### Analyses
- **Created Range**: 2026-02-05 to 2026-02-07
- **Total Analyses**: 49

## Recommended Date Ranges for Observations

Based on the available data:

### For General Baseline Computation:
- **Recommended Window**: 2023-01-01 to 2024-12-28 (full claims data range)
- **Rolling Window**: Last 12 months from any given date
- **Pre-Policy Period**: Any period before 2024-01-01 (before most policies went live)

### For Policy-Specific Baseline Computation:
- **Recommended Window**: Period before the policy's effective date
- **Example**: For policies effective 2024-01-01, use 2023-01-01 to 2023-12-31
- **Example**: For policies effective 2024-04-01, use 2023-04-01 to 2024-03-31

### For Observation Computation:
- **Observation Period**: Post-policy period (after policy effective date)
- **Available Range**: 2024-01-01 onwards (when policies went live)
- **Current Observations**: 2024-12-01 to 2024-12-31

## Baseline Types

### 1. General Baseline
- **Purpose**: Overall population metrics before any policies
- **Computation**: Uses all claims data from baseline-eligible periods
- **Use Case**: Compare against all policies, general population health
- **Date Range**: Typically 6-12 months before first policy effective date
- **API Parameter**: `baseline_type: "GENERAL"`, `policy_id: null`

### 2. Policy-Specific Baseline
- **Purpose**: Metrics for the specific population/scope affected by a policy
- **Computation**: Uses claims data filtered by policy scope, before policy effective date
- **Use Case**: Compare observed results against what was expected for this specific policy
- **Date Range**: Period before the specific policy's effective date
- **API Parameter**: `baseline_type: "POLICY_SPECIFIC"`, `policy_id: <uuid>`

## API Usage

### Create General Baseline Analysis
```json
POST /api/v1/analyses/baseline
{
  "name": "General Baseline Q1-Q4 2023",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "baseline_type": "GENERAL",
  "policy_id": null,
  "n_clusters": 5
}
```

### Create Policy-Specific Baseline Analysis
```json
POST /api/v1/analyses/baseline
{
  "name": "Prior Auth Policy Baseline",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "baseline_type": "POLICY_SPECIFIC",
  "policy_id": "6744b13c-12dd-4f71-8884-0f4944205015",
  "n_clusters": 5
}
```

### Refresh Baseline (General)
```json
POST /api/v1/baselines/refresh
{
  "baseline_type": "ROLLING",
  "window_months": 12,
  "refresh_reason": "MANUAL"
}
```

### Refresh Baseline (Policy-Specific)
```json
POST /api/v1/baselines/refresh
{
  "policy_id": "6744b13c-12dd-4f71-8884-0f4944205015",
  "baseline_type": "ROLLING",
  "window_months": 12,
  "refresh_reason": "MANUAL"
}
```

## Best Practices

1. **General Baseline**: Compute once, refresh quarterly or when significant data changes
2. **Policy-Specific Baseline**: Compute for each policy before it goes live, refresh as needed
3. **Observation Periods**: Use post-policy periods (after effective_date) for comparison
4. **Date Selection**: 
   - Use at least 6 months of data for stable baselines
   - Prefer 12 months for more robust metrics
   - Ensure baseline period is before policy effective date
