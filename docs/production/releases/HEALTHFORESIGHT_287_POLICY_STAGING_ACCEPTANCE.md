# 287-policy staging acceptance

Recommendation: **PARTIAL**

287 policies have local measurement records. Six have a payment-rule mechanism. The other 281 have a historical-rate continuation comparison. Those are not the same thing, and they are not presented as one portfolio savings total.

Staging was not loaded. No staging worker ran.

## Result classes

| Class | Policies | What the prediction is | Mechanism executed |
| --- | ---: | --- | --- |
| `MECHANISM_SIMULATION` | 6 | Validated payment rule on pre-policy claims, frozen before post-policy claims | Yes, synthetic payment simulation |
| `CONTINUATION_COMPARISON` | 281 | Pre-period allowed per enrolled member-month, extended by post-period enrollment | No |
| Of the 281, no candidate procedure code | 122 | Same continuation comparison. Procedure code is empty. Eligibility is not verified | No |
| Clinical outcome engine | 0 of 3 | MRI prior authorization, NCD 220.2, and LCD L34425 have source claims and a continuation comparison only | No |

All 287 verdicts are **INCONCLUSIVE**. No endpoint contract exists. An inconclusive verdict means the verdict engine refused to score effectiveness. It does not mean effectiveness was validated.

The six payment policies are multiple-procedure payment reduction, imaging site of service, procedure-to-procedure edit, the demo unit cap, outpatient therapy, and infusion site of care.

## Local lifecycle evidence

Database: `synthetic_payer_500k_longitudinal` on `127.0.0.1:55434`. The reference database `synthetic_payer_500k` still has 256,428 claim lines. The December 4 demo and the existing lean-staging database were not changed.

| Stage | 6 payment policies | 281 continuation policies |
| --- | --- | --- |
| Historical baseline | Stored | Stored |
| Prediction frozen before post-policy claims | Payment-rule amounts | Continuation amounts. Catalog post-policy claims were generated after the freeze file was written |
| Independent post-policy claims | Yes | Yes. 122 policies have no procedure code |
| Observation from those claims | Yes | Yes |
| Measured difference, not forced to zero | Yes | Yes, 281 nonzero differences |
| Verdict | INCONCLUSIVE | INCONCLUSIVE |
| Audit row | Yes, written by the local script | Yes, written by the local script |
| Application worker or schedule | Not run | Not run |

Pipeline runs: 0. Schedules: 0. The audit rows record the local script. They are not staging worker logs.

## Dashboard and objectives

Signed-in local app: `http://127.0.0.1:3255`. API: `http://127.0.0.1:8093`.

The executive dashboard shows two figures and states that they are not added together:

- Payment-rule simulation, 6 policies: **−$2.04 per enrolled member-month**. This is the sum of the six payment-rule allowed differences divided by post-period enrolled member-months. It is not measured savings.
- Descriptive continuation comparison, 281 policies: **−$15.78 per enrolled member-month**. Each policy contributes its observed post-period allowed minus its frozen continuation, divided by the same shared member-months. Those 281 values are then summed. Members and claims can match more than one policy, so this sum double-counts overlap. It is not a portfolio savings total and not an intervention effect.
- The screen states that 122 continuation policies have no candidate procedure code, so eligibility is not verified.
- Utilization remains unavailable.

`GET /api/v1/dashboard/summary` returned the same split: payment −2.04 across 6 observations, continuation −15.78 across 281, and `missing_applicability_count` 122.

Objectives health reports **0 of 6 objectives met**. The page states that a stored forecast or observation is not an achieved objective. Objective C’s text says 287 policies have an observation and that an observation is not an achieved objective. On track: 0. At risk: 0.

The Policy Intelligence Coverage table on that page is a separate catalog manifest. Its baseline, forecast, and observed columns are still blank. It was not rewritten to look complete.

What-if was not run.

Screenshots: `docs/production/releases/longitudinal_500k_browser/executive-separated.png` and `objectives-not-met.png`.

## Staging

Azure sign-in is present for subscription `Azure subscription 1`. The existing server `hfleanstg-pg` in `rg-healthforesight-enterprise-staging` is Ready, PostgreSQL 15, SKU `Standard_D2s_v3`, storage **32 GB**.

Staging execution stopped before any change:

- A separate application configuration would require new container apps, which are new paid infrastructure, or retargeting `hfleanstg-api` and the existing workers, which would hide the current lean-staging observations.
- Creating a second database on the 32 GB server would consume a large share of the only staging disk and still could not be served without that new app or that retarget.
- No database was created. No staging table was written. No staging worker or schedule was started.

Browser acceptance against staging was not run because there is no isolated staging application. The browser evidence above is the local longitudinal app.

## What is not complete

- 281 policy mechanisms are not executed. Their predictions are continuation forecasts.
- 122 policies do not have verified procedure-code applicability.
- MRI prior authorization, NCD 220.2, and LCD L34425 have no clinical outcome engine.
- No staging worker, scheduler, or staging browser pass has run.
- The coverage manifest on Objectives Health is not connected to these lifecycle rows.
