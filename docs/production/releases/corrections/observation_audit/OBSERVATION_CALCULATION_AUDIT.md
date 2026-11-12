# Observation calculation audit — lean staging

Audited at 2026-11-06T03:29:07.712635+00:00. Read-only. No claims, baselines, observations, policies, or Azure objects were changed. The December 4 demo environment was not used.

This audit separates three questions.

| Question | Result |
|---|---|
| Were the expected records created? | Yes |
| Do the stored numbers match an independent recount of the same formula? | Baselines failing recount: 0 of 250. Observations failing recount: 0 of 2250. |
| Do those numbers measure the intended policy impact? | No. 2250 of 2250 observations are NOT_MEASURABLE. 0 are FAIL. |

A matching recount means the stored figure is what that formula produces from these claim lines. It does not mean the formula is the right measure, and it does not mean the policy caused the change.

## 1. Record check

| Check | Expected | Found | Match |
|---|---:|---:|---|
| Staging claims | 53949 | 53949 | True |
| Claims with service date in 2025 | 25692 | 25692 | True |
| Claims with service date in 2026 | 28257 | 28257 | True |
| Claims outside 2025–2026 | 0 | 0 | True |
| Demo warehouse copies (`DEMO_SUBSET_COPY`) | 0 | 0 | True |
| General 2025 baseline | 1 | 1 | True |
| Policy 2025 baselines | 250 | 250 | True |
| Other baselines | 0 | 0 | True |
| Observations | 2250 | 2250 | True |
| Observations per policy | 9 | 9–9 | True |
| Months outside Jan–Sep 2026 | none | none | True |
| Enrollment rows used as a denominator | required for a utilization rate | 0 | not used |

Claim sources: {"Q1_2026_DEMO": 2880, "DATA_GENERATOR": 2205, "POLICY_MONTHLY_DENSIFY": 48864}.

`data_snapshot_id` is absent on every observation. `policy_version_id` was not stored on the observation rows. Configuration version in the CSV is the latest `policy_versions.version_number` when one exists, not a version pinned to the calculation.

## 2. Formula that was actually stored

The staging writer did not call `compute_metrics_from_database_claims` or `compute_verdict`.

Policy baseline, calendar year 2025, codes on the policy:

```
claimants = distinct member_id on matching lines
utilization_per_1k = (claim_lines / claimants) * (1000 / 12)
cost_pmpm = sum(allowed_amount) / (claimants * 12)
```

January–September 2026 observation, same codes, service date inside that month:

```
claimants_m = distinct member_id on matching lines that month
utilization_per_1k = (claim_lines / claimants_m) * 1000
cost_pmpm = sum(allowed_amount) / claimants_m
predicted_utilization = baseline_utilization * 0.95
predicted_cost = baseline_cost * 0.97
```

Status rule actually applied (`v1.0-scoped-month`), not `uepi_api.verdict.compute_verdict`:

```
ON_TRACK  if observed_util <= predicted_util * 1.05
BACKFIRE  if observed_util > baseline_util * 1.10
AT_RISK   otherwise
```

Cost is stored and is not an input to the status.

The product dictionary formula, which was not used, is:

```
util_rate_target_per_1000_mm = (target_claim_lines / policy_eligible_member_months) * 1000
allowed_pmpm_target = target_allowed_amount / policy_eligible_member_months
```

`policy_eligible_member_months` requires enrollment. Staging enrollment row count is 0. This audit does not invent that denominator. Where a rate would need it, the result is NOT_MEASURABLE.

A supported alternative, reported in the CSV as `claim_volume_change_pct_vs_monthly_equivalent`, is:

```
baseline_month_equivalent = 2025 matching claim lines / 12
change_pct = (month_claim_lines - baseline_month_equivalent) / baseline_month_equivalent * 100
```

That is a time-normalized claim-count comparison. It is not a utilization rate and it is not a policy effect.

## 3. Independent recount

Each policy's 2025 lines are the distinct claim-line ids whose CPT or HCPCS is in that policy's current scope codes. A line that carries both a CPT and an HCPCS in the same code set is counted once. The same line may appear in more than one policy. That overlap is expected and is not double-counting inside one policy.

Baseline rows whose stored claim count and stored rates match this recount: 250 of 250.
Observation rows whose stored claim count, rates, and −5%/−3% prediction match this recount, with no line outside the month window: 2250 of 2250.
Stored status values that match the hardcoded rule above: 2250 of 2250.

October–December 2026 lines are excluded by the month filter. They do not enter the January–September recount.

## 4. Why a matching recount is still not a valid observation

1. The baseline rate divides by 12 and by the distinct claimants across the whole year. The monthly rate does not divide by 12 and uses only the claimants who had a matching line that month. Those are different exposure bases. Comparing them is not a normalized utilization change.
2. Distinct claimants are not eligible member-months. A member with no claim in the month is missing from the denominator, so the rate rises when the population shrinks. No enrollment denominator was available, and none was invented.
3. 250 of 250 policies do not have a claims-executable, verified code mapping. A correct count on the wrong codes is a scope failure.
4. Every policy is scored with the same volume formula. Prior authorization, MPPR, NCCI, site of care, pharmacy, and coverage policies need mechanism-specific inputs that are not on these rows. See `POLICY_METRIC_SEMANTICS_250.csv`.
5. The −5% prediction and the ON_TRACK band are hardcoded. They are not a documented policy objective. Status is INSUFFICIENT_EVIDENCE.
6. Almost all lines are `POLICY_MONTHLY_DENSIFY` (about eight lines per policy per month, twelve for the nine showcase policies), plus a light `DATA_GENERATOR` seed and `Q1_2026_DEMO`. The same generator fills the baseline year and the observation year. A difference between them is a property of that generator, not evidence the policy worked.

## 5. Integrity

| Check | Count |
|---|---:|
| Null allowed amount | 0 |
| Negative allowed amount | 0 |
| Negative paid amount | 0 |
| Duplicate claim_id + claim_line_id | 0 |
| Service date after 6 Nov 2026 | 4282 |
| 29 February lines | 0 |
| Service date on the 15th of the month | 51165 |

Day-15 concentration is the synthetic generator's midpoint date, not a natural service-date distribution.

## 6. Verdict

Record structure: consistent with the expected counts.
Stored-formula recount: see the fail counts above. Any fail is an arithmetic defect. A pass is only a recount.
Policy impact: not established. Do not read these observations as payer outcomes.

Files:

- `POLICY_BASELINE_RECONCILIATION_250.csv`
- `OBSERVATION_RECOMPUTATION_2250.csv`
- `POLICY_METRIC_SEMANTICS_250.csv`
- `OBSERVATION_STATUS_AUDIT.csv`
- `OBSERVATION_CALCULATION_DEFECTS.md`
- `MEASURES_FORMULAS_AND_EXAMPLES.md`
