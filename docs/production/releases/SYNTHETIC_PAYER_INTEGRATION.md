# Synthetic payer integration

Date: 2026-11-06. Local disposable database only. No staging rows, no December 4 demo, no Azure, no PHI.

Every dollar below is a synthetic illustration. It is not real-world savings, CMS adjudication, clinical certification, or a causal effect.

The application is running against that database at http://127.0.0.1:3055. Local login: `synthetic.local@example.com` / `synthetic-local-only`.

## 1. Population realism

The exposure figure reconciles.

| Check | Result |
| --- | --- |
| Members enrolled on 2025-07-01 | 10,000 |
| Coverage window | 2024-01-01 inclusive through 2026-10-01 exclusive (33 calendar months) |
| Convention | `SYNTHETIC_PARTIAL_MONTH_V1`: half-open spans, enrolled days divided by the days in that month |
| Mean enrolled days | 547.09 |
| Member-months from an independent day walk, from the month rows, and from the database | 179,817.163 |
| Member-months per reference member | 17.982 |

179,817 member-months is 17.982 months of exposure per member, not 33 months and not a flat 15. Coverage starts anywhere from January 2024 through the reference date and ends 45 to 450 days after 1 July 2025. The database summer uses the stored start and end dates, plus `GAP_DAYS` when two spans touch one month. It matches the day walk to six decimals. The general baseline stored by the application uses the same 179,817.163 and `denominator_basis = ENROLLMENT`.

The claim file is a policy-specific extract plus one background office visit. It is not a comprehensive multi-year medical and pharmacy dataset.

| Fact | 10,000 lives |
| --- | ---: |
| Claim rows | 5,128 |
| Active rows | 4,300 |
| Members with no claims | 6,000 (60 percent, by the index rule) |
| Lines per member who has a claim | 1.28 |
| Pharmacy rows | 0 |

No distribution in the generator is taken from a cited commercial benchmark. The cohort rule, the one-service-day design, the fixture-scale prices, the 20 percent coinsurance, and the partial-month convention are synthetic assumptions. Claim volume was not increased to look busier.

## 2. Application database

Disposable Postgres is `hf-synthetic-payer` on `127.0.0.1:55434`, database `synthetic_payer`. The loader refuses any other host or database name.

Loaded through the application repositories, then calculated by the application:

| Table | Rows |
| --- | ---: |
| Claims | 5,128 |
| Enrollment month spans | 189,608 |
| Providers | 40 |
| Policies | 9 |
| Baselines | 10 (1 general, 9 policy) |
| Observations | 9 |

Oracle outputs were not copied into those tables. Baselines and observations are the database aggregates and the payment-engine results. The canonical claim table has no modifier, PTP role, site, line status, or unit-necessity column, so those attributes ride in `record_hash` and are read back before the engines run.

Where enrollment rows exist, baseline exposure is the partial-month sum. Where they do not, the previous claimant-count times calendar-months path is unchanged. A blocked remediation envelope returns `NOT_MEASURABLE` instead of a whole-book baseline.

## 3. Nine policies

Operational activation stays prohibited. Codes stay `CANDIDATE_NOT_APPROVED`. No endpoint contract is stored, so every verdict is `INCONCLUSIVE`.

| Policy | What ran | Active lines | Application result | Verdict |
| --- | --- | ---: | --- | --- |
| MPPR | Payment engine, secondary 50 percent | 400 | Payer pays $40,000 less on allowed dollars | INCONCLUSIVE |
| Imaging site of service | Engine at 80 percent of hospital allowed | 100 | $9,000 less. Neutral scenario $0. Adverse scenario −$4,500 | INCONCLUSIVE |
| PTP | Engine | 200 | $32,000 less | INCONCLUSIVE |
| Unit cap | Engine, demo cap 4, not a CMS MUE | 100 | $3,800 less | INCONCLUSIVE |
| Therapy | Engine, pay medically necessary units | 100 | $8,000 less | INCONCLUSIVE |
| Infusion site | Engine, per claim. Codeset still not closed | 100 | $135,000 less | INCONCLUSIVE |
| Lumbar MRI prior authorization | Source events only | 200 | No outcome | INCONCLUSIVE |
| NCD 220.2 | Source events only | 100 | No outcome | INCONCLUSIVE |
| LCD L34425 | Source events only | 100 | No outcome | INCONCLUSIVE |

Plan paid is 80 percent of allowed because of the synthetic coinsurance. The payment engines score allowed dollars, which is the fixture convention. Those two amounts are both stored and are not substituted for each other.

A CPT-only baseline over-counts where codes overlap: 72148 is both imaging site of service and lumbar MRI, 70551 is both PTP and NCD 220.2, and 97110 is both the unit cap and therapy. The stored policy baseline is filtered by the synthetic policy key. The CPT-only count is kept beside it and is not the number on the verdict screen.

## 4. Independent reconciliation

The oracle does not call the engines. On the lines read back from the database, baseline allowed, post-policy allowed, and payment impact match within $0.02 for all six payment runs, including the neutral and adverse site-of-service scenarios.

The same match holds on the 100,000-life database. Clinical policies have a null payment impact on both sides.

Enrollment member-months in the general baseline equal the independent day walk.

## 5. API and browser

API timings on the 10,000-life database, after login:

| Call | Time | Result |
| --- | ---: | --- |
| Policies | 0.02 s | 9 policies |
| Dashboard summary | 0.04 s | Cost −1.27 Σ enrolled ΔPMPM from 6 observations. Utilization unavailable |
| Observations | 0.01 s | 9, stored and screen verdict both INCONCLUSIVE |
| Baselines | 0.00 s | 10 |
| Evidence pack for MPPR | 0.00 s | Pack returned. Verdict INCONCLUSIVE |
| Policy verdicts | — | Enrolled member-month column. Clinical rows have no dollar outcome |
| Objectives health | — | 9 policy rows, status `no_data`, verdict INCONCLUSIVE. No objective contract is defined |

Signed-in browser on http://127.0.0.1:3055. Screenshots are in `docs/production/releases/synthetic_payer_browser/`.

| Screen | Result |
| --- | --- |
| Policy owner home, which is where this role lands | Pass. Enrolled baseline, 179,817.163 member-months, 9 active policies |
| Executive dashboard | Pass. Σ enrolled ΔPMPM −1.27 across 6 observations. Utilization unavailable, not 0.0 percent. Baseline labeled per eligible member-month, with the same member-month count. The paid-dollar chart is labeled as a sketch, not a P10/P50/P90 interval |
| Policy catalog | Pass. 9 policies. Descriptions say operational activation is prohibited and codes are candidates |
| MPPR workspace | Pass. Page loads. Description carries the prohibition. The dollar simulation is on the verdict and observation screens, not this overview |
| Baselines | Pass. 10 stored windows, 1 Jan 2024 through 30 Sep 2026 |
| Observations | Pass. Each tile shows the current screen verdict and the stored historical verdict, both Inconclusive |
| Policy verdicts | Pass. Column is dollars per enrolled member-month. Six payment rows show the enrolled rate. Three clinical rows show a dash |
| Objectives health | Partial. The page loads and does not invent on-track objectives. Rows are no-data because no objective contract exists |
| What-if | Fail as a population result. The builder opens and there are 0 scenario runs. It does not display these six simulations. A scenario was not launched, because that path is a separate forecast and would not be the reconciled payment result |
| Evidence pack | Pass on the API. The verdict page links to it. The dialog click was not confirmed in the screenshot |

−1.27 is the sum of six enrolled member-month rate changes, equal to −$227,800 of simulated allowed difference divided by 179,817.163 member-months. It is not a portfolio dollar total and it is not savings.

## 6. 100,000-life pipeline

Same code path, database `synthetic_payer_100k`. This is the full load and calculation, not the earlier in-memory timing.

| Step | Measured |
| --- | --- |
| Generate, load, baselines, six engines, nine observations, oracle match | 199 s |
| Load portion | 193 s |
| Claims | 51,286 |
| Enrollment rows | 1,893,872 |
| Member-months | 1,795,206.885 |
| Database size | 856 MB |
| Process peak memory | 1.0 GB |
| Engine versus oracle | Match within $0.02, including neutral $0 and adverse −$45,000 |
| Verdicts | 9 INCONCLUSIVE |
| Clinical payment impact | null |

Payment impacts at 100,000 lives: MPPR $400,000, site of service $90,000, PTP $301,600, unit cap $40,600, therapy $80,000, infusion $1,350,000. PTP and the unit cap are not exact ten-times figures because the modifier and unit draws continue through the extra members. The oracle still matches the engine.

API response times above are from the 10,000-life database. The 100,000-life run did not serve the UI.

## 7. 500,000-life readiness

Decision: ready to run locally, not started.

The 100,000-life pipeline passed its correctness checks. A 500,000-life run fits the same function and the same disposable server. It was not started. At the measured rate it is about 15 to 25 minutes, about 9.5 million enrollment rows, about 260,000 claim rows, and about 4 to 5 GB of database. Peak process memory at 100,000 lives was 1.0 GB. Stop the run if process memory passes 6 GB.

Exact run, and only this database:

```
PYTHONPATH="apps/api/src:packages/common/src" .venv7867/bin/python scripts/synthetic_payer_integrate.py 500000 synthetic_payer_500k
```

| Item | Value |
| --- | --- |
| Seed | 20261106 |
| Generator | synthetic-payer-v1 |
| Reference census | 2025-07-01, 500,000 enrolled |
| Window | 2024-01-01 through 2026-10-01 exclusive |
| Partial months | SYNTHETIC_PARTIAL_MONTH_V1 |
| Host | 127.0.0.1 port 55434 only |
| Pass rule | Database member-months equal the day walk. Six engines match the oracle within $0.02. Three clinical impacts stay null. Nine verdicts stay INCONCLUSIVE |
| Rerun | Drop `synthetic_payer_500k` and run the same command. The seed makes the population the same |
| Cloud | Not authorized |

## 8. Remaining blockers

- The claim file is not a realistic full medical and pharmacy history.
- MRI, NCD 220.2, and LCD L34425 have no outcome engine.
- The infusion codeset schema is not closed.
- Candidate codes are not approved includes.
- No endpoint contract, so no policy can leave INCONCLUSIVE.
- A CPT-only query mixes policies that share a code. The product baseline path does that unless the synthetic policy key is applied.
- What-if does not calculate from this population.
- Objectives health has nothing to score until an objective contract exists.
- The executive paid-dollar sketch is still an extrapolation. It is no longer labeled as a confidence interval.
- Lean staging still has the previous Gate A screens. Redeploy was not authorized.
- The 500,000-life run has not been executed.
