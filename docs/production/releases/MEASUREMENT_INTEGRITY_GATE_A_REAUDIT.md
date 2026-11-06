# Gate A re-audit after H1–H5

Date: 2026-11-06. Branch: `measurement-integrity-gate-a`.

This re-audit inspects the H1–H5 corrections and re-runs the synthetic unit tests. It does not start an API or browser, does not query a database, and does not deploy. It is not a production-readiness decision.

Prior audit: `MEASUREMENT_INTEGRITY_GATE_A_INDEPENDENT_AUDIT.md` recommended **BLOCKED**.

## H1–H5

| ID | Original defect | Result | Evidence |
| --- | --- | --- | --- |
| H1 | Reconciliation and objectives health presented a recomputed verdict as the stored outcome | PASS | Reconciliation readiness uses the stored status. `verdict_distinction` keeps `historical_verdict_status` and `recomputed_verdict_status`. Objectives rows set `verdict_is_recomputed` and the stored column separately. The evidence pack flags `verdict_is_recomputed: false`. The objectives page captions the chip as a screen value. |
| H2 | Mounted `policies.py` copied allowed dollars into `cost_pmpm` and filled missing rates with 0 | PASS | Both prediction-input sites call `prediction_baseline_inputs`. Allowed-only input does not create `cost_pmpm`. The old `or 0.0` expression is absent from `policies.py`. |
| H3 | Observation comparison substituted allowed for paid and used `or 0.0` | PASS | Reference comparison with only `allowed_pmpm` leaves paid cost null and `cost_change_status` `UNAVAILABLE`. Predicted comparison writes `paid_pmpm_target`, not `allowed_pmpm_target`. A missing predicted level yields null accuracy, not 0 or 100. The 10,000-member savings multiplier is no longer applied. |
| H4 | Dashboard preferred allowed dollars and then zero-filled the other metric | PASS | `get` of `allowed_pmpm_total` and `round(float(util or 0), 2)` are absent from `dashboard.py`. Paid and allowed are separate fields. `cost_pmpm` is set only from the paid rate. Missing basis is stored as `CLAIMANT_MONTHS` / `NOT_MEASURABLE`. |
| H5 | Verdict, observation, scenario, and what-if screens could say PMPM without a denominator check | PASS for those headings | Bare headings `Cost impact (PMPM)`, `Cost (PMPM)`, `Utilization (per 1K)`, `Paid PMPM`, and `Utilization per 1k` are absent from the four screens. Labels say claimant-based and “not enrolled” unless a later enrolled payload is passed into `costLabel`. |

Regression tests covering the original defects are in `apps/api/tests/test_measurement_integrity_gate_a.py`. Re-run on this worktree: 26 passed, including the prior 20 and the six new H1–H5 tests (`test_objectives_health_stability.py`, `test_policy_reconciliation_gate.py`, and `test_list_observations_latest_only_policy.py` included).

## What remains unverified at runtime

No browser session and no mounted API process were started. Heading text was checked by reading the files, not by rendering them. A true enrolled payload (`denominator_basis` `ENROLLMENT` and `enrolled_rate_status` `MEASURED`) was not clicked through the UI.

`WhatIfAnalysisPage.tsx` `combineMultiPolicyResults` still adds `impact.allowed_pmpm || 0`. That is a missing-value zero on a multi-policy scenario aggregate. It is not one of H1–H5. It should be fixed before a customer demo of combined what-if results.

New observation creates still score from `observation_data.required_endpoints` only. If that field is absent, the stored verdict is `INCONCLUSIVE` even when the policy has a contract. The screen recomputes from the policy. Both values are now labeled. They can still differ.

`compute_verdict` still treats any `actionable_insights` entry as a backfire warning. A missing contract returns before that branch.

## Recommendation

**READY_FOR_ISOLATED_RUNTIME_VALIDATION**

H1–H5 pass on source inspection and synthetic unit tests. Isolated runtime validation may start on a local API and browser with synthetic fixtures. That step was not performed here. Staging deployment, the December 4 demo, and the 500,000-life dataset remain unauthorized.
