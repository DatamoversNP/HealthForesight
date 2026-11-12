# HealthForesight — measures, KPIs, and formulas

Review document. Every measure the platform defines or calculates is listed with the formula that the code actually uses, the inputs, a worked example, and where a second code path uses a different formula for the same name.

Illustrative numbers are invented so the arithmetic can be checked by hand. They are not staging results.

Source of the intended definitions: `packages/common/src/uepi_common/metrics/metric_dictionary.py`.
Source of the calculations: the modules named under each measure.

## How to review a row

| Question | What to mark |
|---|---|
| Is the formula the right healthcare definition? | Accept or replace the formula |
| Do two code paths use the same formula for the same name? | If not, pick one |
| Is the denominator enrolled member-months, or distinct people who had a claim? | Several paths use claimants and still label the result per 1,000 member-months |
| Is a default coefficient being used as if it were estimated? | Elasticity, friction, provider mix, and several scores are tables, not fits |
| Does the measure match the policy mechanism? | A utilization rate does not measure prior authorization, MPPR, or NCCI |

Shared change formulas, used in more than one module:

```
absolute_change = observed − baseline
percent_change  = (observed − baseline) / baseline × 100
```

Both inputs must already be the same kind of rate, over the same length of time, on the same population. An annual count minus a monthly count is not this formula.

---

## 1. Denominators

### 1.1 member_months — dictionary

Formula: sum, over members, of months enrolled in the period.
Unit: member-months. Source: enrollment.
Example: 100 members enrolled all 12 months of 2025 = 1,200 member-months.

Implemented denominator, database baseline (`database_baseline_computation.py`):

```
unique_members = distinct member_id on claims in the window
months         = inclusive calendar months from window start to window end
member_months  = unique_members × months
```

Example: 100 people with at least one claim, 12-month window = 1,200. A person with no claim is missing. A person with one claim is treated as enrolled for every month in the window.

Baseline analysis when enrollment is absent (`analytics/baseline.py`, `_calculate_per_1k`):

```
member_months = distinct member_id × 12
```

The 12 is fixed. It does not follow the length of the data window.

`_calculate_pmpm` in the same file does merge claims to enrollment when an enrollment table is passed. That is the only path that uses real enrolled months.

### 1.2 unique_members — dictionary

Formula: distinct member_id with at least one eligible enrollment day in the period.
Implemented: distinct member_id on the claims that passed the filter. Not an enrollment count.

### 1.3 policy_eligible_member_months — dictionary

Formula: member_months after line of business, market, plan, and network filters.
Implemented policy baseline: the same claimant × calendar-months product, after claim filters (codes, and line of business or market when those filters are applied). It is not an eligibility count.

### 1.4 claims_per_member

```
claims_per_member = total_claims / unique_members
```

Example: 240 claims, 100 claimants = 2.4 claims per claimant. Not per enrolled member.

### 1.5 cost_per_claim

```
cost_per_claim = total_paid / total_claims
```

Database baseline. Example: paid $90,000, 240 claims = $375 per claim.

Impact engine name `avg_cost_per_claim` is the mean of `allowed_amount`, not paid:

```
avg_cost_per_claim = mean(allowed_amount)
```

---

## 2. Utilization and cost

### 2.1 util_rate_total_per_1000_mm

Dictionary:

```
(total_claim_lines / member_months) × 1000
```

Unit: claim lines per 1,000 member-months.
Example: 240 lines, 1,200 member-months. Rate = 240 / 1,200 × 1,000 = 200.

Database general baseline uses the claimant denominator from section 1.1 and stores this name. Alias also stored: `utilization_per_1k` on some paths.

Impact engine (`analytics/impact.py`), metric `utilization_per_1k`:

```
(claim_lines / distinct member_id) × 1000
```

No division by months. A 6-month window and a 12-month window are not on the same scale.
Example: 120 lines, 100 members, any window length. Rate = 1,200.

Staging observation writer (`scripts/lean_staging_full_demo_lifecycle.py`):

```
baseline: (matching lines / distinct claimants) × (1000 / 12)
month:    (matching lines / distinct claimants that month) × 1000
```

These two are not comparable to each other or to the dictionary formula. See section 12.

### 2.2 util_rate_target_per_1000_mm

Dictionary:

```
(target_claim_lines / policy_eligible_member_months) × 1000
```

Target lines are claims whose codes, and any other scope filters, match the policy.
Database policy baseline uses this name with the claimant × months denominator.
Alias in the dictionary and on observations: `utilization_per_1k`.

Example, dictionary form: 120 targeted lines, 1,000 eligible member-months. Rate = 120.
A later month: 90 lines, same 1,000 member-months. Rate = 90.
Change = (90 − 120) / 120 × 100 = −25%.

### 2.3 allowed_pmpm_total and allowed_pmpm_target

Dictionary:

```
allowed_pmpm_total  = total_allowed_amount / member_months
allowed_pmpm_target = target_allowed_amount / policy_eligible_member_months
```

Unit: dollars per member per month.
Example: allowed $120,000, 1,200 member-months. PMPM = $100.

Database baseline stores `allowed_pmpm_total` (general) and `allowed_pmpm_target` (policy) using claimant × months.

Impact engine `cost_per_member`:

```
sum(allowed_amount) / distinct member_id
```

This is cost per claimant over the whole window, not per month.
Example: allowed $120,000, 100 members. Result = $1,200, regardless of whether the window is 1 month or 12.

Observation alias `cost_pmpm` is mapped to `allowed_pmpm_target` in `unified_measures.py`. The staging writer fills `cost_pmpm` with allowed dollars per claimant (per month in the observation, per year divided by 12 in the baseline).

### 2.4 paid_pmpm_total and paid_pmpm_target

```
paid_pmpm = total_paid_amount / member_months
```

Database general baseline stores `paid_pmpm_total` and also copies it to `cost_pmpm` in `compute_metrics_from_database_claims` (`database_claims_loader.py`). That loader’s `cost_pmpm` is paid, while the policy baseline’s `cost_pmpm` field name is not used; the policy function stores paid as `paid_pmpm_target`.

Review point: the name `cost_pmpm` means paid in the claims loader and allowed in the observation alias map.

Example: paid $90,000, 1,200 member-months. Paid PMPM = $75.

### 2.5 total_cost_per_1k

Baseline analysis, legacy:

```
(sum of paid_amount / member_months) × 1000
```

Example: paid $90,000, 1,200 member-months. Cost per 1,000 member-months = $75,000.
This is not PMPM. PMPM would be $75.

### 2.6 member_cost_share_pmpm — dictionary only

```
sum(member_cost_share) / member_months
```

Example: cost share $12,000, 1,200 member-months = $10 PMPM.
The field exists on claim lines. No observation or baseline writer stores this rate.

### 2.7 allowed_total_annualized — dictionary

```
(total_allowed_amount / months_in_period) × 12
```

`baseline_metrics_computation.py` uses a different expansion when both PMPM and member-months exist:

```
(allowed_pmpm × member_months / months_in_period) × 12
```

If `allowed_pmpm` is already per month, then `allowed_pmpm × member_months` is the period total, and dividing by `months_in_period` again understates a multi-month window.

Example of the dictionary formula: $50,000 allowed in January. Annualized = $600,000. That is an extrapolation, not a year of experience. Months outside the observation window must not be included.

---

## 3. Mix and concentration

### 3.1 Site-of-care share

Dictionary, one measure per site (ER, HOPD, ASC):

```
site_share = lines with that site / all targeted lines
```

Baseline analysis stores a percentage:

```
site_of_care_{pos}_percentage = (count at that place_of_service / all lines) × 100
```

Example: 40 HOPD lines and 60 other lines. HOPD share = 40%.

### 3.2 soc_share_delta_target — dictionary

```
post_site_share − baseline_site_share
```

Unit: percentage points.
Example: baseline HOPD 70%, observed 40%. Delta = −30 percentage points.
Not calculated as its own stored metric. Site share itself is only on the baseline-analysis path.

### 3.3 service mix

```
service_{category}_percentage = (lines in that service category / all lines) × 100
```

Example: imaging is 30 of 100 lines = 30%.

Dictionary `service_share_target` is the same idea restricted to the policy code set.

### 3.4 inn_share_target — dictionary

```
in-network targeted lines / all targeted lines
```

Network analysis (`baseline.py`, steerage):

```
in_network_percentage     = in-network lines / all lines × 100
out_of_network_percentage = 100 − in_network_percentage
```

Example: 80 of 100 lines in network = 80% in network, 20% out of network.

### 3.5 oon_leakage_rate_target_per_1000_mm — dictionary only

```
(out-of-network targeted lines / policy_eligible_member_months) × 1000
```

Example: 20 out-of-network lines, 1,000 member-months. Rate = 20.
Not implemented. The percentage in section 3.4 is a different measure.

### 3.6 top10_provider_share_target — dictionary only

```
lines from the 10 providers with the most targeted lines / all targeted lines
```

Example: those ten providers have 450 of 1,000 lines = 45%.
Not implemented.

### 3.7 provider_hhi_target

Dictionary: sum of squared provider shares, scale 0 to 1.
Implemented market concentration (`baseline.py`) uses the 0-to-10,000 scale:

```
provider_share_i = provider allowed / total allowed
HHI = Σ (provider_share_i²) × 10,000
```

Example: two providers, 50% of allowed each.
Dictionary HHI = 0.25 + 0.25 = 0.50.
Implemented HHI = 5,000.

Review point: the same name would not match across these two definitions. The implemented function does not use the dictionary name.

### 3.8 System affiliation

```
affiliated_share = allowed dollars at system-affiliated providers / total allowed
```

Computed only when a provider table with affiliation is supplied.

---

## 4. Time series and baseline trend

`SeasonalityAdjuster._simple_trend` (`analytics/baseline.py`). Used when STL is unavailable.

```
trend     = rolling mean of the value, window = min(12, half the series length)
seasonal  = (mean of that calendar month) − (mean of the whole series)
residual  = value − trend − seasonal
lower     = trend + seasonal − 2 × standard deviation of residual
upper     = trend + seasonal + 2 × standard deviation of residual
```

Example: January mean is $20 above the series mean. Seasonal for January = +20. A trend of 100 gives a fitted January of 120. If residual standard deviation is 5, the band is 110 to 130.

Pre-window length in the impact and method-check engines is `pre_months × 30` days, not calendar months. February and 31-day months are not exact.

---

## 5. Policy impact

`ImpactAnalysisEngine.analyze_policy_impact`.

Pre/post, no control:

```
change         = post_metric − pre_metric
percent_change = change / pre_metric × 100    if pre_metric > 0, else 0
```

Difference in differences, with a control group:

```
treatment_diff = treatment_post − treatment_pre
control_diff   = control_post − control_pre
DiD            = treatment_diff − control_diff
percent_change = DiD / treatment_pre × 100    if treatment_pre > 0, else 0
```

Example: treatment 100 before and 80 after. Control 100 before and 95 after.
Treatment change = −20. Control change = −5. DiD = −15.
Percent = −15 / 100 × 100 = −15%.

The metric inside this formula is whichever of section 2 the caller requested. If that metric is the impact-engine utilization rate, the DiD is on claims per 1,000 claimants, not per 1,000 member-months.

Confidence interval: percentile bootstrap of the same change, default confidence level applied as

```
lower = percentile(bootstrap, (1 − confidence) / 2)
upper = percentile(bootstrap, 1 − (1 − confidence) / 2)
```

P-value is not a test. If the interval contains 0, the code returns 0.50. If it does not, the code returns 0.01.

---

## 6. Method checks

`analytics/method_checks.py`.

Parallel trends. Monthly utilization slope in the pre window, treatment versus control:

```
slope = ordinary least-squares slope of the monthly series
slope_difference = |treatment_slope − control_slope|
PASS if slope_difference < 0.1
WARN if slope_difference < 0.3
FAIL otherwise
```

Sample size:

```
pass if pre-period treatment rows ≥ 1,000
```

The row count is claim lines, not members.

Control balance. The covariate list is age band, gender, and risk score, but the standardized difference is not computed from data. Balance score is 1.0 if the imbalance list is empty, else 0.7. The list is initialized empty, so the check passes without reading covariates.

Seasonality. The code comments call this a coefficient of variation. The arithmetic is variance divided by the mean, not standard deviation divided by the mean:

```
cv = variance(monthly counts) / mean(monthly counts)
LOW    if cv < 0.1
MEDIUM if cv < 0.2
HIGH   otherwise
```

Needs 12 months. Adjustment is recommended at MEDIUM or HIGH.

---

## 7. Prediction

`PredictedImpactGenerator` (`analytics/predicted_impact.py`).

### 7.1 Friction

One lever sets a base friction. The policy friction is the maximum across levers, capped at 1.

| Lever | Base friction |
|---|---:|
| Prior authorization | 0.60 |
| Clinical criteria | 0.50 |
| Cost sharing | 0.50 |
| Site of care | 0.40 |
| Network restriction | 0.40 |
| Quantity limit | 0.30 |
| Duration or frequency limit | 0.30 |
| Referral | 0.30 |
| Anything else | 0.30 |

Hard enforcement multiplies by 1.2. Soft enforcement multiplies by 0.8. Cap 1.0.
Example: prior authorization, hard. Friction = min(1, 0.60 × 1.2) = 0.72.

### 7.2 Elasticity coefficient

Not fit from data in the current code. The comment in `elasticity.py` describes a regression of utilization change on friction. The function returns a table.

| Category | Coefficient |
|---|---:|
| Imaging | −0.35 |
| Physical therapy | −0.40 |
| Therapy services | −0.35 |
| Specialty care | −0.30 |
| Facility care | −0.25 |
| Laboratory | −0.25 |
| Urgent care | −0.25 |
| General, other, or missing | −0.30 |

`elasticity.py` also builds a line through the origin:

```
elasticity_at_friction = coefficient × friction
```

at friction 0, 0.25, 0.50, 0.75, and 1.0. Threshold friction is fixed at 0.5. It is not estimated.

Confidence of that curve: 70 if at least 5 historical analyses exist, 50 if at least 2, else 30. The coefficient itself does not change with those analyses.

### 7.3 Predicted utilization and cost

```
utilization_change_pct = friction × elasticity × 100
cost_change_pct        = utilization_change_pct × 0.9
utilization_change_per_1k = baseline_utilization × (utilization_change_pct / 100)
cost_change_pmpm          = baseline_cost_pmpm × (cost_change_pct / 100)
cost_change_total         = cost_change_pmpm × member_count × 12
```

If baseline metrics are missing, baseline utilization defaults to 100 and baseline cost PMPM defaults to 500.

Example: friction 0.72, elasticity −0.35, baseline utilization 200 per 1,000, baseline cost $80 PMPM, 1,000 members.
Utilization change = 0.72 × −0.35 × 100 = −25.2%.
Cost change = −25.2 × 0.9 = −22.68%.
Utilization level change = 200 × −0.252 = −50.4 per 1,000.
Cost level change = 80 × −0.2268 = −$18.14 PMPM.
Annual cost change = −18.14 × 1,000 × 12 = −$217,680.

The 0.9 factor is a fixed assumption (“selection”), not an estimated cost elasticity.

### 7.4 Predicted substitution, provider mix, and patient response

Substitution rate = category base rate × friction.

| Targeted category | Substitutes named | Base rate |
|---|---|---:|
| Imaging | Urgent care, office visit | 0.15 |
| Physical therapy | Home health, self care | 0.20 |
| Specialty care | Primary care, urgent care | 0.25 |
| Anything else | none named | 0.10 |

Confidence on each substitution row is fixed at 70.

Provider mix by friction band. Figures are percentages and sum to 100.

| Friction | Compliant | Adaptive | Resistant | Circumvention |
|---|---:|---:|---:|---:|
| under 0.30 | 70 | 20 | 8 | 2 |
| 0.30 to under 0.60 | 50 | 30 | 15 | 5 |
| 0.60 or more | 35 | 30 | 25 | 10 |

Confidence fixed at 75.

Patient response:

```
defer_rate        = 0.10 × friction
substitute_rate   = 0.15 × friction
er_fallback_rate  = 0.05 × friction
```

Example at friction 0.72: defer 7.2%, substitute 10.8%, emergency fallback 3.6%. Confidence fixed at 70.

### 7.5 Prediction confidence score

Starts at 100.

| Condition | Subtract |
|---|---:|
| No elasticity data, or model quality POOR | 30 |
| Model quality FAIR | 15 |
| No baseline metrics | 20 |
| More than 3 levers | 10 |

Floor 0, cap 100.
Example: default elasticity (POOR) and a baseline present, 2 levers. Score = 70.

---

## 8. Observation and verdict

### 8.1 Comparison

`observation_enhancement.py`:

```
utilization_change_pct = (observed_utilization − baseline_utilization) / baseline_utilization × 100
cost_change_pct        = (observed_cost − baseline_cost) / baseline_cost × 100
```

Narrative bands, which do not set the verdict:

| Utilization change | Text band |
|---|---|
| under −20% | strong reduction |
| −20% to under −10% | moderate reduction |
| −10% to under −5% | mild reduction |
| over +5% | increase |
| Cost under −10% | significant savings |
| Cost −10% to under −5% | moderate savings |
| Cost over +5% | cost increase |

### 8.2 Verdict — product rule `v1.0`

`uepi_api/verdict.py`. Uses percent change versus baseline when both utilization and cost percents exist.

```
ON_TRACK  if utilization_change_pct ≤ 0 and cost_change_pct ≤ 0
AT_RISK   if utilization_change_pct > 5 or cost_change_pct > 10
BACKFIRE  only if that AT_RISK condition is true and behavioral risk text is also present
```

If those percents are missing, prediction-error percents are used:

```
AT_RISK if |utilization error| > 20 or |cost error| > 25
ON_TRACK if any comparison number exists and the rules above did not fire
INCONCLUSIVE if there is no comparison
```

A reduction, or a flat result, is ON_TRACK even when the policy’s objective was not a reduction. There is no policy-specific expected effect in this function.

### 8.3 Staging observation status — a different rule

Not `compute_verdict`. Written by the staging lifecycle script:

```
predicted_utilization = baseline_utilization × 0.95
predicted_cost        = baseline_cost × 0.97
ON_TRACK  if month utilization ≤ predicted_utilization × 1.05
BACKFIRE  if month utilization > baseline_utilization × 1.10
AT_RISK   otherwise
```

Cost is stored and is not an input. The −5% and −3% are constants.

### 8.4 Prediction error — dictionary

```
prediction_error_util_pp   = observed_utilization_change_pct − predicted_utilization_change_pct
prediction_error_cost_pmpm = observed_cost_change_pmpm − predicted_cost_change_pmpm
```

Example: predicted −8%, observed −10%. Utilization error = −2 percentage points.
The staging rows store a difference of the two rate levels, not this percentage-point error.

---

## 9. Forecast

`forecast_service.py`. Needs at least two observations.

```
slope = (last_value − first_value) / (n − 1)
trend_projection at month m = last_value + slope × m
trend_weight      = max(0, 1 − m / horizon)
prediction_weight = 1 − trend_weight
forecast_m        = trend_projection × trend_weight + predicted_value × prediction_weight
```

Example: values 100 then 90, horizon 6, predicted target 80.
Slope = (90 − 100) / 1 = −10.
Month 1 trend = 80. Trend weight = 5/6. Forecast = 80 × 5/6 + 80 × 1/6 = 80.

Convergence:

```
months_to_converge = |predicted − latest| / |slope|
convergence_rate   = |predicted − latest| / horizon
```

Direction is toward the prediction only when the slope points at the predicted value.

Six-month accuracy versus the prediction, not versus a later actual:

```
error_pct = |forecast_at_6 − predicted| / |predicted| × 100
accuracy  = max(0, 100 − min(error_pct, 200))
```

A forecast that lands on the prediction scores 100 even if the next observation does not.

---

## 10. Substitution detection

`analytics/substitution.py`. Pre and post windows are `months × 30` days.

Per CPT code:

```
allowed_delta       = post_allowed − pre_allowed
claim_count_delta   = post_claims − pre_claims
allowed_pct_change  = allowed_delta / pre_allowed × 100
avg_allowed_per_claim = total_allowed / claim_count
```

A code is kept only when allowed dollars increased and post claim count is at least 10.

Classification:

- SITE_OF_CARE_SHIFT if the modal place of service changed.
- SERVICE_SUBSTITUTION if the code shares a code group with a policy-affected code.
- UNKNOWN otherwise.

Chi-square, when SciPy is present, on the 2×2 table of (this code versus all other lines) by (pre versus post). The p-value is that test. It does not adjust for member-months or multiple codes.

Lag windows default to 30, 60, and 90 days. Each window is the next 30 days after that lag, and the result is a claim count and an allowed sum, not a rate.

Confidence starts at 50.

| Add | When |
|---:|---|
| 25 | site-of-care shift |
| 20 | service substitution |
| 20 / 10 / 5 | allowed change over 100% / 50% / 25% |
| 15 / 10 / 5 | p-value under 0.001 / 0.01 / 0.05 |
| 5 | every lag window has a positive count |

Cap 100. Top 20 codes are returned.

---

## 11. Providers and patients

### 11.1 Provider features

Per provider, pre versus post:

```
allowed_delta          = post_allowed − pre_allowed
claim_count_delta      = post_claims − pre_claims
avg_allowed_pct_change = (post_mean_allowed − pre_mean_allowed) / pre_mean_allowed × 100
pos_shift              = 1 if the modal place of service changed, else 0
member_count_delta     = post_members − pre_members
```

Archetype label, in this order:

| Label | Rule |
|---|---|
| COMPLIERS | allowed delta under −1,000 and claim delta under −5 |
| CIRCUMVENTERS | allowed delta over 1,000 and site-shift rate over 0.5 |
| SUBSTITUTORS | allowed delta over 500 and percent change over 50 |
| REDUCERS | allowed delta under −100 and claim delta negative |
| INCREASERS | allowed delta over 100 |
| NEUTRAL | otherwise |

Cluster stability:

```
stability = 1 / (1 + average feature variance / 1000)
```

capped to 0–1. Provider confidence starts at 50 and adds points for large allowed or claim deltas (see `_compute_provider_confidence`).

K-means uses a fixed random seed of 42. Silhouette under 0.25 is POOR, under 0.50 is FAIR, else GOOD.

Dictionary measures not computed by this clustering:

```
provider_archetype_share = providers in a class / providers in scope
provider_ordering_intensity = (targeted lines for the provider / attributed member-months) × 1000
```

Observation enhancement approximates ordering intensity as targeted claims / an approximate member-month figure × 1,000. That approximation is not the dictionary denominator.

### 11.2 Patient segments

Patients are split into LOW, MEDIUM, and HIGH cost bands by percentiles of their total cost, so the three bands are balanced by count. This is not a clinical risk score.

Dictionary `patient_response_share` (member-months showing a response / member-months in the segment) is not computed from claims. The predicted patient rates in section 7.4 are the friction table.

### 11.3 Deferral index — dictionary only

```
post_30_day_targeted_rate / baseline_30_day_targeted_rate
```

Example: baseline 40, post 20. Index = 0.5.
Not implemented. Service-date timing is not scored.

### 11.4 substitution_uplift_per_1000_mm — dictionary only

```
observed substitute rate − rate expected from the baseline trend
```

Not implemented. Detected substitution in section 10 is a dollar and count increase, not this uplift.

---

## 12. Trust panel

`analytics/trust_panel.py`.

| Component | Value |
|---|---|
| Method | 90 if difference-in-differences, else 70 |
| Data quality | fixed 85 |
| Sample size | min(100, claim rows / 1,000 × 100) |
| Control group | 100 if no balance object; 90 if balanced; 60 if not; 0 for pre/post |
| Methodology | fixed 85 |

```
overall = 0.30×method + 0.20×data quality + 0.20×sample size
        + 0.15×control + 0.15×methodology
```

Data sufficiency coverage:

```
coverage_score = min(1, data_window_months / 12)
sufficient     = sample_size_ok and data_window_months ≥ 6
```

The interval-contains-zero flag is recorded. It does not change the score.

---

## 13. Scorecard

`storage_scorecards.py`, from a predicted-impact record.

```
cost_savings_pct = |cost_change_pct| if cost_change_pct is negative, else 0
cost_impact_score = min(100, max(0, 50 + cost_savings_pct × 2))

defer_rate = |utilization_change_pct| × 0.1   if utilization change is negative, else 0
behavioral_risk_score = min(100, max(0, 100 − defer_rate × 200))

access_impact_score = 80
regulatory_defensibility_score = min(100, confidence_score + 20)

effectiveness_index =
    0.30×cost_impact_score
  + 0.25×behavioral_risk_score
  + 0.25×access_impact_score
  + 0.20×regulatory_defensibility_score
```

Example: predicted cost change −10%, utilization change −20%, confidence 70.
Savings percent = 10. Cost score = 50 + 20 = 70.
Defer rate = 20 × 0.1 = 2. The code multiplies a percent by 0.1 and then treats the result as a rate in the next line (`× 200`). Behavioral score = 100 − 400, floored at 0.
Regulatory score = 90.
Access score = 80.
Index = 0.30×70 + 0.25×0 + 0.25×80 + 0.20×90 = 21 + 0 + 20 + 18 = 59.

Review point: `defer_rate` here is not the patient defer rate from section 7.4. Access is a constant 80.

---

## 14. What-if and payment rules

### 14.1 Multiple procedure payment reduction

`reimbursement_mppr.py`. Within one claim id, rank lines by allowed amount descending. Tie-break on claim line id.

```
rank 1 paid        = allowed
rank 2 and later   = allowed × secondary_pct
default secondary_pct = 0.50
payment_impact     = baseline_paid − post_policy_paid
payer_savings      = payment_impact
provider_payment_change = −payment_impact
```

Example: one claim, allowed $1,000 and $600, secondary percent 50%.
Primary paid = $1,000. Secondary paid = $300. Post paid = $1,300.
If baseline paid both in full ($1,600), payment impact = $300.

What-if compares two secondary percents on a fixed demo line set, not on the tenant’s claims. Utilization change is explicitly null. The result is marked synthetic.

### 14.2 Site-of-service payment differential

`reimbursement_sos.py`. Volume is held constant. Pre-policy paid equals allowed at every site.

```
hospital outpatient (place of service 22 or 19): post paid = allowed × hospital_pct
default hospital_pct = 0.80
every other site: post paid = allowed
payment_impact = baseline_paid − post_paid
payment_impact_pct = payment_impact / baseline_paid × 100
price_effect = payment_impact
volume_effect = 0
mix_effect = 0
```

Example: one hospital line allowed $1,000. Post paid = $800. Payer impact = $200.

### 14.3 Infusion site of care

`expansion_demo_scenarios.apply_infusion_soc`. Runs on a fixed demo line list, not tenant claims.

The first `steer_hopd_count` hospital lines (default 2) are repriced to the office allowed amount (default $3,200). Other lines keep their allowed amount.

```
payment_impact = sum(allowed) − sum(post paid)
```

Known answer: three hospital lines at $5,000 and one office line at $3,200. Two hospital lines move to $3,200. Baseline $18,200. Post $14,600. Impact $3,600.

### 14.4 NCCI procedure-to-procedure

`apply_ncci_ptp`. A claim is a pair when it has a line tagged `column_one` and a line tagged `column_two`.

```
indicator 0: column-two paid = 0
indicator 1: column-two paid = 0 unless modifier is 59, XE, XP, XS, or XU
indicator 1 with one of those modifiers: both lines paid = allowed
column-one paid = allowed
payment_impact = baseline_paid − post_paid
```

Known answer on the demo lines: baseline $4,400, post $3,600, impact $800, 3 pairs, 1 modifier bypass.

### 14.5 NCCI medically unlikely units

`apply_ncci_mue`. Default limit is 4 units. This is a demo value, not a CMS MUE table.

```
paid units = min(billed units, mue_value)
baseline paid = billed units × allowed per unit
post paid = paid units × allowed per unit
payment_impact = baseline − post
```

Example: 6 units at $50, limit 4. Baseline $300. Post $200. Impact $100.

### 14.6 Therapy coverage units

`apply_therapy_coverage`.

```
paid units = min(billed units, medically_necessary_units)
paid = paid units × allowed per unit
payment_impact = baseline − post
```

Known answer: baseline $420, post $340, impact $80.

### 14.7 Mechanisms that still have no formula

These do not have an engine. When they are scored, they use utilization and cost from sections 2 and 7, or the what-if dispatcher rejects them.

Measures those mechanisms need, which this platform does not calculate from claims today:

| Mechanism | Formula that would be required | Input that is absent |
|---|---|---|
| Prior authorization | approvals / decisions | authorization decisions |
| Coverage or clinical criteria | services meeting the criteria / services in scope | diagnosis and the criteria |
| Site of care | site share among eligible services, section 3.1 | stored as a baseline mix only, not as the policy result |
| NCCI pair | column-2 lines paired with column-1 / column-1 lines | the edit table and modifiers |
| NCCI units | max(0, units on the date − MUE value) | the MUE table |
| Pharmacy step | first fills with the required prior product / first fills | NDC history |
| Quantity limit | max(0, quantity in the window − limit) | the limit value tied to the member |
| Frequency limit | max(0, services in the lookback − allowed visits) | the limit and the member history |
| Benefit and cost share | member cost share / eligible member-months | enrollment |
| Network | in-network share, section 3.4 | calculated only in the network-feature helper |
| Access | members meeting the standard / members in scope | appointment or adequacy events |
| Care management | participants, and the stated outcome rate | program enrollment |
| Referral | scoped services with a referral / scoped services | referral records |
| Provider eligibility | scoped services by an eligible provider / scoped services | credential flag |
| Coding edit | lines failing the edit / lines subject to the edit | the edit table |

---

## 15. Data quality

`ingestion/data_quality.py`.

```
completeness = 1 − (missing cells / all cells)
validity     = valid rows / all rows
uniqueness   = unique rows / all rows
quality = 0.30×completeness + 0.40×validity + 0.20×uniqueness
        + 0.10×(1 − min(error_count / total_rows, 1))
```

Scores are 0 to 1, not 0 to 100. The last term is an error-rate penalty, not a separate schema score.

Example: completeness 0.90, validity 0.80, uniqueness 1.00, schema pass.
Quality = 0.27 + 0.32 + 0.20 + 0.10 = 0.89.

---

## 16. Policy similarity

`policy/policy_similarity.py`. Two policies are reported when the score is at least 0.85.

```
similarity = 0.2×name + 0.3×scope + 0.4×levers + 0.1×date overlap
name       = |shared words| / |all words|          Jaccard on whitespace tokens
scope      = average of Jaccard on line of business, markets, and exact network id
```

Lever similarity and date overlap are the remaining two terms in that file (lever-type overlap, and overlap of the effective intervals). Cap 1.

Example: identical scope and levers, no shared words, no date overlap.
Score = 0 + 0.3 + 0.4 + 0 = 0.70, which is below 0.85.

---

## 17. Baseline shift and refresh

`baseline_refresh.py`.

```
utilization_change_pct = (current_util − previous_util) / previous_util × 100
cost_change_pct        = (current_pmpm − previous_pmpm) / previous_pmpm × 100
shift_detected         = |utilization change| > 0.01 or |cost change| > 0.01
significant_shift      = |utilization change| > 5 or |cost change| > 5
refresh recommended    = baseline computed_at older than 90 days
```

Example: utilization 200 then 212. Change = 6%. Significant shift is true.

---

## 18. Staging writer, kept separate on purpose

The lean-staging lifecycle does not call the database baseline service, the impact engine, or `compute_verdict`. Its formulas are in section 2.1 and section 8.3. The independent recount of those formulas is in `docs/production/releases/corrections/observation_audit/`. Matching that recount does not make the rate a member-month utilization rate and does not make the difference a policy effect.

---

## 19. Names that are aliases, not extra measures

| Name in storage or UI | Canonical name |
|---|---|
| utilization_per_1k | util_rate_target_per_1000_mm in the dictionary; several engines compute a different ratio and store this name anyway |
| cost_per_member | allowed_pmpm_target in the dictionary; impact engine stores allowed per claimant |
| cost_pmpm | paid PMPM in the claims loader; allowed PMPM in the observation alias map |
| util_rate_per_1k | util_rate_total_per_1000_mm |

---

## 20. Learning, scenario accuracy, and rollout

These were not in the first draft of this document.

### 20.1 Prediction accuracy

`learning_loop.calculate_prediction_accuracy`, one predicted value against one observed value.

```
error = observed − predicted
error_pct = error / |predicted| × 100     if predicted is not 0
accuracy_pct = 100 − |error_pct|
mae = |error|
rmse = |error|                            for a single pair
within_range if |error_pct| < 20
```

Example: predicted −10, observed −8. Error = 2. Error percent = 20%. Accuracy = 80%. Not within range, because the test is strict less-than 20.

When several observations update elasticity (`update_elasticity_from_observations`), at least 3 observations are required:

```
ratio = observed / predicted          for each pair whose predicted value is not 0
avg_ratio = mean of those ratios
new utilization elasticity = −0.8 × avg_ratio
new cost elasticity = −0.75 × avg_ratio
mae = mean of |observed − predicted|
rmse = square root of mean of squared errors
confidence = min(0.95, 0.5 + observation_count / 20)
```

These −0.8 and −0.75 defaults are not the category table in section 7.2.

### 20.2 Scenario accuracy

`storage_scenario_accuracy.compute_scenario_accuracy`.

```
util_error = observed utilization change % − predicted utilization change %
util_accuracy = max(0, 100 − |util_error / predicted util % × 100|)
cost_accuracy uses the same form on allowed PMPM percent change
overall = 0.6×util_accuracy + 0.4×cost_accuracy
```

If the predicted percent is 0, accuracy is 100 when the observed percent is also 0, and 0 otherwise.

### 20.3 Rollout duplicate check

`policy_rollout_recommendations._jaccard`.

```
jaccard = |shared codes| / |all codes|
duplicate if jaccard ≥ 0.55 and policy types match and both code sets have at least 2 codes
```

Empty compared with empty returns 1. One empty set returns 0.

Archetype impact bands are fixed ranges, not calculated from claims. Examples: advanced imaging utilization −6% to −2.5% and cost −5% to −2%; infusion site of care utilization −4% to −1.5% and cost −8% to −3%. If a tenant elasticity model exists, that model replaces the band. The replacement does not have a second formula beyond section 20.1.

### 20.4 Narrative check, not a new measure

`calculation_validator.py` recomputes the dictionary utilization and PMPM formulas and accepts the stored number when the relative error is at most 1%. It does not define a different measure.

### 20.5 Readiness flags

`compute_policy_readiness` does not compute a rate. A policy is CONFIGURED when it has an id and a name, BASELINE_READY when a baseline exists, FORECAST_READY when a forecast exists, OBSERVATION_READY when an observation exists, and IMPACT_ASSESSABLE when an observation exists and a causal flag is set.

## 21. Review list

Items a reviewer can accept or replace without rereading the code.

1. Member-months are distinct claimants times the number of months, except when the baseline PMPM function is given an enrollment table.
2. Impact-engine utilization is per 1,000 claimants and is not divided by months. Database utilization is per 1,000 claimant-months. The dictionary asks for enrolled member-months. Three different quantities share the utilization name.
3. `cost_pmpm` is paid in one module and allowed in another.
4. Impact p-values are 0.50 or 0.01. They are not a statistical test.
5. Elasticity, friction, provider mix, patient response, and substitution rates are fixed tables.
6. Cost change percent is utilization change percent times 0.9.
7. Missing baseline metrics are replaced by utilization 100 and cost $500 PMPM.
8. Verdict treats any non-increase as ON_TRACK. It does not read a policy objective.
9. The staging status rule is a second verdict, with a hardcoded −5% utilization prediction.
10. Scorecard access is the constant 80. Scorecard defer rate is not the prediction defer rate.
11. Seasonality “coefficient of variation” divides variance by the mean.
12. Control-balance does not compute a standardized difference.
13. Trust-panel data quality and methodology scores are constants.
14. Substitution keeps only codes whose allowed dollars rose, and only the top 20.
15. HHI is on a 0–10,000 scale in code and a 0–1 scale in the dictionary.
16. MPPR is the only payment rule with an explicit line-ranking formula, and the what-if runs it on a fixed demo set.
17. NCCI procedure-to-procedure, NCCI unit caps, therapy unit caps, site-of-service percent of allowed, and infusion steerage each have a demo payment formula (sections 14.2–14.6). They run on fixed demo lines or on lines passed into the function. They do not estimate a causal effect.
18. Learning-loop elasticity (−0.8 and −0.75 times an observed-to-predicted ratio) is a different elasticity from the category table in section 7.2.
19. Authorization decisions, pharmacy step therapy, quantity and frequency limits against a member history, referral, access, and care-management enrollment still have no outcome formula.
