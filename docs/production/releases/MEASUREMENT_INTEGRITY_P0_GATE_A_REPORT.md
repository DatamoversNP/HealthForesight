# Gate A implementation report

Branch: `measurement-integrity-gate-a`

Implementation commit: `c2336ac040aad7e876b6f2359840994c534ee474`

Governing documents: `HEALTHFORESIGHT_FORMULA_DECISION_STANDARD_V2.md` and `MEASUREMENT_INTEGRITY_P0_IMPLEMENTATION_SPEC.md`.

This commit implements Gate A in application code and synthetic tests. It does not deploy, does not connect to a database, does not change a schema, and does not write staging, production, or the December 4 demo.

## Authorization boundary

Implemented: F20, F26, F01, F06, F18, F29, F52, F30, F57, F07, F51, plus F09 and F19 labeling.

Not implemented: Gate B quarantine table, the 2,250 metadata rows, enrollment ingestion, F48, F50, observation or baseline regeneration, the 250 execution-eligibility blocks, demo fixtures, Azure resources, and the seven-wave program.

## Rollback

The production rollback is to revert this commit and restore the last approved deployment. No observation or baseline rows are rewritten, so no data restore is required.

The restored deployment still emits fabricated 0.01/0.50 p-values, still labels claimant ratios as enrolled utilization or PMPM, and can still score ON_TRACK without an endpoint contract. Restoring those behaviors is not an acceptable production correction. The analytical limitations of that deployment remain.

## Files and why

- `packages/common/src/uepi_common/metrics/measurement_integrity.py` — shared labels. A rate is enrolled only when `denominator_basis` is `ENROLLMENT` and `enrolled_rate_status` is `MEASURED`. Missing flags are not enrolled. Zero claimants null the rate keys.
- `packages/common/src/uepi_common/metrics/unified_measures.py` — `cost_pmpm` and `cost_per_member` canonicalize to `paid_pmpm_total`, not allowed.
- `packages/common/src/uepi_common/analytics/impact.py` — percent change is null when the baseline is missing or not positive. `p_value` on the result is null. The interval is labeled a line-level resample, not a 95% confidence interval. The bootstrap loop, including empty-frame `n=1`, is unchanged.
- `packages/common/src/uepi_common/analytics/predicted_impact.py` — lookup percents remain. Confidence is null. Method is `SIMULATION_LOOKUP` or `CALLER_ELASTICITY`. Missing baselines stay null. Evidence class is `SIMULATION_ONLY`.
- `packages/common/src/uepi_common/analytics/baseline.py` — claimant-path units no longer say enrolled member-months. The enrollment-path PMPM wording is unchanged.
- `apps/api/src/uepi_api/verdict.py` — rule `v1.1-endpoints`. No contract returns `INCONCLUSIVE`. One declared endpoint can be `ON_TRACK`. `monitor_only` cannot. A missed direction is `AT_RISK`, or `BACKFIRE` when behavioral warnings are also present.
- `apps/api/src/uepi_api/routers/observations.py` — `/policy-verdicts` recomputes with the policy contract and returns `historical_verdict_status` plus `verdict_is_recomputed`. It does not write the observation. The pending-analysis mock no longer writes `p_value` 0.01.
- `apps/api/src/uepi_api/services/objectives_health.py` and `policy_reconciliation_gate.py` — same contract. A true zero change is not treated as missing.
- `apps/api/src/uepi_api/storage_observations.py` — new writes pass `required_endpoints` from the new payload. Historical rows are not updated.
- `apps/api/src/uepi_api/observation_enhancement.py` — paid is not copied from allowed. Missing rates, percents, intervals, and confidence are not filled with 0. Narratives without a contract are `INCONCLUSIVE` and do not say statistically significant or 95% CI.
- `apps/api/src/uepi_api/learning_loop.py` and `routers/learning.py` — predicted zero yields null accuracy. Summaries skip nulls.
- `apps/api/src/uepi_api/routers/analyses.py` — mock p-value is null. A missing trust-panel score is `UNAVAILABLE`, not 70.
- `apps/api/src/uepi_api/routers/policies_file.py` — prediction inputs no longer invent 10,000 members or copy allowed dollars into paid.
- `apps/api/src/uepi_api/routers/dashboard.py` and `cohorts_file.py` — missing exposure no longer becomes 10,000, and a missing change is not shown as zero.
- `apps/api/src/uepi_api/storage_scorecards.py` — null confidence does not become 50, and the index is null when a component is null.
- `apps/api/src/uepi_api/database_claims_loader.py` and `baseline_metrics_computation.py` — claimant exposure flags and the annualization identity, labeled claimant-based.
- Web label and null guards listed in the compatibility section.
- `apps/api/tests/test_measurement_integrity_gate_a.py` and the no-contract assertion in `test_objectives_health_stability.py`.

## Tests

Command:

`PYTHONPATH=apps/api/src:packages/common/src:scripts .venv7867/bin/python -m pytest apps/api/tests/test_measurement_integrity_gate_a.py apps/api/tests/test_objectives_health_stability.py apps/api/tests/test_policy_reconciliation_gate.py apps/api/tests/test_list_observations_latest_only_policy.py -q`

Result: 20 passed. Fixtures are synthetic. No database connection.

The project virtualenv did not already contain pytest. Pytest 9.2.0 was installed into `.venv7867` so the suite could run. `requirements.txt` was not changed.

## Before and after

| Correction | Before | After |
| --- | --- | --- |
| F20 p-value | 0.50 if the range contains 0, otherwise 0.01. Enhancement used 1.0 and “statistically significant” below 0.05. | Result `p_value` is null. `uncertainty_status` is `UNVERIFIED_INFERENTIAL`. `resample_grain` is `CLAIM_LINE`. |
| F19 label | “95% CI” and “95% confidence”. | “Line-level resample range. Not a validated confidence interval and not inferential uncertainty.” Algorithm unchanged, including empty-frame sample size 1. |
| F26 / F52 prediction | Missing elasticity became a default table and was labeled `ELASTICITY_MODEL`. Baselines fell back to 100, 500, and 10,000. Confidence was a penalty score. | Hard prior auth, imaging elasticity −0.35: utilization −25.2%, cost −22.68%. Method `SIMULATION_LOOKUP`. Confidence null. Level changes null when baselines are missing. |
| F01 / F09 exposure | Zero claimants stored a rate or divided by 1. Annualized dollars could be read as enrolled spend. | Zero claimants: rates null, `measurement_status` `NOT_MEASURABLE`, reason `EMPTY_DENOMINATOR`. $100 PMPM over 1,200 claimant-months and 12 months remains $120,000, labeled claimant-based, not enrolled-population spend. |
| F06 paid identity | `cost_pmpm` canonicalized to allowed. | `cost_pmpm` canonicalizes to `paid_pmpm_total` with `cost_pmpm_meaning` `PAID`. Allowed stays on `allowed_pmpm`. |
| F18 / F29 percent | Baseline at or below 0 became 0% or 999. Missing percent became 0 through `or 0`. | Null and `change_status` `UNAVAILABLE`. A real 0% stays 0 with `MEASURED` when both sides exist and the baseline is positive. DiD illustration (80−100)−(95−100) = −15. |
| F30 / F57 verdict | Both utilization and cost at or below 0, or a fallthrough, could be `ON_TRACK`. Narratives said excellent performance. | No contract: `INCONCLUSIVE`. One decrease endpoint at −25% with a +4% cost change: `ON_TRACK`. Missed direction: `AT_RISK`. Missed direction plus an insight: `BACKFIRE`. `monitor_only`: `INCONCLUSIVE`. |
| F07 accuracy | Predicted 0 produced accuracy 100. | Predicted 0: accuracy null, `accuracy_status` `UNAVAILABLE`. Predicted −10 and observed −8: error 20%, accuracy 80, `within_range` false. |
| F51 scorecard | Missing confidence became 50, then 70 after the +20 boost. | Regulatory score and effectiveness index are null. |

Demo payment known answers were not edited. MPPR remains baseline 3150, post 2550, impact 600. Site of service remains 4000 / 3480 / 520. PTP remains 4400 / 3600 / 800. The demo MUE cap of 4 remains 650 / 550 / 100. Therapy remains 420 / 340 / 80. Infusion remains 18200 / 14600 / 3600.

## API and UI compatibility

Legacy numeric keys remain when the claimant count is positive. Authoritative labels say “not enrolled” unless the payload has both enrollment flags. A missing basis is treated as not enrolled.

Nullable fields: confidence, accuracy, denominators, percent changes, level changes, and p-values. Response models that required an accuracy percent are now optional. The policy-verdict response adds `historical_verdict_status` and `verdict_is_recomputed` without a database column.

Checked consumers that previously called `.toFixed` or divided confidence by 100: predicted impact, scenario comparison, analysis workspace, observation analysis, what-if confidence text, and the verdict page. Nulls render as unavailable or an em dash. The verdict page states that the chip is the screen value and shows the stored status separately.

## Read-time verdict

`list_policy_verdicts_route` calls `compute_verdict` with `endpoint_contract_from_policy` for the response only. The test reads that function and checks that it does not call `db.add` or `db.commit`. Stored `verdict_status` is returned as `historical_verdict_status`. New observation creates use `v1.1-endpoints` only for the new row. Objectives health and the reconciliation loader use the same contract. A policy with no contract and a negative utilization change is `INCONCLUSIVE` / `no_data`. A policy with one decrease endpoint and a −8% utilization change is `ON_TRACK`.

## Known remaining defects

F48 uniqueness overwrite and F50 shift-detector key mismatch remain P1. Enrollment is still absent, so eligible member-month utilization and enrolled PMPM stay not measurable. Empty bootstrap frames still use sample size 1; that algorithm was not changed. Line-level resampling is still not an inferential interval. The scorecard access weight remains the existing constant 80. Forecast, substitution, and what-if scenario math were not redesigned. Documentation tables outside the two corrected definition lines can still say member-months. Narrative text in some older branches can still describe a decrease as effectiveness when an endpoint contract is present and the direction is decrease.

## Unverified assumptions

The live staging database was not queried again. Stored observation JSON was not rewritten and was not re-read. The empty Polars bootstrap frame was not executed; the test checks that the `n=1` source line is still present. In-network flag types and the 250 code sets were not clinically recertified. The web screens were not clicked in a browser. This authorization prohibits deployment, and no local application server was started. UI safety is from the source guards and the synthetic API tests.

## Confirmation

No deployment ran. No database statement ran. No schema was created or altered. No Azure resource was changed. The December 4 demo, its fixtures, and its App Service were not modified. Gate B was not started.
