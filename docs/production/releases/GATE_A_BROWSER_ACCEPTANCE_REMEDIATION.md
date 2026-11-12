# Gate A browser acceptance remediation

Date: 2026-11-06. Local code and synthetic checks only. Lean staging was not redeployed. The December 4 demo, historical staging observations, execution blocks, database schemas, and Azure infrastructure were not changed. The 10,000-life pilot remains blocked.

## Defects

1. Observation tiles and the CKD detail used the stored `verdict_status` as the current conclusion. A stored BACKFIRE appeared as “Backfire risk” and “Verdict: BACKFIRE” with no screen recomputation.
2. The executive and home rollup cards labeled a dollar sum “Σ ΔPMPM” without a verified enrollment denominator. Missing utilization changes were coerced with `or 0` and `metrics.get("utilization_change_pct", 0)`, so an all-missing set displayed as 0.0%. A missing `cost_change_pmpm` fell through to `change_from_baseline`, which is a utilization level change, not dollars. An empty cost sum was returned as 0.

## Root causes

Observation list and detail render `ObservationAnalysisPage` from `GET /api/v1/observations`. That response returned the stored verdict and did not attach the same read-time `compute_verdict` result the Policy Verdicts route already computes. The page then colored the chip from `verdict_status`.

The executive cards read `GET /api/v1/dashboard/summary` (`get_dashboard_summary` in `apps/api/src/uepi_api/routers/dashboard.py`). The home page at `/` uses the same summary. Both pages also applied `|| 0` while formatting, so a null from the API would still have rendered as 0.0%.

## What changed

Stored observation rows are not updated. Read responses now add `screen_verdict`, `screen_verdict_reason`, `screen_recommendation`, `historical_verdict_status`, and `verdict_is_recomputed`. `verdict_status`, `verdict_reason`, `recommendation`, and `verdict_rule_version` stay equal to the stored values. No endpoint contract still scores INCONCLUSIVE. One directional endpoint can still score ON_TRACK. A required endpoint with no measured change stays INCONCLUSIVE.

The rollup now lives in `aggregate_policy_observation_rollups`. Null utilization changes are excluded. A measured 0 is kept, and the count of contributing observations is returned. If none are measured, the average is null and the status is UNAVAILABLE. Dollar changes are included only from `cost_change_pmpm` or `cost_change`. Claimant-month rows are labeled “claimant-month $” and “not enrolled PMPM”. Enrolled “Σ enrolled ΔPMPM” is used only when `denominator_basis` is ENROLLMENT and `enrolled_rate_status` is MEASURED. Mixed bases, or a cost change with no usable basis, return a null total. The home page no longer paints 0.0% while it is redirecting to a role dashboard or when the summary is absent.

Scenario comparison no longer calls `toFixed` on a missing percent. A reimbursement what-if result shows Unavailable for missing percents and shows `delta_payment_impact` as fixture dollars, not enrolled PMPM.

## Changed files

- `packages/common/src/uepi_common/metrics/measurement_integrity.py`
- `apps/api/src/uepi_api/verdict.py`
- `apps/api/src/uepi_api/routers/observations.py`
- `apps/api/src/uepi_api/routers/dashboard.py`
- `apps/api/src/uepi_api/storage_observations.py` (summary responses keep `risk_factors` and `actionable_insights` so the read-time verdict can see warnings; rows are not rewritten)
- `apps/web/src/components/ObservationVerdict.tsx`
- `apps/web/src/pages/ObservationAnalysisPage.tsx`
- `apps/web/src/pages/dashboardRollup.ts`
- `apps/web/src/pages/DashboardPage.tsx`
- `apps/web/src/pages/persona/ExecutiveDashboardPage.tsx`
- `apps/web/src/components/ScenarioComparison.tsx`
- `apps/web/src/pages/WhatIfAnalysisPage.tsx`
- `apps/api/tests/test_measurement_integrity_gate_a.py`
- `apps/web/src/pages/__tests__/gateAAcceptanceRemediation.test.tsx`

## Regression tests

`apps/api/tests/test_measurement_integrity_gate_a.py`: 30 passed.

Covered cases:

- Stored BACKFIRE stays BACKFIRE while the screen verdict is INCONCLUSIVE when no contract is present.
- One utilization endpoint with a decrease remains ON_TRACK at read time, and the stored status stays BACKFIRE.
- A contract with no measured change does not become ON_TRACK.
- All-null utilization and a utilization level in `change_from_baseline` do not become a 0.0% average or a dollar total.
- Mixed null and measured zero: average of 0 and −10 is −5, with 2 measured observations and 1 measured zero.
- Claimant-month dollars are not labeled ΔPMPM.
- Verified enrollment may use Σ enrolled ΔPMPM. Enrollment without MEASURED status does not.
- Mixed claimant and enrolled dollar changes stay unavailable, with each count reported.
- Dashboard summary source no longer contains `utilization_change or 0` or a `change_from_baseline` dollar fallback.
- Missing trend metrics stay null.
- MPPR what-if on the known-answer lines: baseline paid 3150, base secondary 50% payment impact 600, alternate 40% payment impact 720, delta 120. `utilization_change_pct` is null. `volume_effect` is 0 because the engine holds volume constant; that zero is not a utilization percent.

`apps/web` vitest `gateAAcceptanceRemediation.test.tsx` and `whatIfMultiPolicy.test.ts`: 8 passed. The UI test renders “Current screen verdict: Inconclusive” and “Stored historical verdict: BACKFIRE”, refuses a ΔPMPM unit unless the basis is ENROLLMENT, shows Unavailable for an unmeasured 0, shows 0.0 for a measured zero with a count of 2, and renders the $120 payment delta beside Unavailable percents.

## Before and after

Before, on lean staging (unchanged by this pass): observation tiles and the CKD detail led with Backfire risk. The executive card said ΔPMPM and 0.0% utilization. Screenshots remain in `docs/production/releases/gate_a_browser_acceptance/`.

After, locally: `docs/production/releases/gate_a_browser_acceptance_remediation/local-corrected-screens.png`. The observation block shows the inconclusive screen verdict, the stored BACKFIRE status, and the missing-contract reason. The rollup shows Cost Unavailable and Utilization Unavailable, plus a measured zero of 0.0 across 2 observations. The scenario table shows Unavailable percents and “Payment impact delta $120.00 (fixture dollars, not enrolled PMPM)”. That $120 is the MPPR what-if delta above, not a placeholder.

## Previously unscored views

Home `/`. The first paint is a spinner because `loading` starts true. When a role is already selected, the page redirects to that role dashboard and does not wait on the summary. The previous capture was that spinner. The page was also able to clear loading with no summary and then format a missing average as 0.0%. It now stays on “Opening your role dashboard” during the redirect, and an absent summary says the rollup is unavailable. This was not re-checked as a signed-in staging session.

Scenario result. The MPPR what-if function returned the numbers above with no database write. The comparison component rendered that shape. This was not a click-through of the What-If page on staging. A route that merely loads is not scored as a pass.

## Unresolved

- Staging still serves the previous images, so the two failures remain visible there until a separate redeploy and a new signed-in pass.
- The general baseline block still fills a missing `denominator_basis` with CLAIMANT_MONTHS. The staging baseline that passed already had that basis stored.
- Role dashboards other than the executive cards still use `|| 0` when filtering performance rows. Those filters do not turn a null into a displayed 0.0% card, but they are not the corrected rollup.
- The MPPR what-if payload sets `confidence_score` to 1.0. The comparison chip formats that number as a percent, which would read 1%. The local screenshot used a null score and shows Unavailable. The 1.0 scale was not relabeled.
- New observation writes still do not copy a policy endpoint contract onto the stored row. The screen recomputes from the policy at read time. The stored verdict is unchanged.
- MRI prior authorization, NCD 220.2, and LCD L34425 remain without an execution engine. This pass did not score them.

## Readiness

Local remediation of the two presentation defects is complete and covered by the tests above. Authenticated staging re-acceptance has not been run.

Recommendation: **not ready for the 10,000-life pilot.** Next step, only with separate authorization: redeploy this code to lean staging, then repeat the signed-in browser pass on observation tiles, CKD detail, the executive rollup, the home dashboard after it leaves the spinner, and one completed scenario result. The pilot stays blocked until that pass records PASS.
