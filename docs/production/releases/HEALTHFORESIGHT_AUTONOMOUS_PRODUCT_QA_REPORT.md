# HealthForesight autonomous product QA

## 1. Executive assessment

The agent discovered 287 policies and evaluated each through the API, stored comparisons, and an independent claim-line and exposure oracle. 0 failed the data contract and 0 failed the calculation check. 0 browser journeys failed on the final retest. Review-only and blocked policies are not treated as executed.

False completeness check: 191 policies are legitimate configuration gaps, 90 are review-only, and 6 are payment simulations. Populated baseline, prediction, and observation rows were present for the catalog, and none of those rows were accepted as proof that a payment mechanism ran.

False visual correctness check: the observation chart journey required the stored baseline and observed series, refused a fabricated monthly prediction line, and required an explicit statement that the 18-month baseline and 15-month observation totals cover different lengths.

False financial correctness check: the executive payment-rule total stayed −2.04 across 6 policies and the continuation total stayed −15.78 across 281 policies. Both matched the independent oracle. They remained separate cards.

First run found three frontend defects (missing unequal-window chart wording and missing What-If not-savings warning on both frontends). Those were repaired in `mock-r1-20261106f` / `mock-r1-dv-20261106f` and retested on staging. Final status for all three is fixed.

Mock-client staging: **GO FOR SUPPORTED CONFIGURATIONS ONLY**.
Functional production readiness: **FAIL**.

## 2. Environment

- Web: `https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io`
- Data Voyager: `https://hfleanstg-web-datavoyager.whiteplant-64737337.eastus2.azurecontainerapps.io`
- API: `https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1`
- API health: 200
- Database name: hfleanstg
- Synthetic: True (`SYNTHETIC_LONGITUDINAL_V1`)
- Covered lives: not reported by the longitudinal identity path
- Tenant: 00000000-0000-0000-0000-000000000001
- Policies discovered: 287
- December 4 demo image check: DOCKER|healthforesightacr.azurecr.io/healthforesight-api:dec4-stab-5b587ed

The test target host is lean staging. The December 4 demo was not opened.

## 3. Build and dataset

- Web revision: `hfleanstg-web--0000012` image `healthforesight-web:mock-r1-20261106f`
- Data Voyager revision: `hfleanstg-web-datavoyager--0000012` image `healthforesight-web:mock-r1-dv-20261106f`
- API revision: `hfleanstg-api--0000013` image `healthforesight-api:mock-r1-20261106f`
- Pre member-months recomputed by the QA oracle: 4931065.313584
- Post member-months recomputed by the QA oracle: 4055428.690707

## 4. Feature inventory

Browser journeys executed: **36**. This is not 287 browser journeys.
Browser passes: 36. Browser failures: 0.

| Journey | Result |
| --- | --- |
| route-dashboard-executive | PASS |
| route-dashboard-policy-owner | PASS |
| route-dashboard-analyst | PASS |
| route-policies | PASS |
| route-policy-verdicts | PASS |
| route-objectives-health | PASS |
| route-baseline-analysis | PASS |
| route-observation-analysis | PASS |
| route-predicted-impacts | PASS |
| route-whatif | PASS |
| route-whatif-scenarios | PASS |
| route-policies-builder | PASS |
| route-medicare-rules | PASS |
| route-exports | PASS |
| route-audit-log | PASS |
| route-lineage | PASS |
| route-cohorts | PASS |
| route-analyses | PASS |
| route-scorecards | PASS |
| workspace-4aa9248d | PASS |
| workspace-4700258b | PASS |
| workspace-67217db4 | PASS |
| workspace-475b0843 | PASS |
| workspace-9723994c | PASS |
| workspace-00ce7271 | PASS |
| workspace-6395fca8 | PASS |
| workspace-1ffd459a | PASS |
| workspace-a31915b1 | PASS |
| workspace-ffe9b246 | PASS |
| workspace-c7998b09 | PASS |
| workspace-7179e9f3 | PASS |
| chart-4aa9248d | PASS |
| executive-separation | PASS |
| whatif-disclaimer | PASS |
| executive-separation | PASS |
| whatif-disclaimer | PASS |

## 5. Policy results

- Discovered: 287
- Data contract pass: 287
- Data contract fail: 0
- Calculation fail: 0
- Browser sample, not the full catalog: 36

Execution classes:

- legitimate_gap: 191
- payment_simulation: 6
- review_only_not_execution: 90

A review-only or blocked row is not counted as an executed mechanism.
A continuation prediction is not counted as policy execution.

## 6. Lifecycle

Every discovered policy was checked for a baseline, an observation, a frozen prediction, a verdict, and an execution record.
Payment-rule policies are excluded from the continuation formula.
Policies whose baseline or observation dollar total disagrees with claim lines by more than $1: 0.

## 7. Calculation discrepancies

Independent continuation rollup: {'payment_sum': -2.04, 'payment_count': 6, 'continuation_sum': -15.78, 'continuation_count': 281}
Dashboard payment figure: -2.04
Dashboard continuation figure: -15.78
Dashboard comparison: {'payment_matches_oracle': True, 'continuation_matches_oracle': True, 'payment_api': -2.04, 'continuation_api': -15.78, 'payment_oracle': -2.04, 'continuation_oracle': -15.78}

Population what-if dollar results were not recomputed claim by claim in this run.
The published payment fixtures were checked only as offline arithmetic, not as the 500k population totals.

## 8. Dashboard and charts

Chart journeys require the baseline and observed series, an explicit statement when the 18-month and 14-month totals are not the same length, and no fabricated monthly prediction line.

## 9. What-if

Overlapping what-if status 400. Observation count before 287, after 287. A simulated difference is not measured savings. Population what-if dollars were not recomputed from individual claim lines in this run. Disposable policy create status 201. Deleted by primary key: True.

## 10. Defects

| ID | Severity | Status | Feature | Actual |
| --- | --- | --- | --- | --- |
| HFQA-001 | high | fixed | chart-4aa9248d | missing text: Baseline allowed; missing text: Observed allowed; missing text: These period totals cover different lengths; forbidden text: Prediction not available for this policy yet; after click missing: These period totals cover different lengths; after click forbidden: claimant-month |
| HFQA-002 | high | fixed | whatif-disclaimer | missing text: not measured savings |
| HFQA-003 | high | fixed | whatif-disclaimer | missing text: not measured savings |

## 11. Evidence

Policy matrix: `docs/production/releases/HEALTHFORESIGHT_QA_POLICY_MATRIX.csv`
Defects: `docs/production/releases/HEALTHFORESIGHT_QA_DEFECTS.csv`
Machine-readable results: `docs/production/releases/HEALTHFORESIGHT_QA_RESULTS.json`
Screenshots are referenced from the browser results and contain no credentials.

## 12. Regression tests

============================= test session starts ==============================
platform darwin -- Python 3.14.10, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/nileshl/Private/HealthForesight
configfile: pyproject.toml
plugins: anyio-4.16.0
collected 5 items

qa/product_agent/test_oracle_arithmetic.py .....                         [100%]

============================== 5 passed in 0.03s ===============================


## 13. Remaining blockers

- 122 catalog packages have no candidate procedure code. Those policies stay blocked.
- Parameters other than quantity_limit_units do not have an implemented engine.
- Unsigned clinical policies are not executed.
- Population what-if dollars were not independently recomputed from claim lines. The agent verified that overlapping what-if is rejected and that observations are not overwritten.
- Browser coverage is one journey per mechanism family and the required edge cases, not 287 browser journeys.
- Medicare rules inventory is empty on this dataset (`count=0`). The page no longer returns 500.

## 14. Mock-client staging decision

**GO FOR SUPPORTED CONFIGURATIONS ONLY**. Supported payment simulations and correctly labeled review or blocked policies can be shown. A failed calculation, a false execution claim, or a failed customer journey blocks staging.

## 15. Functional production readiness

**FAIL**. Functional production readiness stays fail. The catalog contains unsigned clinical policies, policies with no candidate code, and parameters whose engines are not implemented. Staging evidence is not approval for another client's data.

This report was generated by `python -m qa.product_agent` after the checks in this file's JSON companion. It is not a manual claim that the backend passed.
