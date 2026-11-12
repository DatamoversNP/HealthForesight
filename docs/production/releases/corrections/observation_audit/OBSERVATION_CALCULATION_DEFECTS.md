# Observation calculation defects — lean staging

Ordered by severity. Counts are from the read-only audit at 2026-11-06T03:29:07.712635+00:00.

## P0 — Annual baseline rate compared with a monthly rate

The stored baseline utilization divides claim lines by distinct annual claimants and by 12. The stored monthly utilization divides that month's claim lines by that month's distinct claimants and does not divide by 12.

Those denominators are not the same exposure. The persisted `vs_baseline.utilization_change` is the difference of those two rates. It is not a time-normalized change in services per eligible member-month.

Affected rows: all 2250 observations. Classification: `rate_comparison_validity = FAIL`.

The CSV column `claim_volume_change_pct_vs_monthly_equivalent` is the only time-normalized comparison this audit will stand behind, and it is a claim-count comparison, not a utilization rate.

## P0 — No eligible-member denominator

Enrollment rows on staging: 0.

The dictionary formula needs `policy_eligible_member_months`. The stored formula uses distinct `member_id` values on matching claims. Members with no matching claim drop out of the denominator. This audit does not fill in an enrollment number.

Utilization and PMPM cost on these rows: NOT_MEASURABLE.
Claim-line counts: reconcilable, and labeled as counts.

## P0 — Code scope is not a certified policy scope

Policies whose remediation state is missing or not claims-executable with a verified code map: 250 of 250.

A line is included when its CPT or HCPCS is in `scope.procedure_codes` (or lever targets if scope codes are empty). Place of service, line of business, diagnosis, modifiers, provider, and site restrictions on the policy are not applied.

Scope result on the observation CSV: FAIL for those policies. A numerically matching count on an uncertified code list is not a valid policy observation.

## P0 — Synthetic lines are not policy-effect evidence

Source mix: {"Q1_2026_DEMO": 2880, "DATA_GENERATOR": 2205, "POLICY_MONTHLY_DENSIFY": 48864}.

`DEMO_SUBSET_COPY` count is 0. The legacy demo warehouse (about 3.5 million lines) was not loaded.

`POLICY_MONTHLY_DENSIFY` builds both the 2025 baseline window and the 2026 observation window. Observed differences follow that generator. They are not an estimate of what the policy did.

Effectiveness column on every policy: NOT_SUPPORTED.

## P1 — One generic formula for every mechanism

All 250 policies persist `utilization_per_1k` and `cost_pmpm`. Mechanism-specific measures (authorization decisions, MPPR ranking, NCCI edits, site share, pharmacy sequence, member cost share against enrollment) are not calculated.

Metric validity on every observation: NOT_MEASURABLE. See `POLICY_METRIC_SEMANTICS_250.csv` for the measure each mechanism actually needs.

## P1 — Status is a hardcoded stub

`uepi_api.verdict.compute_verdict` was not called. The writer compared observed utilization with `baseline * 0.95` and used fixed 5% and 10% bands. Cost does not affect the status. There is no stored policy objective.

Status validity: INSUFFICIENT_EVIDENCE on all 2250 rows.
Rows whose stored label disagrees with even that hardcoded rule: 0.

## P1 — Future-dated and collapsed service dates

Service dates after 6 Nov 2026: 4282. Those lines sit in October–December observations, which were not created, so they do not enter the 2,250 recomputations. They remain in the 2026 claim total of 28257.

Lines with a service date on the 15th: 51165 of 53949. That is the generator midpoint, so within-month runout and partial-month timing cannot be tested on these lines.

## P2 — Arithmetic recount

Baseline rows that do not match an independent code-filtered recount: 0 of 250.
Observation rows that do not match: 0 of 2250.

Null allowed amounts: 0. Negative allowed: 0. Duplicate claim-line keys: 0.

A zero in the P2 counts means the stored figures are the output of the stored formula. It does not close the P0 defects.

## What this audit does not claim

Measurement correctness and policy effectiveness are different. An observation can match its formula and still provide no evidence that a policy caused the change. These staging rows can show that a record was stored. They cannot be presented as payer outcomes.
