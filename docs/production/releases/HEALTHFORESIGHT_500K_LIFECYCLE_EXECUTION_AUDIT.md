# 500,000-life lifecycle execution audit

Date: 2026-11-06. Local disposable database only. Staging was not loaded, queried, or changed. Azure was not used. The December 4 demo was not changed. No new population was generated.

## Has this dataset been loaded in staging?

No. The 500,000-life rows exist only in local Postgres database `synthetic_payer_500k` on `127.0.0.1:55434`. The writer refuses any URL that is not that local disposable database. The existing lean-staging application and its 2,250 historical observations were not a target of the generator, the integration, or this lifecycle close-out.

The 10,000-life local app is still on `synthetic_payer` and still reports −1.27 and 5,128 claims. The 500,000-life app at http://127.0.0.1:3155 still reports −1.26, 256,428 claims, and 8,986,494.004 member-months.

## What the first local run had actually executed

Before this close-out, the 500,000-life database had baselines and observations, and it did not have a separate prediction or a post-policy event set.

| Stage | Evidence before this close-out | Status |
| --- | --- | --- |
| Policy configuration and scope | 9 policy rows, procedure scope, policy key, operational activation prohibited | EXECUTED |
| Population and exposure | 500,000 reference lives, 8,986,494.004 member-months from stored spans | EXECUTED |
| General baseline | Application baseline, denominator ENROLLMENT | EXECUTED |
| Policy-specific baseline | 9 baselines, line counts matched policy identity | EXECUTED |
| Predicted impact persisted | `policy_predicted_impacts` count was 0 | NOT_IMPLEMENTED |
| Post-policy source events | Claims file is the pre-policy extract. No second event set | NOT_IMPLEMENTED |
| Observation persisted | 9 observations. Each payment observation stored the simulation total directly | EXECUTED_SIMULATION_ONLY |
| Prediction versus observation | No prediction row to compare | NOT_IMPLEMENTED |
| Verdict | 9 stored verdicts INCONCLUSIVE. No `required_endpoints` on any policy | EXECUTED |
| Evidence pack | Read from the observation by the API. `evidence` table count was 0 | READ_TIME_ONLY |
| Objectives health | 9 policies, no contract, status no_data | EXECUTED_NO_CONTRACT |
| Worker, schedule, pipeline | `schedules` 0, `pipeline_runs` 0, `analyses` 0. Nine analytics runs exist only because creating an observation writes one | NOT_VERIFIED |
| Audit history | 9 `RUN_COMPLETED` rows, one per observation. No stage history | NOT_IMPLEMENTED |
| Clinical outcomes | MRI, NCD 220.2, LCD L34425 source lines only, dollars null | NOT_MEASURABLE |

A passing screen was not treated as proof of a stage. Counts above are from `synthetic_payer_500k`.

## What was completed locally

The missing distinction is now stored, and it is labeled as a synthetic scenario. It is not a second period of real utilization.

For each of the six payment policies the application now does four different things:

1. The payment engine total is stored as a prediction in `policy_predicted_impacts`. Method `SYNTHETIC_PAYMENT_ENGINE`. Confidence is null. The standard predicted-impact writer was not used, because that writer adds fabricated provider-compliance shares.
2. The engine's line results are stored in `synthetic_post_policy_events`, source label `SYNTHETIC_POST_POLICY_SCENARIO`. These rows are not inserted into `claims_lines`.
3. The observation's observed allowed amount is the SQL sum of those event rows. That sum does not read the prediction total.
4. `comparisons.vs_predicted` records the gap. Allowed matched within $0.02, and the plan-paid gap is $0.00. The independent oracle matches the same allowed totals.

Claims stayed at 256,428. Member-months stayed 8,986,494.004. The executive figure stayed **−1.26 $ / enrolled member-month**. No endpoint contract was added. All nine verdicts stayed `INCONCLUSIVE`. No clinical dollar outcome was written.

| Policy | Prediction allowed | Event rows summed | Reconciliation | Verdict |
| --- | ---: | ---: | --- | --- |
| MPPR | 12,000,000 | 20,000 | MATCH | INCONCLUSIVE |
| Imaging site of service, hospital 80% | 4,050,000 | 5,000 | MATCH | INCONCLUSIVE |
| PTP | 4,480,400 | 10,000 | MATCH | INCONCLUSIVE |
| Unit cap, demo cap 4 | 852,000 | 5,000 | MATCH | INCONCLUSIVE |
| Therapy | 600,000 | 5,000 | MATCH | INCONCLUSIVE |
| Infusion, per claim | 16,000,000 | 5,000 | MATCH | INCONCLUSIVE |
| Lumbar MRI prior authorization | none | 0 outcome rows; 10,000 source lines remain | NOT_MEASURABLE | INCONCLUSIVE |
| NCD 220.2 | none | 0 outcome rows; 5,000 source lines remain | NOT_MEASURABLE | INCONCLUSIVE |
| LCD L34425 | none | 0 outcome rows; 5,000 source lines remain | NOT_MEASURABLE | INCONCLUSIVE |

Machine-readable result: `data/synthetic/lifecycle_500000.json`. Unit tests: `apps/api/tests/synthetic/test_synthetic_lifecycle.py`. Entry point: `scripts/synthetic_payer_lifecycle.py`, which calls `persist_synthetic_lifecycle`.

Each policy now has one changelog row and 12 lifecycle audit rows (`audit_events.action = LIFECYCLE_STAGE`). That is an audit history of this close-out. It is not a policy status machine moving through draft, approval, and activation. Policy status stayed ACTIVE, and operational activation stayed prohibited.

## Lifecycle matrix after the local close-out

| Stage | Six payment policies | MRI, NCD 220.2, LCD L34425 |
| --- | --- | --- |
| 1. Configuration and applicability | EXECUTED | EXECUTED |
| 2. Population scope | EXECUTED. Cohort is the generator index rule, not a clinical eligibility engine | EXECUTED_SOURCE_EVENTS_ONLY |
| 3. General baseline | EXECUTED | EXECUTED |
| 4. Policy baseline | EXECUTED | EXECUTED |
| 5. Predicted impact | EXECUTED_SIMULATION_ONLY. Engine total, persisted | NOT_MEASURABLE. Null dollars |
| 6. Post-policy events | EXECUTED_SIMULATION_ONLY. Separate scenario table, not a new claims ingestion | NOT_MEASURABLE. No outcome rows |
| 7. Observation | EXECUTED. SQL sum of the scenario events | NOT_MEASURABLE |
| 8. Prediction versus observation | EXECUTED_SIMULATION_ONLY. Allowed match, oracle match | NOT_MEASURABLE |
| 9. Verdict | EXECUTED. INCONCLUSIVE because no contract exists | EXECUTED. INCONCLUSIVE |
| 10. Evidence | READ_TIME_PACK_ONLY. The pack is built when the API is called. The `evidence` table is still empty | READ_TIME_PACK_ONLY |
| 11. Objectives health | EXECUTED_NO_CONTRACT. Nine no-data rows | EXECUTED_NO_CONTRACT |
| 12. Lifecycle history | EXECUTED as audit and changelog rows. No worker state transition | EXECUTED as audit rows recording the block |
| Scheduled workers and pipelines | NOT_VERIFIED. None ran | NOT_VERIFIED |

## What is still not a full lifecycle

The synthetic extract has one pre-policy service day per using member. There is no later claims period produced by an independent process. The post-policy rows are the payment rule applied to those same lines and stored beside them. That is enough to prove the application can keep a prediction, an event sum, and a reconciliation apart. It is not evidence of realized post-policy utilization, and it is not a medical and pharmacy book.

These items are still open, on purpose:

- No endpoint contract. A directional contract was not added, because a decrease contract would turn these matched simulations into ON_TRACK without a declared payer endpoint.
- Verdicts remain inconclusive. Zero verdicts were forced.
- Evidence packs are generated at read time. They are not stored evidence records.
- No schedule, pipeline, or staging worker executed this lifecycle.
- MRI prior authorization, NCD 220.2, and LCD L34425 stay blocked at the outcome stages. Their source lines are still visible.
- Infusion codeset is not closed. Codes remain candidates. Operational activation remains prohibited.

## Staging package

Do not run this package. It describes the isolated database that would be required. It does not connect to lean staging.

| Item | Intended value | Current state |
| --- | --- | --- |
| Target | A new database whose name contains `synthetic_payer_500k` and whose host is not the existing lean-staging database | Not created |
| Existing lean staging | `rg-healthforesight-enterprise-staging` and the current staging API, web, and workers | Must stay unchanged, including the 2,250 observations and the 250 execution blocks |
| December 4 demo | `healthforesight-api` and the frozen demo database | Out of scope |
| Schema | Current application schema, plus `synthetic_post_policy_events` created by `persist_synthetic_lifecycle` | Present only on local `synthetic_payer_500k` |
| Data movement | Restore or reload from the local database. Do not copy rows into the existing staging tables | Not started |
| Identity | Source system `SYNTHETIC_PAYER_V1`, scenario label `SYNTHETIC_POST_POLICY_SCENARIO`, seed `20261106`, generator `synthetic-payer-v1` | Local only |
| Workers | Staging worker processes would have to be pointed at the new database only | Not configured |
| Performance seen locally | Lifecycle close-out 18.5 seconds. Dashboard 0.03 seconds. Largest what-if 0.62 seconds. Database about 4.2 GB before the event table | Not a staging measurement |
| Rollback | Drop only the new database. Do not drop or update the existing staging database | Not applicable until a new database exists |

Proof this local close-out left staging alone: the script calls `assert_disposable_database`, which rejects any URL without port `55434` and the `synthetic_payer` name, and rejects `azure` and `database.windows.net`. The run printed `database: synthetic_payer_500k`.

## Staging steps that need a separate authorization

None of the following has been run. Approval would have to name the new database and say that the existing lean-staging database and the December 4 demo stay untouched.

1. Create a new empty database that is not the current lean-staging database and not the demo database.
2. Apply the application schema there, including `synthetic_post_policy_events`.
3. Load the local 500,000-life data into that new database only.
4. Point a staging API and worker process at that database only, without changing the current staging apps' connection.
5. Run `persist_synthetic_lifecycle` there, or confirm the loaded rows already contain the nine predictions, 50,000 scenario events, and nine reconciled observations.
6. Run the signed-in browser journeys against that API.
7. Reconcile with the independent oracle.
8. If the run fails, drop only the new database.

Pass criteria for that future run:

- Database name is the new database, and a count of the existing staging observations is still 2,250.
- Covered lives 500,000. Member-months 8,986,494.004. Claim rows 256,428. Pharmacy rows 0.
- Six payment predictions match the event-row sums and the oracle within $0.02. Plan paid and allowed stay separate.
- MRI, NCD 220.2, and LCD L34425 have null outcomes and `NOT_MEASURABLE` reconciliation.
- Nine verdicts are INCONCLUSIVE unless an endpoint contract already exists. This dataset has none. A run that reports ON_TRACK fails.
- Executive figure is about −1.26 $ / enrolled member-month, labeled as a simulated allowed difference, not savings.
- No schedule or worker attached to the existing staging database writes these rows.

Fail and stop if any check above fails, if a query targets the existing staging database, or if the run would replace the December 4 demo.

## Recommendation

The six payment policies now have a traceable synthetic path from baseline, to a stored prediction, to scenario events, to an observation sum, to reconciliation, to an inconclusive verdict. The three clinical policies remain explicitly blocked.

That path has run in the local application database. It has not run through staging workers. Staging does not contain this population.

Do not import it until there is a separate approval for a new database. Do not call the scenario events a complete payer lifecycle.
