# Production integrity audit

Recommendation: **NOT READY**

Populated lifecycle records for 287 policies do not make HealthForesight production-ready. Six payment policies have a synthetic payment-rule simulation. The other 281 have a historical-rate continuation comparison. Neither class is a real payer outcome.

This audit traced the customer-facing numbers that are on screen now, removed verified substitutions of missing data, and left the unsupported policy mechanisms unbuilt.

## What the screens are actually showing

The local longitudinal app at `http://127.0.0.1:3255` reads `GET /api/v1/dashboard/summary`. That endpoint sums stored observations. It does not contain the numbers −2.04 or −15.78 in source code.

| Screen figure | Class | Source |
| --- | --- | --- |
| −$2.04 per enrolled member-month | Payment-rule simulation for 6 policies | Sum of observation `cost_change` values whose kind is `observed_post_period_allowed_difference_per_enrolled_member_month`, divided through the shared post-period member-months already stored on each row |
| −$15.78 per enrolled member-month | Descriptive continuation comparison for 281 policies | Same shape of sum, kept in a separate field. The label states that overlap is double-counted and that this is not savings |
| 287 active policies | Catalog count | `COUNT` of policy rows for the tenant |
| 122 without a candidate code | Applicability limit | Policy metadata `applicability_evidence = NO_CANDIDATE_CODE_IN_PACKAGE` |
| Utilization unavailable | Missing measure | No utilization change is stored. It is not shown as zero |
| 0 of 6 objectives met | Objectives | An objective is met only by a supported ON_TRACK verdict. A stored observation does not count |
| 287 inconclusive verdicts | Verdict engine `v1.1-endpoints` | No required endpoint contract is stored, so the engine returns INCONCLUSIVE |

Prediction, observation, and simulation stay different:

- A prediction is the frozen pre-period calculation.
- An observation is the post-period measurement from stored claim lines.
- A simulation is the payment rule applied to those lines. For the six policies, the observation is that simulation applied to post-policy synthetic claims. It is not proof that a payer paid a different amount.

## Hardcoding that was on a production path

These were corrected. Missing inputs now stay missing.

| Location | What it did | Correction |
| --- | --- | --- |
| `prediction_enhancement_service.py` | Used confidence 0.7, utilization 50 per 1,000, and $50 PMPM when the baseline or confidence was absent | Returns `UNAVAILABLE` for confidence intervals and ramp-up. Confidence stays null |
| `routers/observations.py` analysis rebuild | Wrote p-value 0.05 or 0.10, a confidence interval of ±20 percent, trust score 0.85, and member-months as member count times 6 | Uncertainty fields are null. Method checks are not assessed. A zero pre-period rate does not become 0 percent or 999 percent |
| `routers/analyses.py` legacy trust panel | Filled method confidence 70 or 90, data quality 85, and coverage 0.8 | Those components are null and marked not measured. An empty analysis no longer returns confidence 0 |
| `main.py` startup | Created the demo tenant user on every start | Production does not seed that user. Production pointed at a synthetic database URL skips demo startup |

Regression: `apps/api/tests/test_production_integrity_no_fabricated_results.py`. It fails if a missing baseline becomes a stand-in rate, and it fails if a continuation comparison is added into the payment-rule total. That test and the objectives stability tests passed.

## What is still not a governed production path

These remain. They were not replaced with another constant.

- `baseline_segmentation_from_claims.enrich_predicted_impact_for_ui_row` still builds provider-archetype shares from fixed percentages when a prediction is enriched for the UI. The longitudinal load does not call it. A later “generate prediction” action can.
- Several scripts under `apps/api/scripts/` still write trust score 0.85 when they complete old analyses. They are not the API request path. They must not be run against production.
- The policy-owner dashboard can build in-flight and approval lists in the browser when the persona API payload is empty. Those lists are derived from policy status, not from a financial formula, but they are not a governed server calculation.
- Observation detail still uses a null cost change as a color decision in a few places. The amount itself is shown as N/A when absent.
- The Policy Intelligence Coverage table is a static manifest. Its baseline, forecast, and observed columns are blank. It is not the live observation count.
- There is no production feature flag that disables the six synthetic payment engines. They run when their code is called. Production isolation now refuses the demo seed if `ENVIRONMENT` is production and `DATABASE_URL` points at a synthetic database. It does not, by itself, prove the deployed API is pointed at a real payer database.

## Policy execution matrix

| Group | Count | Baseline | Frozen prediction | Post-policy observation | Mechanism | Verdict |
| --- | ---: | --- | --- | --- | --- | --- |
| Payment-rule simulation | 6 | Yes | Payment rule | Rule applied to synthetic post-policy claims | Implemented for synthetic payment arithmetic | INCONCLUSIVE |
| Continuation comparison with candidate codes | 159 | Yes | Historical allowed rate extended by enrollment | Independent synthetic claims | Not implemented | INCONCLUSIVE |
| Continuation comparison without a candidate code | 122 | Yes | Same continuation | Policy-tagged claims, empty procedure code | Not implemented. Eligibility is not verified | INCONCLUSIVE |
| Clinical outcome engine | 0 of 3 | Source claims exist | Continuation only | Source claims exist | Not implemented | INCONCLUSIVE |

The 281 continuation policies must not be described as mechanism-executed.

## Aggregation rules now in force

- Payment-rule simulations and continuation comparisons are separate API fields and separate executive cards.
- They are not added into one portfolio total.
- The continuation sum divides each policy by the same enrolled member-months and then adds the rates. A member in more than one policy is counted more than once. The screen says so.
- Paid and allowed stay separate in the baseline. The general baseline card shows paid dollars per enrolled member-month.
- Missing utilization stays unavailable.
- Objectives met is 0. Presence of an observation is not an achieved objective.

## Staging and production

No staging database was changed. No production deploy was made. The December 4 demo was not changed.

Staging remains blocked for this dataset: serving it would require new container apps or retargeting the existing lean-staging apps. The existing staging server is 32 GB. Neither option was taken.

## Production-readiness blockers

1. Only six policy mechanisms exist, and they are synthetic payment simulations.
2. 281 policies have no mechanism. 122 of them have no verified procedure code.
3. No approved endpoint contracts exist, so every verdict is inconclusive.
4. Objectives have no approved measurable definitions beyond the verdict rule.
5. Evidence packs are not generated from these lifecycle rows. The coverage manifest is not connected to them.
6. No staging worker has executed this lifecycle. Local audit rows were written by scripts.
7. Demo analysis scripts can still stamp a confidence of 0.85 if someone runs them.
8. Prediction generation can still attach illustrative provider and patient shares through the UI enrichment helper.
