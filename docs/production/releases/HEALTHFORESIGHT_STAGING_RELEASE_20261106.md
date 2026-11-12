# Staging release — 6 November 2026

The existing lean-staging environment was replaced. The December 4 demo and production were not changed. No new paid infrastructure was created.

## Where it is running

| Surface | URL | Revision | Image |
| --- | --- | --- | --- |
| HealthForesight web | https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io | hfleanstg-web--0000009 | healthforesight-web:mock-r1-20261106c |
| Data Voyager web | https://hfleanstg-web-datavoyager.whiteplant-64737337.eastus2.azurecontainerapps.io | hfleanstg-web-datavoyager--0000009 | healthforesight-web:mock-r1-dv-20261106c |
| API | https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io | hfleanstg-api--0000011 | healthforesight-api:mock-r1-20261106b |
| Analytics worker | same resource group | hfleanstg-worker-analytics--0000006 | healthforesight-worker:mock-r1-20261106b |
| Interactive worker | same resource group | hfleanstg-worker-interactive--0000009 | healthforesight-worker:mock-r1-20261106b |

Sign in with `synthetic.local@example.com` / `synthetic-local-only`. API health returned 200. Both workers logged `celery@… ready` against staging Redis.

The web images include `/api/v1` on the baked API URL. An earlier image called the host without that prefix, and the sign-in page showed Not Found.

## Demo isolation

Demo API in `healthforesight-rg` is still `healthforesightacr.azurecr.io/healthforesight-api:dec4-stab-5b587ed`. Staging uses `rg-healthforesight-enterprise-staging` and `hfleanstg-pg.postgres.database.azure.com`. Production was not targeted.

## Backup and capacity

Previous staging database, before replacement: 250 policies, 2,250 observations, 251 baselines, 53,949 claim lines, 80 audit events. Custom dump `/Users/nileshl/Private/hf-staging-backups/hfleanstg-20261106.dump` (4.1 MB) was restored locally to `staging_backup_verify` and those counts matched.

The replacement database is the 500k longitudinal book. Logical size about 5.7 GB on the existing 32 GB server. Storage during restore was about 36 percent. The previous staging database was not kept alongside it.

## Configured-policy check on the live site

Policy: acl reconstruction prior authorization (`4b0b8e40-5b9a-549e-8b0c-b76b2e120fc6`).

| Item | Live value |
| --- | --- |
| Baseline allowed | $829,080.00, 18 monthly points, sum matches the stored total |
| Frozen prediction | $681,855.67. One exposure-scaled total. No monthly prediction line is drawn |
| Observed allowed | $422,792.11, 14 monthly points, sum matches the stored total |
| Verdict | INCONCLUSIVE. No policy endpoint contract is defined |
| Execution | Review required, no auto-deny, no payment change. Not a clinical outcome |
| Chart | Green baseline-allowed line and purple observed-allowed line on the policy overview |

Executive dashboard, same session: payment-rule simulation −$2.04 per enrolled member-month (6 policies) and descriptive continuation −$15.78 (281 policies), kept separate. Utilization is unavailable, not zero. What-If states that it does not calculate the synthetic payer population.

## Catalog execution

287 policies. These are not 287 executed clinical interventions.

| State | Count | Meaning |
| --- | ---: | --- |
| Review only | 90 | Configured review logic matched claims. Financial effect is null |
| Payment simulation | 6 | Prior validated payment-rule simulations. Dollars were not recomputed in this run |
| Awaiting configuration | 44 | The definition names a parameter and does not supply it |
| Blocked | 147 | No candidate code (102), unsigned clinical or coverage authority (43), or no executable rule (2) |

Awaiting configuration, by required field:

| Policies | Missing field | Reason |
| ---: | --- | --- |
| 12 | required_prior_step_codes | MISSING_STEP_THERAPY_PROTOCOL |
| 10 | preferred_place_of_service | MISSING_SITE_OF_CARE_PARAMETER |
| 7 | frequency_limit | MISSING_FREQUENCY_LIMIT |
| 6 | member_cost_share_fraction | MISSING_COST_SHARE_PARAMETER |
| 4 | allowed_reduction_fraction | MISSING_PAYMENT_PARAMETER |
| 2 | quantity_limit_units | MISSING_QUANTITY_LIMIT |
| 1 | edit_pairs | MISSING_CODING_EDIT |
| 1 | product_identifier | MISSING_PRODUCT_IDENTIFIER |
| 1 | episode_allowed_amount | MISSING_EPISODE_PARAMETER |

Only `quantity_limit_units` has an execution engine. Saving one of the other fields does not produce a financial result. No quantity limit, payment factor, clinical criterion, or procedure code was invented. Blocked policies are not counted as executed.

Nine longitudinal baselines (six payment rules and MRI, NCD, LCD) store monthly claim-line counts reconciled to `pre_lines`. They do not store a monthly dollar series, because their stored baseline is a line count rather than allowed dollars.

## Release decisions

1. Staging application functionality: **GO for supported configurations.** The live site shows a configured policy’s baseline, frozen prediction, observation, chart lines, inconclusive verdict, and separated executive figures. Missing utilization and missing monthly predictions stay absent.
2. Mock-client catalog execution: **partial.** 90 review-only, 6 payment simulations, 44 awaiting a client parameter, 147 blocked. Not a 287-policy execution.
3. Functional production readiness: **conditional pass.** A client can run this application without code changes when policies use the supported contract (review with candidate codes and the no-auto-deny rule, the six validated payment keys, or a supplied quantity limit) and canonical claim and enrollment data. Policies that need an unsigned clinical rule or an unimplemented parameter stay blocked in the product. That is not a failure of the whole application, and it is not approval to treat the mock catalog as complete.

Real-client deployment is not approved from this staging run.
