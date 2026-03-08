# Calculation Methodology Documentation

This document defines the standard formulas used for all baseline analysis calculations. These formulas follow industry-standard healthcare analytics practices and are designed to be defensible to clients.

## Core Metrics

### 1. Utilization Rate (per 1,000 member-months)

**Formula:**
```
util_rate_total_per_1000_mm = (Total claim lines / Member-months) × 1,000
```

**Components:**
- **Total claim lines**: Count of all claim line records in the analysis period
- **Member-months**: Sum of months of enrollment for all unique members
  - If enrollment data available: Sum of (end_date - start_date) in months for each member
  - If enrollment data not available: Unique members × 12 (annualized estimate)

**Validation:**
- Member-months must be > 0
- Result must be non-negative
- Relative error tolerance: 1%

**Example:**
- Total claims: 50,000
- Member-months: 120,000
- Utilization rate: (50,000 / 120,000) × 1,000 = 416.67 claims per 1,000 member-months

---

### 2. Cost Per Member Per Month (PMPM)

**Formula:**
```
allowed_pmpm_total = Total allowed amount / Member-months
```

**Components:**
- **Total allowed amount**: Sum of `allowed_amount` (or `paid_amount` if `allowed_amount` not available) for all claim lines
- **Member-months**: Same as utilization rate calculation

**Validation:**
- Member-months must be > 0
- Result must be non-negative
- Relative error tolerance: 1%

**Example:**
- Total allowed: $12,000,000
- Member-months: 120,000
- PMPM: $12,000,000 / 120,000 = $100.00 PMPM

---

### 3. Average Cost Per Claim

**Formula:**
```
avg_cost_per_claim = Total cost / Total claims
```

**Components:**
- **Total cost**: Sum of `allowed_amount` (or `paid_amount`) for all claim lines
- **Total claims**: Count of claim line records

**Validation:**
- Total claims must be > 0
- Result must be non-negative
- Relative error tolerance: 1%

**Example:**
- Total cost: $12,000,000
- Total claims: 50,000
- Avg cost per claim: $12,000,000 / 50,000 = $240.00

---

### 4. Claims Per Member

**Formula:**
```
claims_per_member = Total claims / Unique members
```

**Components:**
- **Total claims**: Count of claim line records
- **Unique members**: Count of distinct `member_id` values

**Validation:**
- Unique members must be > 0
- Result must be non-negative
- Relative error tolerance: 1%

**Example:**
- Total claims: 50,000
- Unique members: 10,000
- Claims per member: 50,000 / 10,000 = 5.0

---

## Provider Archetype Metrics

### Provider Archetype Characteristics

Provider archetypes are created using **K-means clustering** on the following features:

1. **total_claims**: Total number of claim lines per provider
2. **total_cost**: Total allowed/paid amount per provider
3. **avg_cost_per_claim**: Average cost per claim line for the provider
4. **claims_per_member**: Average claims per unique member for the provider

**Clustering Process:**
1. Extract provider-level features from claims data
2. Standardize features using `StandardScaler` (mean=0, std=1)
3. Apply K-means clustering (default: 5 clusters, random_state=42)
4. Calculate cluster centroids and characteristics

**Archetype Characteristics Calculation:**
```
For each archetype:
  - provider_count = Number of providers in cluster
  - total_claims = MEAN of total_claims across providers in cluster
    * Note: This is the AVERAGE claim lines per provider, not a total sum
    * Each provider's total_claims = count of claim lines for that provider
    * Then: mean(total_claims for each provider in cluster)
  - total_cost = MEAN of total_cost across providers in cluster
    * Note: This is the AVERAGE total cost per provider, not a total sum
    * Each provider's total_cost = sum of allowed_amount for their claim lines
    * Then: mean(total_cost for each provider in cluster)
  - avg_cost_per_claim = MEAN of avg_cost_per_claim across providers in cluster
    * Each provider's avg_cost_per_claim = total_cost / total_claims
    * Then: mean(avg_cost_per_claim for each provider in cluster)
  - claims_per_member = MEAN of claims_per_member across providers in cluster
    * Each provider's claims_per_member = total_claims / unique_members
    * Then: mean(claims_per_member for each provider in cluster)
```

**Important:** The "total_claims" and "total_cost" values in archetype characteristics are **averages per provider**, not aggregate totals. This is because we're characterizing the typical provider in the archetype, not summing across all providers.

**Validation:**
- All characteristics must be non-negative
- Provider count must match actual providers in cluster
- Average values must match manual calculation within 1% tolerance

---

## Patient Segment Metrics

### Patient Risk Stratification

Patients are stratified into risk bands based on total cost:

- **HIGH Risk**: Total cost > $10,000
- **MEDIUM Risk**: Total cost $2,000 - $10,000
- **LOW Risk**: Total cost < $2,000

**Segment Characteristics:**
```
For each segment:
  - member_count = Number of members in risk band
  - avg_claims_per_member = Mean of total_claims across members in segment
  - avg_cost_per_member = Mean of total_cost across members in segment
  - avg_cost_per_claim = Mean of avg_cost_per_claim across members in segment
```

---

## Provider Concentration Metrics

### Herfindahl-Hirschman Index (HHI)

**Formula:**
```
HHI = Sum of (provider_share^2) × 10,000
```

**Components:**
- **provider_share**: Market share of each provider (0-1)
  - Calculated as: Provider's claim count / Total claim count

**Interpretation:**
- HHI < 1,500: Competitive market
- HHI 1,500 - 2,500: Moderately concentrated
- HHI > 2,500: Highly concentrated

**Example:**
- Provider A: 40% share → 0.4² = 0.16
- Provider B: 30% share → 0.3² = 0.09
- Provider C: 30% share → 0.3² = 0.09
- HHI = (0.16 + 0.09 + 0.09) × 10,000 = 3,400 (highly concentrated)

---

### Top 10 Provider Share

**Formula:**
```
top_10_provider_share = Sum of top 10 provider shares × 100
```

**Components:**
- Provider shares sorted in descending order
- Sum of top 10 shares converted to percentage

---

## Site-of-Care Mix

### Site-of-Care Percentage

**Formula:**
```
site_of_care_{pos}_percentage = (Claims at POS / Total claims) × 100
```

**Components:**
- **POS**: Place of Service code (e.g., 11=Office, 21=Inpatient, 22=Outpatient)
- **Claims at POS**: Count of claim lines with specific POS code
- **Total claims**: Total count of claim lines

**Validation:**
- Sum of all site-of-care percentages should equal 100% (within 0.1% tolerance)
- Each percentage must be between 0% and 100%

---

## Time Series Analysis

### Trend Calculation

**Formula:**
```
trend_pct = ((Last value - First value) / First value) × 100
```

**Components:**
- **First value**: First data point in time series
- **Last value**: Last data point in time series

**Validation:**
- First value must be > 0 for percentage calculation
- Trend direction: positive = increasing, negative = decreasing

---

## Validation Standards

All calculations are validated using the following standards:

1. **Input Validation:**
   - Denominators must be > 0
   - All numeric inputs must be finite (not NaN or Inf)

2. **Output Validation:**
   - Results must be non-negative (unless explicitly a change metric)
   - Relative error tolerance: 1% (0.01)
   - Absolute error tolerance: $0.01 for currency, 0.01 for rates

3. **Cross-Validation:**
   - Derived metrics must match component calculations
   - Sums must match individual components
   - Percentages must sum to 100% (within tolerance)

4. **Documentation:**
   - All formulas documented with examples
   - Calculation methodology traceable to source data
   - Validation results stored with calculations

---

## Data Quality Requirements

### Minimum Data Requirements

- **Claims Data:**
  - Must have: `member_id`, `provider_id` (or `rendering_npi`), date column, amount column
  - Date column: `service_date`, `service_date_from`, or similar
  - Amount column: `allowed_amount` (preferred) or `paid_amount`

- **Enrollment Data (optional but recommended):**
  - Must have: `member_id`, `coverage_start_date`, `coverage_end_date` (or `coverage_month`)
  - Used for accurate member-months calculation

### Data Quality Checks

1. **Completeness:**
   - Missing values in key columns flagged
   - Missing dates excluded from analysis
   - Missing amounts set to 0 (with warning)

2. **Consistency:**
   - Date ranges validated (start <= end)
   - Amounts validated (non-negative, reasonable ranges)
   - Member/provider IDs validated (non-null, non-empty)

3. **Reasonableness:**
   - Outlier detection (values > 3 standard deviations flagged)
   - Negative amounts flagged (unless explicitly allowed)
   - Future dates flagged

---

## Standard Formulas Reference

| Metric | Formula | Unit | Validation |
|--------|---------|------|------------|
| Utilization Rate | (Claims / Member-months) × 1,000 | per 1,000 MM | ±1% |
| Cost PMPM | Total cost / Member-months | $ PMPM | ±1% |
| Avg Cost Per Claim | Total cost / Total claims | $ | ±1% |
| Claims Per Member | Total claims / Unique members | ratio | ±1% |
| Provider Share | Provider claims / Total claims | % | Sum = 100% |
| HHI | Sum(share²) × 10,000 | index | ±1% |
| Site-of-Care % | (POS claims / Total claims) × 100 | % | Sum = 100% |

---

## Client Defensibility

All calculations are designed to be:

1. **Transparent:** Formulas clearly documented and traceable
2. **Standard:** Using industry-standard healthcare analytics formulas
3. **Validated:** Automated validation ensures accuracy
4. **Auditable:** All calculations include source data references
5. **Reproducible:** Same inputs always produce same outputs

Clients can:
- Review calculation methodology
- Validate formulas independently
- Request source data for any metric
- Verify calculations using provided formulas

---

## Implementation Notes

- All calculations use **double precision** floating point arithmetic
- Rounding applied only at final display (not intermediate calculations)
- Currency values stored and calculated in dollars (not cents)
- Percentages stored as decimals (0-1) internally, displayed as percentages (0-100%)
- Dates handled as ISO 8601 format (YYYY-MM-DD)
- Time zones: All dates assumed to be in UTC or local timezone (documented per analysis)

