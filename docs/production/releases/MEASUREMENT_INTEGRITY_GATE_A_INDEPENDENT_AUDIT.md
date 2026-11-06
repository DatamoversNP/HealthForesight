# Gate A independent diff audit

Audit type: read-only source inspection, plus a re-run of the existing synthetic unit tests. No application code was changed. No database, deployment, or Azure resource was touched.

| Item | Value |
| --- | --- |
| Branch | `measurement-integrity-gate-a` |
| Pre-Gate-A base | `18d7010cfb88b3d28c8f614eb7bfa6f04470f7bb` |
| Implementation commit | `c2336ac040aad7e876b6f2359840994c534ee474` (parent `18d7010`) |
| Report commit | `8a25d9994ef9d20b5d937a9a83113f92254aa638` (parent `c2336ac`) |
| HEAD at audit | `8a25d99` |
| Final recommendation | **BLOCKED** |

This is not a production-readiness determination. Source inspection and the 20 unit tests do not exercise a running API or browser.

## Method

- `git merge-base` of the branch and `main` is `18d7010`.
- `git show` confirmed both reported commits, their parents, and their file lists.
- `git diff 18d7010..8a25d99` is the complete committed delta. It contains no Alembic revision, Terraform file, Dockerfile, demo fixture, or Azure change.
- The worktree still has unrelated tracked and untracked files. They are not in either commit. They were inspected and not modified.
- Call sites were read in the current worktree, which matches `8a25d99` for every file in those commits.
- The 20 tests were re-run. They passed. Their assertions were also read. Passing does not cover the defects below.

`HEALTHFORESIGHT_FORMULA_DECISION_STANDARD_V2.md` is in the worktree and was used as the decision standard. It is not inside either Gate A commit.

## Requirement results

| # | Requirement | Result | Basis |
| --- | --- | --- | --- |
| 1 | Both commits contain only authorized Gate A changes | PASS | Commit file lists below. Worktree dirt is outside the commits. |
| 2 | Formula corrections match Revision 2 and the live code paths | FAIL | Core helpers match. Live policy and comparison paths still conflate paid and allowed or fill zeros. |
| 3 | Nulls cannot become zero, perfect accuracy, or success | FAIL | Several live consumers still coerce missing numbers to 0. |
| 4 | Endpoint contracts, one-endpoint policies, read-time recomputation | FAIL | `compute_verdict` matches the contract rule. Other consumers drop the historical-versus-recomputed distinction. |
| 5 | Missing contracts never produce authoritative ON_TRACK or BACKFIRE | PASS | Early return in `compute_verdict`. Not true of a stored historical status that a different screen still displays. |
| 6 | Missing denominator metadata cannot be shown as enrolled utilization or PMPM | FAIL | Some captions fail closed. Authoritative tables and charts still say PMPM and do not read the flags. |
| 7 | Paid and allowed cannot be silently conflated | FAIL | Live `policies.py`, dashboard summary, and observation enhancement still prefer allowed dollars for a paid or generic cost field. |
| 8 | Test assertions cover boundary, zero, null, and mixed-version cases | FAIL | The suite locks the happy paths and does not catch the defects in this audit. |
| 9 | API models, frontend null handling, runtime exceptions | UNVERIFIED at runtime / FAIL on inspection | Several `.toFixed` sites are guarded. Other screens and the what-if accumulator still assume numbers. No browser run. |
| 10 | No migrations, staging writes, demo edits, infrastructure, or deployments in the commits | PASS | Diff name filter against `alembic`, `terraform`, `Dockerfile`, `demo`, and `azure` was empty. |
| 11 | Existing 2,250 observations and 250 execution blocks are unaffected as stored data | PASS for storage / FAIL for displayed verdicts | No write path for old rows. Read-time verdict, objectives health, and reconciliation change what those rows mean on screen. Execution-eligibility code is not in the commits. |
| 12 | December 4 demo is not an intended deployment target | PASS | Neither commit names the demo resource group, demo database, or demo App Service. The branch is not pushed. |

## What the commits contain

`c2336ac` changes 43 paths: measurement helpers, verdict and observation callers, prediction and learning null handling, selected API and UI labels, the implementation spec, the implementation report, and synthetic tests.

`8a25d99` adds two lines to `MEASUREMENT_INTEGRITY_P0_GATE_A_REPORT.md`: the implementation hash. Nothing else.

Untracked and unstaged work still present, and not part of these commits, includes Terraform, lean-staging Docker files, lifecycle scripts, execution-eligibility code, and the formula decision standard. A deploy or `git add -A` from this worktree would mix that work with Gate A. The commits themselves do not.

## Findings

### H1 — Recomputed verdicts are unlabeled outside the verdict list

Severity: high.

`GET /policy-verdicts` keeps the distinction. `list_policy_verdicts_route` sets `verdict` to the recomputed value, `historical_verdict_status` to the stored column, and `verdict_is_recomputed` to true. It does not call `db.add` or `db.commit` (`apps/api/src/uepi_api/routers/observations.py` around lines 674–689).

These callers recompute and present the result as the observation verdict:

- `load_reconciliation_gate` replaces the observation's `verdict` with `compute_verdict` and does not keep `verdict_status` (`apps/api/src/uepi_api/services/policy_reconciliation_gate.py` lines 263–270). `build_reconciliation_gate_for_tenant` passes that field in as `observation_verdict` (line 191). The explanation says “Verdict ready from observation comparisons” (lines 113–116). A no-contract policy becomes `INCONCLUSIVE` here even when the stored column is different.
- `build_objectives_health_snapshot` writes the recomputed status into `verdict` and `status` with no historical field (`apps/api/src/uepi_api/services/objectives_health.py` lines 119–144). Its `status_source` text says this is the same calculation as `/policy-verdicts` (line 286) and does not say the stored column was left unchanged.
- `build_evidence_pack` does the opposite. It returns the stored `verdict_status` (`apps/api/src/uepi_api/evidence_pack.py` lines 57–77). The observation page and policy monitoring panel also render `observation.verdict_status` (`apps/web/src/pages/ObservationAnalysisPage.tsx` around lines 1032–1036 and 1175–1179; `apps/web/src/components/policy/PolicyMonitoringPanel.tsx` lines 218 and 291).

Reproduction, by inspection: a stored row with `verdict_status` `ON_TRACK` and no `required_endpoints` on the policy. `/policy-verdicts` returns `verdict=INCONCLUSIVE` and `historical_verdict_status=ON_TRACK`. The evidence pack and observation page still say on track. Objectives health and the reconciliation gate say inconclusive and do not show the stored status. No test builds these three responses from one fixture.

`PolicyVerdictsPage.tsx` lines 280–282 show the stored status only when `verdict_is_recomputed` is true. The other screens have no equivalent caption.

### H2 — The mounted policy router still copies allowed dollars into cost and fills missing rates with zero

Severity: high.

Gate A changed `apps/api/src/uepi_api/routers/policies_file.py`. The running application mounts `policies.router`, not that module (`apps/api/src/uepi_api/app_extended_routes.py` line 65). `policies_file` is only named in `apps/api/src/uepi_api/routers/__init__.py`.

The live mapping is `apps/api/src/uepi_api/routers/policies.py` lines 1333–1338, repeated near lines 1506–1507:

- missing utilization becomes `0.0`
- `cost_pmpm` is `allowed_pmpm_target` or `allowed_pmpm_total` or `0.0`

A later predicted-impact call can therefore treat allowed dollars as paid and treat a missing rate as a measured zero. The unit test calls `PredictedImpactGenerator` directly and never this router.

### H3 — Observation comparison still substitutes allowed for paid and zero for missing

Severity: high.

In `apps/api/src/uepi_api/observation_enhancement.py`:

- Lines 620–621: `paid_pmpm or allowed_pmpm or cost_pmpm or 0.0` for both pre and post cost. A missing paid value becomes allowed, then zero. `or` also treats a true zero as missing.
- Lines 1099–1115: policy baselines prefer `paid_pmpm_target or allowed_pmpm_target`. General baselines assign `allowed_pmpm_total` directly into `baseline_cost_pmpm`.
- Lines 1018–1026 and 1303–1305: observed utilization and cost use `or 0.0`.

`extract_metrics_from_analysis_result` was fixed for the post-period paid key. `enhance_comparisons_with_baseline` and the narrative cost block were not. The test `test_paid_alias_does_not_become_allowed` covers only the extract function.

### H4 — Dashboard summary still prefers allowed dollars and stores a zero when one side is missing

Severity: high.

`apps/api/src/uepi_api/routers/dashboard.py` lines 198–208 select `allowed_pmpm_total` before any paid key, then:

```text
"utilization_per_1k": round(float(util or 0), 2),
"cost_pmpm": round(float(cost or 0), 2),
```

If only one of the two values exists, the other becomes 0. The executive and dashboard captions now say “Paid dollars per claimant-month” (`ExecutiveDashboardPage.tsx` line 534, `DashboardPage.tsx` line 422). The number above that caption can be allowed dollars. Missing denominator flags are not copied onto `general_baseline`, so a consumer that did check the flags would fail closed, but this builder does not attach the flags and the caption is unconditional.

### H5 — Authoritative screens still say PMPM without reading denominator metadata

Severity: high.

`measurementIntegrity.ts` fails closed: enrolled wording requires `denominator_basis === 'ENROLLMENT'` and `enrolled_rate_status === 'MEASURED'` (lines 17–30). It is used by the policy-owner baseline captions, one monitoring panel, and the baseline table header (`BaselineAnalysisPage.tsx` lines 2373–2374, which passes `undefined` and therefore the not-enrolled label).

The same baseline table then displays `allowed_pmpm_total ?? cost_pmpm ?? allowed_pmpm_target` under that not-enrolled cost caption (lines 2380–2381). Allowed and paid share one column.

These surfaces still use enrolled wording and do not consult the flags:

- `PolicyVerdictsPage.tsx` lines 246 and 359: “Cost impact (PMPM)”.
- `ObservationAnalysisPage.tsx` lines 960, 1373, 2153, 2182, 2233, 2465, 2494, 2545, 2890, 2918, 3001.
- `ScenarioComparison.tsx` lines 103–104, 134, and 161: chart keys and “Paid PMPM” / “Utilization per 1k”.
- `WhatIfAnalysisPage.tsx` lines 1627, 1653, 1786, 1817, 1882, and 1896.
- `PredictedImpactsOverviewPage.tsx` “Cost Change (PMPM)”.
- `DocumentationPortalPage.tsx` still has “Paid PMPM (M3)” and member-month table cells after lines 711–712 were corrected.
- `PredictedImpactDisplay.tsx` line 231: “Cost Change (PMPM)”.

A legacy payload with a numeric `utilization_per_1k` and no `denominator_basis` is still captioned as PMPM or “per 1k” on those screens.

### M1 — New stored verdicts do not use the policy contract

Severity: medium.

`storage_observations.py` lines 157–160 pass only `observation_data.get("required_endpoints")`. No caller in `apps/api/src` puts `required_endpoints` on that payload. A new create therefore stores `INCONCLUSIVE` and `verdict_rule_version` `v1.1-endpoints` even when the policy has one endpoint. The verdict list reads the policy and can return `ON_TRACK`. The evidence pack then shows the stored `INCONCLUSIVE`. Historical rows are not updated. The split appears on the next write.

### M2 — Any actionable insight counts as a backfire warning

Severity: medium.

`verdict.py` lines 129–140 treat any `actionable_insights` entry as a behavioral warning. The Gate A test expects `BACKFIRE` when that list is `["review"]` (`test_measurement_integrity_gate_a.py`). Stored narratives that say the policy is working also contain insights. This does not fire when the contract is missing, because lines 74–79 return `INCONCLUSIVE` first. It fires after a contract is added to a policy whose stored explanation already has insights.

### M3 — What-if arithmetic still turns missing inputs into zero

Severity: medium.

`WhatIfAnalysisPage.tsx` lines 439–485 initialize totals at 0 and add `impact.allowed_pmpm || 0`. A missing allowed change becomes a measured zero and can be divided into a percent. The confidence string on that page is null-safe. This accumulator is not.

### M4 — Dictionary display units can still say member-months

Severity: medium.

`get_measure_display` returns `defin.unit` from the metric dictionary before the Gate A fallback (`packages/common/src/uepi_common/metrics/unified_measures.py` lines 40–47). The alias map itself is correct: `cost_pmpm` maps to `paid_pmpm_total` (lines 31–36). Any API that renders `defin.unit` can still say member-months. This audit did not execute that response.

### L1 — The verdict-route test reads source text

Severity: low.

`test_read_time_verdict_route_recomputes_without_writing_history` asserts that the function source contains `endpoint_contract_from_policy` and does not contain `db.commit`. It does not call the route. A later edit can write through another helper and still pass.

### L2 — Scorecard access weight is still a constant

Severity: low.

`storage_scorecards.py` still uses access score 80. Regulatory confidence is null, and the index is null when a component is null. That part matches the report. The constant weight was out of Gate A scope.

## Formula check against the implemented helpers

These paths match the specification when called directly. They are not the only live paths.

| Family | Inspection | Result |
| --- | --- | --- |
| F20 / F19 | `impact.py` `to_dict` forces `p_value` null, `confidence_interval.level` null, and `uncertainty_status` `UNVERIFIED_INFERENTIAL`. `_compute_p_value` returns null. `_bootstrap_pre_post_ci` still uses `n=1` on an empty frame. | PASS for this module |
| F26 / F52 | `PredictedImpactGenerator` keeps −25.2% and −22.68% for hard prior auth plus imaging elasticity, sets method `SIMULATION_LOOKUP`, and leaves confidence and missing levels null. | PASS for the generator; FAIL for `policies.py` inputs (H2) |
| F01 / F09 | `annotate_claimant_exposure` nulls rates at zero claimants and labels positive claimant rates as not enrolled. Annualization of $100 × 1,200 claimant-months over 12 months remains $120,000. | PASS for those functions |
| F06 | `normalize_to_canonical_key("cost_pmpm")` is `paid_pmpm_total`. | PASS for the alias map; FAIL downstream (H3, H4) |
| F18 / F29 | `_relative_percent` returns null when the baseline is missing or not positive, and 0 when both sides exist and are equal. Enhancement still has `or 0.0` paths. | PASS for `impact.py`; FAIL for enhancement |
| F30 / F57 | No contract returns `INCONCLUSIVE`. One decrease endpoint can be `ON_TRACK` without a cost change. `monitor_only` stays `INCONCLUSIVE`. A missed direction without insights is `AT_RISK`. | PASS for `compute_verdict`; M2 qualifies backfire |
| F07 | Predicted 0 yields null accuracy. Predicted −10 and observed −8 yield 80 and `within_range` false. The summary skips null accuracy. | PASS |
| F51 | A null confidence score does not become 50. | PASS for the scorecard helper |

Demo payment constants were not in the diff. This audit did not re-execute the MPPR, site-of-service, PTP, MUE, therapy, or infusion fixtures.

## Historical integrity

No migration is in `18d7010..8a25d99`. `storage_observations.py` changes the create path only. There is no update of existing `verdict_status`. The 2,250 stored rows and the execution-eligibility module are not modified by these commits.

Deploying the branch would still change read behavior for those rows:

- `/policy-verdicts`, objectives health, and reconciliation would recompute `INCONCLUSIVE` for policies with no endpoint contract.
- Evidence packs, observation detail, and monitoring would keep showing the stored status.
- The 250 execution blocks are unchanged because `policy_execution_eligibility.py` is untracked and not in the commits.

The database was not queried in this audit. “2,250” and “250” are the prior audit’s counts, not a new count.

## Tests that are missing

The re-run on 6 November 2026 reported 20 passed in 1.76 seconds. Assertions that exist:

- claimant label and empty denominator
- canonical paid alias and one extract case
- annualization identity
- null percent, null p-value, unchanged bootstrap `n=1` source text
- generator known percents and null confidence
- learning accuracy at predicted 0 and the −10/−8 case
- verdict contract cases, including one endpoint and monitor-only
- source text of the verdict route and the mock p-value
- narrative text without a contract
- scorecard null confidence
- objectives health: no contract is `INCONCLUSIVE` / `no_data`; one endpoint is `ON_TRACK`

Not asserted:

- `policies.py` baseline mapping
- enhancement cost fallback from allowed to paid, or a true zero paid value
- dashboard `float(util or 0)` when cost exists and utilization does not
- reconciliation and objectives health responses alongside `historical_verdict_status`
- evidence pack remaining on the stored status while the verdict list changes
- a new observation create with a policy contract and an empty payload
- backfire only for a real warning, not any insight string
- UI render with missing `denominator_basis`
- what-if missing allowed change
- mixed `v1.0-scoped-month` stored rows and `v1.1-endpoints` recomputation
- negative baseline percent, and a measured 0% that must survive `or 0`

## Runtime versus inspection

| Checked by reading code or git | Checked by executing |
| --- | --- |
| Commit contents, parents, and dirty worktree | The 20 existing unit tests, re-run locally |
| Verdict, alias, null, and UI call sites | None of the FastAPI routes |
| Absence of migrations and demo files in the commits | No database, no browser, no deployment target |

Possible runtime exceptions that were not executed:

- `WhatIfAnalysisPage.tsx` division and `.toFixed` after `|| 0` usually returns a number, so it misleads rather than throws.
- `PredictedImpactDisplay` guards the confidence chips that were converted to null. A remaining `cost_change_pmpm >= 0` comparison is guarded at the icon. `formatCurrency` already accepts null.
- `ObservationAnalysisPage` percent display uses `!= null` before `.toFixed` at the site changed in Gate A. Other percent sites in that large page were not exhaustively executed.
- Scorecard `round` is guarded when a component is null.

## Deployment isolation

The commits do not target the December 4 demo. They were not pushed. No workflow file in this inspection names `healthforesight-rg`.

The hazard is the dirty worktree, not the two commits. Terraform under `infra/terraform/envs/enterprise-lean-staging/` and the lean-staging Docker files are modified or untracked beside the branch. They must stay out of any Gate A review build.

## Recommendation

**BLOCKED**

Do not approve staging deployment. Do not treat the branch as ready for isolated runtime validation until H1–H5 are corrected on this branch and the missing tests above fail before the fix and pass after it.

Isolated runtime validation remains the right step after those corrections. It needs a synthetic API and web process that is not the December 4 demo, and it needs fixtures for: no endpoint contract, one endpoint, stored `ON_TRACK` versus recomputed `INCONCLUSIVE`, missing denominator flags, and allowed-only cost fields.

This audit does not establish production readiness.
