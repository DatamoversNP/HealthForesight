# HealthForesight 500,000-life longitudinal acceptance

Recommendation: **PARTIAL**

The six payment policies now have a local longitudinal lifecycle on an independent post-policy claim book. Predictions were frozen before those post-policy claims existed, observations were calculated from the post-policy claims, and the prediction-versus-observation gaps were stored as measured differences. The three clinical and coverage policies remain not measurable. Staging was not loaded.

This is synthetic test data. It is not a commercial utilization benchmark, a CMS adjudication, or measured payer savings.

## Environment

| Item | Value |
| --- | --- |
| Local database | `synthetic_payer_500k_longitudinal` on `127.0.0.1:55434` |
| Database size | 4.8 GB |
| Generator | `synthetic-longitudinal-v1`, seed `20261106` |
| Member identities | Same 500,000 identities as the reference population |
| Reference database | `synthetic_payer_500k` was not written. It still has 256,428 claim lines and 9 observations |
| Local API | `http://127.0.0.1:8093` |
| Local UI | `http://127.0.0.1:3255` |
| Sign-in | `synthetic.local@example.com` / `synthetic-local-only` |
| Policy catalog | v1.2 packages under `docs/demo/bcbs-nc/policy_definitions/v1.2/catalog` |
| Staging | Not loaded |
| December 4 demo | Not changed |
| Existing lean-staging observations | Not changed |

The 10,000-life app on ports 8091 and 3055, and the reference 500,000-life app on ports 8092 and 3155, were left running.

## Staging blocker

An isolated staging run cannot be done with the current authorization.

- Creating a second database server or container app would be new paid Azure infrastructure.
- Pointing the existing `hfleanstg` API and workers at this dataset would replace the application that serves the current lean-staging observations.
- Loading this dataset into the existing lean-staging database would mix it with those historical observations.

No Azure resource was created and no staging database was changed. Rollback of staging is not required because staging was not touched. The local longitudinal database can be dropped; it is disposable and is not the reference database.

## Time windows

The effective date **2025-07-01** is a synthetic hypothetical label for this test. It is not policy authority.

| Window | Dates | Use |
| --- | --- | --- |
| Historical baseline and prediction inputs | 2024-01-01 through 2025-06-30 | Pre-policy claims only |
| Prediction freeze | Recorded before any post-policy claim was generated | Cutoff 2025-06-30. The freeze file recorded `post_claims_present: 0` |
| Post-policy observation | 2025-07-01 through 2026-09-30 | A separate random stream |

Pre-period claims use random stream `seed + 17`. Post-period claims use `seed + 104729`. The post-period generator does not take a prediction, a scenario total, or a payment-engine result. Post-period occurrence rates are fixed synthetic assumptions (0.55 to 0.91 by policy). They are not the payment-rule percentages, and the post-period book is not the baseline multiplied by a predicted change.

Enrollment exposure is calculated separately for each window. Pre-period enrolled member-months are 4,931,065.314. Post-period enrolled member-months are 4,055,428.691. Partial months use the existing `SYNTHETIC_PARTIAL_MONTH_V1` convention.

## Population and source records

| Measure | Count or amount |
| --- | --- |
| Members | 500,000 |
| Enrollment rows | 9,479,433 |
| Pre-policy claim lines | 269,825 |
| Post-policy claim lines | 295,036 |
| Pharmacy lines | 111,527 |
| Professional lines | 234,412 |
| Emergency lines | 46,266 |
| Outpatient lines | 31,064 |
| Inpatient lines | 20,520 |
| Pre-period allowed | $157,419,700 |
| Pre-period plan paid | $125,935,760 |
| Accounting breaks (`allowed` not equal to plan paid plus member share, beyond $0.02) | 0 |

Service dates do not cross the cutoff: 269,825 lines are before 2025-07-01 and 295,036 are on or after that date.

The book is intentionally low intensity so the run can finish. It includes professional, outpatient, inpatient, emergency, and pharmacy events, plus the policy-specific services. It does not claim the frequency of a commercial payer. Pharmacy rows use the synthetic token `SYN-NDC-0001`. They are not a formulary.

## Catalog

287 policies are stored.

- 9 demonstration policies have the existing synthetic execution status.
- 278 v1.2 catalog packages were loaded as definitions only. Their execution status is `NOT_IMPLEMENTED`. No codes, clinical criteria, endpoint contracts, or outcome engines were invented for them.

## Nine-policy lifecycle

Payment arithmetic was checked with the independent oracle. All six payment observations matched the oracle. None of the differences below were forced to zero.

| Policy | Pre lines | Frozen allowed impact | Post lines | Observed allowed impact | Difference | Oracle | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Multiple procedure payment reduction | 20,000 | $2,000,000 | 12,598 | $1,272,276.51 | $-727,723.49 | Match | INCONCLUSIVE |
| Imaging site of service | 5,000 | $450,000 | 4,583 | $415,811.82 | $-34,188.18 | Match | INCONCLUSIVE |
| Procedure-to-procedure edit | 10,000 | $2,624,300 | 7,686 | $2,036,229.68 | $-588,070.32 | Match | INCONCLUSIVE |
| Unit cap (demo cap 4, not a CMS MUE) | 5,000 | $500,000 | 2,734 | $198,524.55 | $-301,475.45 | Match | INCONCLUSIVE |
| Outpatient therapy coverage | 5,000 | $500,000 | 4,164 | $263,891.84 | $-236,108.16 | Match | INCONCLUSIVE |
| Infusion site of care | 5,000 | $6,757,200 | 3,578 | $4,068,758.12 | $-2,688,441.88 | Match | INCONCLUSIVE |
| Lumbar MRI prior authorization | 10,000 | Not calculated | 8,788 | Not calculated | — | Not applicable | INCONCLUSIVE, NOT_MEASURABLE |
| NCD 220.2 | 5,000 | Not calculated | 3,241 | Not calculated | — | Not applicable | INCONCLUSIVE, NOT_MEASURABLE |
| LCD L34425 | 5,000 | Not calculated | 3,700 | Not calculated | — | Not applicable | INCONCLUSIVE, NOT_MEASURABLE |

A positive impact means the payment rule reduced allowed dollars on that period's own claims. The difference is the post-period impact minus the frozen pre-period impact. The post-period volume and prices were generated independently, so the impacts are not expected to match.

The unit-cap prediction was corrected before any observation was stored. The first pass left a null `allowed_per_unit` key on the claim, and the payment function treated the whole line amount as the per-unit amount. The corrected prediction uses the same pre-period lines only. Its oracle check then matched. The other five payment predictions matched the oracle on the first freeze.

No endpoint contract exists for these policies. Verdicts stay INCONCLUSIVE. No contract was added to produce ON_TRACK, AT_RISK, or BACKFIRE. Confidence is null. Utilization change is unavailable, not zero.

MRI prior authorization, NCD 220.2, and LCD L34425 have source claims in both periods. No clinical decision, coverage determination, or savings amount was created.

## What the application stored

| Stage | Result |
| --- | --- |
| Ingestion | Enrollment, providers, and claims loaded into the application tables |
| Baseline | 1 general pre-period baseline and 9 policy baselines, window ending 2025-06-30 |
| Prediction | 6 rows, method `SYNTHETIC_PAYMENT_ENGINE_PRE_FREEZE`, cutoff 2025-06-30 |
| Observation | 9 rows calculated from post-period claims. `copied_from_prediction` is false |
| Reconciliation | `MEASURED_DIFFERENCE` for the six payment policies. `NOT_MEASURABLE` for the three clinical policies |
| Verdict | 9 INCONCLUSIVE, rule `v1.1-endpoints` |
| Audit | 9 `LIFECYCLE_STAGE` rows written by `synthetic_payer_longitudinal.py` |
| Pipeline runs | 0 |
| Schedules | 0 |
| Analyses | 0 |

The audit rows record the local script's call to the application baseline, prediction, and observation services. A staging worker process was not started, and no schedule ran. Those stages are not claimed as worker execution.

## Screen and API check

Signed in at `http://127.0.0.1:3255`. Screenshots are in `docs/production/releases/longitudinal_500k_browser/`.

The executive dashboard shows:

- Observed post-period allowed difference **$-2.04 per enrolled member-month**
- The label states that the frozen prediction is stored separately and that the figure is not measured savings
- Utilization **Unavailable**
- 287 active policies
- Pre-policy baseline: 54.7 claims per 1,000 member-months, $25.54 paid per enrolled member-month, 4,931,065.314 member-months

`GET /api/v1/dashboard/summary` returned the same $-2.04, the same unit, and utilization status UNAVAILABLE in 0.06 seconds. The $-2.04 is the sum of the six post-period allowed changes divided by the post-period enrolled member-months. It is not the frozen prediction.

Predicted Impacts shows the six frozen payment predictions, with utilization and confidence unavailable. Policy Verdicts shows INCONCLUSIVE and the per-member-month amounts. Observation Analysis shows nine observations, including the three clinical policies as inconclusive. The policy workspace for multiple procedure payment reduction identifies the policy as a synthetic illustration and says operational activation is prohibited.

The mobile executive view also shows the observed post-period allowed difference.

## Performance

| Step | Time |
| --- | --- |
| Schema | 1.2 seconds |
| Pre-period claim generation | 4.9 seconds from start |
| Enrollment and pre-period load | 327 seconds from start |
| Baseline and prediction freeze | 376 seconds from start |
| Post-period claim generation | 379 seconds from start |
| Observation, catalog load, and report | 18 seconds |
| Dashboard summary API | 0.06 seconds |
| Signed-in browser pass | 50 seconds |

Peak memory for the load process was not sampled because that process exited on a missing observation timestamp before the sample line. The observation was then stored by a second process. Database size after the load is 4.8 GB.

## Remaining limits

- Staging execution is blocked for the reason above.
- No deployed worker or schedule ran.
- The 278 catalog policies have definitions only. They do not have baseline, prediction, or observation engines.
- The three clinical and coverage policies have source events and explicit not-measurable outcomes. They do not have clinical decision engines.
- There is no claim-line screen that opens one historical claim, its baseline inclusion, the frozen prediction, and a post-policy claim on one page. Those records are in the database and are linked by policy, period, and observation comparison.
- The generating rates are documented synthetic assumptions. They are not evidence of commercial payer realism.
