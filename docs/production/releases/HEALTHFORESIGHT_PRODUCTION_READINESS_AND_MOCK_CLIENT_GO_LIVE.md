# HealthForesight production readiness and mock-client go-live

Date: 2026-11-06

Mock client: tenant `00000000-0000-0000-0000-000000000001`, local user `synthetic.local@example.com`, database `synthetic_payer_500k_longitudinal` on `127.0.0.1:55434`.

Catalog: 278 representative packages at `docs/demo/bcbs-nc/policy_definitions/v1.2/catalog`, package version `v1.2.0-representative-batch`, plus the 6 validated payment policies and 3 clinical source policies already stored on that database. Stored policy count: 287.

## Decisions

| Decision | Result |
| --- | --- |
| A. Mock Client Staging | **NO-GO** |
| B. Functional Production Readiness | **FAIL** |
| C. Real-Client Production Deployment Authorization | **NOT APPROVED** |

A is NO-GO because 191 policies have no executable contract, the 90 executed catalog policies only select claims for review, and the 500k environment was not deployed to isolated staging.

B is FAIL because a future client cannot run the full catalog through this product without supplying parameters the current definitions do not contain, and because staging deployment was not completed.

C is NOT APPROVED. Functional readiness was not demonstrated, and security and operations enhancements were not assessed. Successful local screens are not deployment authorization.

## What was executed

The execution contract is `mock-client-exec-v1`. It reads the package mechanism, family, candidate codes, rules, and parameters. It does not invent procedure codes, clinical allow/deny decisions, or payment percentages.

| Result | Policies | Meaning |
| --- | ---: | --- |
| Review required, no payment change | 90 | Package rule is prior authorization review and “do not auto-deny.” Matching claim lines are counted. Allowed and paid amounts are not changed. Financial effect is null. |
| Validated payment engine | 6 | MPPR, site of service, PTP, MUE, therapy, and infusion. This run did not recompute their dollars. They remain prior mechanism simulations, not observed payer savings. |
| Blocked | 191 | No supported executable contract. Eligible counts are null, not zero. |

Blocked reasons:

| Reason | Policies |
| --- | ---: |
| No candidate procedure code | 102 |
| Unsigned clinical or coverage authority | 43 |
| Missing step-therapy protocol | 12 |
| Missing site-of-care parameter | 10 |
| Missing frequency limit | 7 |
| Missing cost-share parameter | 6 |
| Missing payment parameter | 4 |
| Missing quantity limit | 2 |
| No executable rule in the definition | 2 |
| Missing coding edit | 1 |
| Missing product identifier | 1 |
| Missing episode parameter | 1 |

Every one of the 90 review policies matched an independent oracle on line count, allowed amount, and paid amount. The worker spot-check for ACL reconstruction prior authorization counted 3,011 lines, the same count as the SQL aggregate. Financial effect stayed null. One retry test confirms a worker failure stores no fabricated amount.

The complete row-level matrix is `docs/production/releases/HEALTHFORESIGHT_MOCK_CLIENT_EXECUTION_MATRIX.csv`. The run artifact is `data/synthetic/mock_client_r1_execution.json`.

Review results are not savings. Twenty-seven candidate codes are shared by more than one review policy, including bariatric, spine, PAP, and residential-treatment codes. In-scope allowed amounts for those policies overlap and are not added together.

A policy title is not its mechanism. Breast reduction medical necessity is configured in its package as `PRIOR_AUTH_UM` with a review rule, so the engine marks it “Review required.” It does not make a medical-necessity determination. MRI, NCD, and LCD stay blocked as unsigned clinical authority.

Continuation comparisons already stored for 281 policies were not treated as execution. Observations were not rewritten. Observation count after the run remains 287.

## Lifecycle and screens

Existing baseline, prediction, observation, verdict, objective, and dashboard records remain available. They are not acceptance evidence that 287 mechanisms executed.

The dashboard API still separates the two financial figures:

- Payment-rule simulation, 6 policies: **−$2.04** per enrolled member-month. Label: observed post-period payment-rule allowed difference. Not measured savings.
- Descriptive continuation comparison, 281 policies: **−$15.78** per enrolled member-month. The label states that overlap is double-counted and that the figure is not a portfolio savings total, payment-rule effect, or intervention effect.

The authenticated policy catalog at `http://127.0.0.1:3255/policies` shows 287 policies, the execution column, and the note that review-only results are not payment changes. Checked journeys: ACL reconstruction shows “Review required”; assistant surgeon payment rules shows “Missing parameter”; policies without codes show “No candidate code.”

What-If at `/whatif` loads and states that it does not calculate the synthetic payer population. No new What-If scenario was run for the 287 policies. Scenario list API returned HTTP 200.

Screenshots: `docs/production/releases/mock_client_r1_browser/`.

## Portability

The same engine accepts a second client configuration without a code change. The regression test supplies a different policy, code `99213`, and a client-configured quantity limit of 3 units. The independent oracle expects an allowed reduction of $60 on that fixture, and the engine matches it. The 278 catalog packages do not contain that parameter, so the catalog quantity policies stay blocked.

A second 500k tenant was not loaded. Portability of the engine is demonstrated. Portability of the full product on a second client dataset is not.

## Staging

Isolated staging deployment did not happen.

Rechecked on 2026-11-06: Azure subscription “Azure subscription 1” (`94a13dda-e607-413d-a0ef-d9501e71e506`) is logged in. `hfleanstg-pg` in `rg-healthforesight-enterprise-staging` is Ready, SKU `Standard_D2s_v3`, storage 32 GB.

A second database large enough for the 500k longitudinal book would consume a large share of that 32 GB disk. Serving it would require new container apps, which are new paid resources, or retargeting `hfleanstg-api` and its workers, which would hide the current lean-staging data. Neither was authorized. No staging database was created. No staging table was written. The frozen December 4 demo was not changed.

Local evidence is not staging acceptance. Celery and Azure workers were not used. The local worker function `uepi_worker.policy_mechanism_execution` ran in process, with one audit row `POLICY_EXECUTION` on the local longitudinal database.

## Tests

`packages/common/tests/test_policy_execution_contract.py` and `apps/api/tests/test_policy_mechanism_worker.py`: 7 passed.

Covered failures: missing codes stay blocked with a null count; unsigned clinical rules stay blocked; a quantity policy without a configured limit stays blocked; a worker exception does not invent a financial result; review execution does not change payment; a second client configuration uses the same engine.

## Production-readiness gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Functional completeness | Fail | 191 policies cannot execute. Review execution does not implement payment, quantity, site-of-care, step therapy, or clinical determination. |
| Policy configurability | Partial | Contracts come from package fields and optional client parameters. Catalog packages have no numeric parameters. |
| Policy execution | Fail | 96 of 287 have a mechanism result. 90 of those are review selection. 6 are prior payment simulations. |
| Calculation integrity | Partial | 90 review policies match the oracle. The 6 payment engines were not recomputed in this run. |
| Lifecycle integrity | Not accepted for this release | Existing predictions and observations remain. They were not used as execution evidence. |
| Dashboard integrity | Pass for separation | −$2.04 and −$15.78 stay separate. Review volume was not added to either figure. |
| Objectives and verdicts | Unchanged | No new favorable verdict was created. An observation is still not an achieved objective. |
| What-If | Not expanded | The screen loads and does not claim the synthetic population result. |
| Data portability | Partial | Engine-level second-client test passed. No second full dataset was run. |
| Worker reliability | Partial | Local worker retry test passed. Staging workers did not run. |
| Deployment acceptance | Fail | No isolated staging deployment. |
| Production configuration | Not accepted | Local API is `development` and still seeds the synthetic demo user. Production combined with a synthetic database URL remains refused by the existing startup guard. That guard was not redeployed. |

## Remaining blockers

1. **191 policy definitions are not executable.** Each needs a versioned client parameter or a real code schedule before the engine can run it. Filling those values without a client configuration would invent policy authority.
2. **90 review results are not economic or clinical execution.** They implement only the configured “review, do not auto-deny” rule.
3. **Isolated staging is blocked on infrastructure approval.** Required decision: authorize either additional database storage and a separate app/worker pair, or an explicit window to use different existing capacity without hiding lean staging or the December 4 demo. No cost was estimated here because no new resource was designed or priced in this run.
4. **Staging workers, schedules, and pipeline runs were not executed.**
5. **The six payment simulations were not re-oracled in this sprint.** Their earlier results remain simulations.
6. **Security and operations enhancements were not started.** Existing login is still required for the new execution summary. That is not a production-operations acceptance.

## Recommendation

Do not demonstrate the 287 policies as executed mechanisms. Demonstrate three classes: 6 payment-rule simulations, 90 review-only selections with no payment change, and 191 blocked definitions. Do not deploy this build for a real client.
