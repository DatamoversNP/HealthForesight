# Gate A on lean staging

Date: 2026-11-06. Code: `ec3007f` on `measurement-integrity-gate-a`.

Lean staging is running this commit. The December 4 demo App Service `healthforesight-api` is still `healthforesightacr.azurecr.io/healthforesight-api:dec4-stab-5b587ed`. No staging rows were rewritten and no new Azure resource was created.

## Images now on the existing staging apps

| App | Image |
| --- | --- |
| `hfleanstg-api` | `healthforesightacr.azurecr.io/healthforesight-api:gate-a-ec3007f` |
| `hfleanstg-worker-interactive` | `healthforesightacr.azurecr.io/healthforesight-worker:gate-a-ec3007f` |
| `hfleanstg-worker-analytics` | `healthforesightacr.azurecr.io/healthforesight-worker:gate-a-ec3007f` |
| `hfleanstg-web` | `healthforesightacr.azurecr.io/healthforesight-web:gate-a-ec3007f` |
| `hfleanstg-web-datavoyager` | `healthforesightacr.azurecr.io/healthforesight-web:gate-a-dv-ec3007f` |

Web: https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io/
API: https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/

## API evidence

`/api/v1/ready` returned ready and connected.

`/api/v1/policy-verdicts` returned 250 policies.

- All 250 rows include `historical_verdict_status`.
- All 250 set `verdict_is_recomputed` true.
- All 250 have a screen verdict that differs from the stored status.
- Observed pairs include screen `INCONCLUSIVE` with stored `BACKFIRE`, and screen `INCONCLUSIVE` with stored `AT_RISK`.
- `confidence_pct` is null on those rows.
- `denominator_basis` is null on the sampled stored observations, so the screen must fail closed rather than call the figure enrolled PMPM.

`/api/v1/dashboard/summary` general baseline:

- `paid_pmpm` 2426.17, `allowed_pmpm` 2426.17, `cost_pmpm` 2426.17
- `cost_pmpm_meaning` `PAID`
- `denominator_basis` `CLAIMANT_MONTHS`
- `enrolled_rate_status` `NOT_MEASURABLE`
- `utilization_per_1k` 1362.83

Paid and allowed are separate response fields. On this stored general baseline the two dollar amounts are equal. The cost field is labeled paid, and the enrolled-rate status is not measurable.

## Web bundle

The live staging bundle `/assets/index-BsnZpBVV.js` contains “Stored status”, “Screen value”, and “not enrolled”. It does not contain `allowed_pmpm || 0` or `Cost impact (PMPM)`. It calls the lean staging API.

A signed-in browser pass of the verdict and what-if screens was not completed in this session.

## Tests before the image build

- `apps/web` vitest `whatIfMultiPolicy.test.ts`: 3 passed. A missing allowed impact stays null. An explicit zero still sums.
- Gate A pytest set: 28 passed, including the summary-route contract test and the what-if source test.

## Still open

- Staging observations do not yet carry `denominator_basis`. The labels fail closed until a new calculation writes that field. Historical rows were not backfilled.
- Payment engines still turn a missing allowed amount into zero inside `apply_mppr`, `apply_sos`, and the expansion fixture functions. That is outside this image’s what-if aggregator fix.
- Unit-cap dispatch by policy name still falls through to utilization elasticity unless the mechanism is stamped. See `NINE_POLICY_EXECUTION_AND_10K_PILOT_PLAN.md`.
- The 10,000-life pilot and the 500,000-life dataset are not started.
