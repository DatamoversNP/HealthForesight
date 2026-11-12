# Measures, formulas, and examples

Two layers are listed on purpose.

1. The product dictionary in `packages/common/src/uepi_common/metrics/metric_dictionary.py`. These are the measures HealthForesight defines.
2. The formula that actually produced the 2,250 lean-staging observations. It is a narrower, different calculation.

Illustrative numbers in the dictionary section are invented so the arithmetic can be checked by hand. They are not staging results. The staging section uses one real staging policy and is labeled synthetic.

## How to read a result

| Label | Meaning |
|---|---|
| PASS | Independent recount matches the stored number under the formula named in that row |
| FAIL | Recount does not match, or the comparison is the wrong shape (annual rate versus monthly rate, wrong codes) |
| NOT_MEASURABLE | The required inputs are absent, so no rate should be published |
| INSUFFICIENT_EVIDENCE | A status was stored without a policy objective and a supported expected impact |
| NOT_SUPPORTED | Do not treat the number as evidence the policy worked |

## A. Denominators

### member_months

Formula: sum over members of months enrolled in the period.
Denominator: enrollment table.
Example: 100 members enrolled for all 12 months of 2025 = 1,200 member-months. 100 members enrolled for January only = 100 member-months.
Staging observations: not calculated. Enrollment rows = 0.

### unique_members

Formula: count of distinct member_id with at least one eligible day in the period.
Denominator: enrollment.
Example: 100 people enrolled at any point in 2025 = 100 unique members, even if member-months are 1,200.
Staging: the stored field `unique_members` is distinct claimants on matching claims, not enrolled members.

### policy_eligible_member_months

Formula: member-months remaining after the policy's line of business, market, plan, and network filters.
Denominator: enrollment, filtered.
Example: 1,200 commercial member-months, policy limited to commercial HMO = only the HMO subset.
Staging: not calculated. Line of business on the claim was not applied as an eligibility filter.

## B. Primary outcomes

### util_rate_total_per_1000_mm

Formula: (all claim lines in period / member_months) * 1000.
Unit: lines per 1,000 member-months.
Example: 240 lines, 1,200 member-months. Rate = 240 / 1200 * 1000 = 200.
Staging general baseline uses claimants instead of member-months. See section H.

### util_rate_target_per_1000_mm

Formula: (claim lines in the policy code and eligibility scope / policy_eligible_member_months) * 1000.
Alias stored on observations: `utilization_per_1k`.
Example: 120 targeted lines, 1,000 eligible member-months. Rate = 120.
A later month with 90 targeted lines and 1,000 eligible member-months. Rate = 90.
Change = (90 - 120) / 120 * 100 = -25%.
Staging: the alias is filled with (matching lines / distinct claimants) times 1000, and the baseline further divides by 12. Eligible member-months are not in the denominator. Published utilization on these rows is NOT_MEASURABLE.

### allowed_pmpm_total

Formula: sum of allowed_amount for all lines / member_months.
Example: allowed $120,000, 1,200 member-months. PMPM = 100.
Staging general baseline divides by claimants times 12, not by enrolled member-months.

### allowed_pmpm_target

Formula: sum of allowed_amount on scoped lines / policy_eligible_member_months.
Alias stored on observations: `cost_pmpm`.
Example: scoped allowed $60,000, 1,000 eligible member-months. PMPM = 60.
Staging: divides scoped allowed by distinct claimants (and by 12 on the baseline). NOT_MEASURABLE as PMPM.

### paid_pmpm_total

Formula: sum of paid_amount / member_months.
Example: paid $90,000, 1,200 member-months. PMPM = 75.
Staging observations do not persist paid PMPM. Paid amount is on the claim line and is unused by the observation.

### member_cost_share_pmpm

Formula: sum of member cost share / member_months.
Example: cost share $12,000, 1,200 member-months. PMPM = 10.
Staging: the field exists on claim lines and is not a stored observation metric.

### allowed_total_annualized

Formula: (allowed dollars in the period / months in the period) * 12.
Example: $50,000 allowed in January. Annualized = 50,000 / 1 * 12 = $600,000. This is an extrapolation, not a year of experience.
Staging observations do not persist this. October–December dollars must not be folded into a September annualization. This audit's month filter keeps them out of the 2,250 rows.

## C. Mix

### Site-of-care shares

Formula: scoped lines with that site / all scoped lines.
Sites in the dictionary: ER, HOPD, ASC.
Example: 40 HOPD lines and 60 freestanding lines. HOPD share = 40%.
`soc_share_delta_target` = post share minus baseline share. Example: baseline 70% HOPD, observed 40% HOPD, delta = -30 percentage points.
Staging: place of service is on the line. Site share is not stored. A site-of-care policy scored only on total volume is NOT_MEASURABLE for its mechanism.

### inn_share_target

Formula: in-network scoped lines / all scoped lines.
Example: 80 in-network of 100 scoped lines = 80%.
Staging: `in_network` is on the line and is not an observation metric.

### oon_leakage_rate_target_per_1000_mm

Formula: (out-of-network scoped lines / policy_eligible_member_months) * 1000.
Example: 20 out-of-network lines, 1,000 member-months. Rate = 20.
Staging: not calculated.

### service_share_target

Formula: lines for one code or code group / all scoped lines.
Example: 72148 is 30 of 100 MRI lines = 30%.
Staging: not calculated.

### top10_provider_share_target

Formula: scoped lines from the ten providers with the most scoped lines / all scoped lines.
Example: top ten providers have 450 of 1,000 lines = 45%.
Staging: not calculated.

### provider_hhi_target

Formula: sum of squared provider shares. 0 is fully dispersed, 1 is a single provider.
Example: two providers at 50% each. HHI = 0.25 + 0.25 = 0.50.
Staging: not calculated.

## D. Substitution and timing

### substitution_uplift_per_1000_mm

Formula: observed rate of the substitute service minus the rate expected from baseline trend.
Example: baseline substitute rate 10 per 1,000, trend-expected 11, observed 18. Uplift = 7 per 1,000.
Staging: not calculated. No counterfactual series is stored.

### deferral_index_target

Formula: post 30-day targeted rate / baseline 30-day targeted rate, or a shift in time from the index date to the service.
Example: baseline 30-day rate 40, post 20. Index = 0.5, which is a delay only if the denominator is the same eligible population.
Staging: not calculated. Service dates are concentrated on the 15th, so timing shift cannot be seen.

## E. Behavior

### provider_archetype_share

Formula: providers in a class / providers in scope.
Example: 15 of 60 providers classed as resistant = 25%.
Staging: not calculated. No archetype assignment is on these rows.

### provider_ordering_intensity_target_per_1000_mm

Formula: (scoped lines attributed to the provider / member-months of that provider's population) * 1000.
Example: 30 lines, 200 attributed member-months. Intensity = 150.
Staging: not calculated.

### patient_response_share

Formula: member-months in a segment who show the response / member-months in the segment.
Example: 100 of 500 member-months substitute to another site = 20%.
Staging: not calculated.

## F. Prediction and learning

### Absolute and percent change

```
absolute = observed - baseline
percent = (observed - baseline) / baseline * 100
```

Example: baseline 120 per 1,000 member-months, observed 108.
Absolute = -12. Percent = (108 - 120) / 120 * 100 = -10%.
Both numbers must already be rates on the same denominator and the same period length. An annual count minus a monthly count is not this formula.

### prediction_error_util_pp

Formula: observed percent change minus predicted percent change, in percentage points.
Example: predicted -8%, observed -10%. Error = -2 percentage points. The prediction was slightly too high.
Staging: predicted percent is hardcoded at -5% utilization. The stored comparison is a difference of rates, not this percentage-point error.

### prediction_error_cost_pmpm

Formula: observed PMPM change minus predicted PMPM change.
Example: predicted -$2.00 PMPM, observed -$1.00 PMPM. Error = +$1.00 PMPM.
Staging: predicted cost is hardcoded at 97% of the baseline rate. It is not an estimated effect.

### confidence_score

Formula: a weighted composite of data sufficiency, analog strength, and uncertainty width, from 0 to 100.
Example: thin data and a wide interval should score low even when the point estimate is large.
Staging observations: not stored. Do not treat a populated verdict as high confidence.

## G. Mechanism measures that staging did not calculate

These are the calculations a policy of that type needs. The staging rows do not contain them. Using the generic volume formula instead is NOT_MEASURABLE, not a simplified version of the same measure.

### Prior authorization

Approval rate = approvals / decisions.
Denial rate = denials / decisions.
Example: 70 approvals and 30 denials. Approval rate = 70%. A drop in MRI claim lines is not an approval rate.
Required data absent: authorization requests and decisions.

### Coverage and clinical criteria

Criteria met rate = scoped services meeting diagnosis, age, and frequency rules / scoped services.
Example: 40 of 100 lumbar MRI lines meet the criteria. Rate = 40%.
Required data absent: diagnosis and the criteria schedule.

### Site of care

Use the site-share formula in section C.
Example: infusion HOPD share moves from 80% to 50% on the same eligible drug codes, with member-months held constant.
Required for a valid share: eligible drug or service definition and place of service. Volume change alone is the wrong measure.

### MPPR and other payment policy

Identify same-day, same-provider procedure groups. Rank lines. Apply the reduction to the lower-ranked allowed amounts.
Example: two procedures the same day, allowed $1,000 and $600. Second line pays at 50% = $300. Reduction = $300.
A lower claim count is not this reduction.
Required data absent: grouping key, rank, and the fee schedule.

### NCCI procedure-to-procedure

Pair rate = column-2 lines billed with their column-1 partner on the same day / column-1 lines.
Example: 10 column-2 lines paired with the column-1 code, out of 100 column-1 lines. Pair rate = 10%.
Required data absent: the PTP edit table and modifiers.

### NCCI medically unlikely units

Excess units = max(0, units on the date of service - MUE value).
Example: MUE is 1, billed units are 3. Excess = 2.
Required data absent: the MUE table. Units exist on the claim and were not compared with an edit.

### Pharmacy

Step completion, quantity limit, and days supply are product-level.
Example: 25 of 100 first fills have a required prior product within 180 days. Step rate = 25%.
Required data absent: NDC or a drug-product history. A HCPCS J-code count is not a step-therapy result.

### Benefit and cost sharing

Use `member_cost_share_pmpm`.
Example: baseline member share $15 PMPM, observed $22 PMPM on the same eligible member-months. Change = +$7 PMPM.
Required data absent: the enrollment denominator. The cost-share field on the line is not enough.

### Network

Use `inn_share_target`.
Example: in-network share of scoped imaging moves from 90% to 84%.
Required data absent as a stored metric. The flag exists on the line.

### Administrative and compliance

These policies need process evidence: documentation rate, turnaround, audit pass rate.
Example: 92 of 100 sampled cases have the required attachment. Rate = 92%.
Claim counts do not measure this. Required data absent.

### Quantity limit

Excess = max(0, units or days supply in the limit window − allowed quantity).
Example: limit is 30 tablets / 30 days, fill is 90. Excess = 60.
A lower claim count is not evidence the limit was applied.

### Frequency or visit limit

Excess visits = max(0, services in the lookback − allowed visits).
Example: 12 chiropractic visits allowed per year, 15 billed. Excess = 3.
Required data absent: the limit value and the member's prior services.

### Payment policy other than MPPR

Allowed after the rule minus the allowed that would have been paid without the rule, on the same lines.
Example: a DRG case priced at $8,000 instead of $10,000. Reduction = $2,000.
Required data absent: the fee schedule and the grouping key.

### Benefit design

Covered-service rate and member cost share on the eligible population.
Example: 95 of 100 preventive services adjudicated at zero member cost share. Rate = 95%.
Required data absent: the benefit decision. Enrollment is empty.

### Access

Members meeting the standard / members in scope.
Example: 860 of 1,000 members have a behavioral-health appointment within 10 days. Rate = 86%.
Required data absent: appointment or adequacy events.

### Care management program

Program participants and the stated outcome, each with its own denominator.
Example: 400 members enrolled, 40% with a completed care plan. Claim volume in the same months is not the enrollment rate.
Required data absent: program enrollment.

### Coding and billing edit

Fail rate = lines failing the edit / lines subject to the edit.
Example: 12 of 200 lines fail the edit. Fail rate = 6%.
Required data absent: the edit table. NCCI PTP and MUE are the specific forms of this measure.

### Referral

Referral present rate = scoped services with a required referral / scoped services.
Example: 70 of 100 specialty visits have a referral. Rate = 70%.
Required data absent: referral records.

### Provider eligibility

Eligible-provider share = scoped services by an eligible provider / scoped services.
Example: 88 of 100 services are rendered by a credentialed provider. Share = 88%.
Required data absent: provider eligibility.

## H. Formula actually used on staging

```
baseline utilization = (2025 matching lines / 2025 distinct claimants) * (1000 / 12)
baseline cost = 2025 matching allowed / (2025 distinct claimants * 12)
month utilization = (month matching lines / month distinct claimants) * 1000
month cost = month matching allowed / month distinct claimants
predicted utilization = baseline utilization * 0.95
predicted cost = baseline cost * 0.97
```

Status:

```
ON_TRACK if month utilization <= predicted utilization * 1.05
BACKFIRE if month utilization > baseline utilization * 1.10
AT_RISK otherwise
```

Worked staging example. Synthetic data. Not a policy effect.

```
Policy: 90-Day Retail Maintenance Program
2025 matching claim lines: 11279
2025 distinct claimants: 908
Stored baseline utilization: 1035.15
Recount of the stored formula: 1035.15
Formula: (11279 / 908) * (1000 / 12) = 1035.15

January 2026 matching claim lines: 920
Stored January utilization: 1228.3
Recount: 1228.3
Stored minus baseline rate: 193.15

Time-normalized claim-count change, which is the supported comparison:
baseline month equivalent = 11279 / 12 = 939.92
January lines = 920
change = -2.12%

These lines are synthetic. The percentage is not a policy effect.

```

## I. What may be compared

| Comparison | Valid when |
|---|---|
| 2025 claim-line count with January 2026 claim-line count | Only after dividing the 2025 count by 12, and only as a volume comparison |
| 2025 utilization rate with January utilization rate | Only when both use eligible member-months and the same scope filters |
| Either rate with a verdict | Only when the expected direction and the threshold come from the policy's own objective |
| A difference between 2025 and 2026 on these staging rows | As a check that the pipeline stored a number. Not as evidence of policy impact |

October–December 2026 claim lines stay out of January–September measures, out of any annualization of those months, and out of a current-period rate.
