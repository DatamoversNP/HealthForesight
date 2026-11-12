# HealthForesight 500,000-life product acceptance

Date: 2026-11-06. Local only. The 500,000-life database was not deployed. Staging, production, Azure, and the frozen December 4 demo were not changed. The 10,000-life application and its database were left running.

Every dollar below is a synthetic illustration. It is not measured savings, CMS adjudication, clinical certification, or a causal effect.

## Environment and isolation

| Item | 500,000-life application | 10,000-life application |
| --- | --- | --- |
| Web | http://127.0.0.1:3155 | http://127.0.0.1:3055 |
| API | http://127.0.0.1:8092 | http://127.0.0.1:8091 |
| Database | `synthetic_payer_500k` on `127.0.0.1:55434` | `synthetic_payer` on the same local Postgres |
| Covered lives | 500,000 | unchanged |
| Member-months | 8,986,494.004 | 179,817.163 |
| Claim rows | 256,428 | 5,128 |
| Executive figure | −1.26 $ / enrolled member-month | −1.27 $ / enrolled member-month |

The 500,000-life API reports `current_database() = synthetic_payer_500k`. The 10,000-life API does not expose that identity route, and its dashboard still returns the 10,000-life claims count and −1.27. Nothing in this run wrote to staging, Azure, or the December 4 demo.

Local sign-in for either disposable database: `synthetic.local@example.com` / `synthetic-local-only`.

The banner on every 500,000-life screen says: synthetic payer population, 500,000 covered lives, 8,986,494.004 member-months, 256,428 policy-event claim rows, pharmacy rows 0, database `synthetic_payer_500k`. It states that this is a covered population plus a policy-event extract, not a complete medical or pharmacy book, and that the dollars are not real adjudication or measured savings.

Seed `20261106`. Generator `synthetic-payer-v1`. No new population was generated.

## Nine-policy acceptance

Operational activation stays prohibited. Codes stay candidates. No endpoint contract is stored, so every stored verdict and every screen verdict is `INCONCLUSIVE`. Missing clinical outcomes stay null. They are not shown as zero.

Policy baselines use policy identity plus procedure scope. What-if line loads for all nine policies excluded 0 lines for another policy identity, 0 inactive lines, and 0 out-of-scope procedure codes. Shared CPT codes did not combine populations.

| Policy | Lines | Baseline allowed | Simulated allowed | Allowed difference | Plan paid, baseline → simulated | Payer difference | Per enrolled member-month | Oracle | Verdict |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |
| MPPR, secondary 50% | 20,000 | 14,000,000 | 12,000,000 | −2,000,000 | 11,200,000 → 9,600,000 | 2,000,000 less | −0.2226 | Match | INCONCLUSIVE |
| Imaging site of service, hospital 80% | 5,000 | 4,500,000 | 4,050,000 | −450,000 | 3,600,000 → 3,240,000 | 450,000 less | −0.0501 | Match | INCONCLUSIVE |
| Site of service, hospital 100% | 5,000 | — | — | 0 | — | 0 | 0 | Match | same policy |
| Site of service, hospital 110% | 5,000 | — | — | +225,000 | — | 225,000 more | — | Match | same policy |
| PTP | 10,000 | 6,000,000 | 4,480,400 | −1,519,600 | 4,800,000 → 3,584,320 | 1,519,600 less | −0.1691 | Match | INCONCLUSIVE |
| Unit cap, demo cap 4, not a CMS MUE | 5,000 | 1,056,000 | 852,000 | −204,000 | 844,800 → 681,600 | 204,000 less | −0.0227 | Match | INCONCLUSIVE |
| Therapy | 5,000 | 1,000,000 | 600,000 | −400,000 | 800,000 → 480,000 | 400,000 less | −0.0445 | Match | INCONCLUSIVE |
| Infusion site, per claim | 5,000 | 22,750,000 | 16,000,000 | −6,750,000 | 18,200,000 → 12,800,000 | 6,750,000 less | −0.7511 | Match | INCONCLUSIVE |
| Lumbar MRI prior authorization | 10,000 | none | none | none | none | none | none | not scored | INCONCLUSIVE |
| NCD 220.2 | 5,000 | none | none | none | none | none | none | not scored | INCONCLUSIVE |
| LCD L34425 | 5,000 | none | none | none | none | none | none | not scored | INCONCLUSIVE |

The payer difference is baseline allowed minus simulated allowed. Positive means simulated allowed is lower. The allowed difference is the opposite sign. Plan paid is the stored plan-paid amount. Simulated plan paid applies that same plan-paid share of allowed (80 percent on these lines) to the simulated allowed. It is not a second adjudication.

Each policy has one observation. Comparisons are present. The MPPR evidence pack opens from the verdict screen. The reason is: no policy endpoint contract is defined, so a change in utilization or cost is not a verdict. Confidence is null and displays as unavailable. Utilization change on the executive rollup is `UNAVAILABLE`, not zero.

The executive card is **−1.26 $ / enrolled member-month**. The label is: simulated allowed-dollar difference per enrolled member-month. Negative means simulated allowed is below baseline allowed. The figure is the sum of the policy allowed differences divided by the shared enrolled member-month denominator. It is not measured savings. The general baseline member-months are 8,986,494.004, denominator `ENROLLMENT`. The 200,000 figure on the policy-owner population card is members with claims in the extract, not the covered census. The banner carries the 500,000 covered lives.

Objectives health: 9 policies, 0 on track, 0 at risk, 9 no data. That follows from having no objective contract.

## What-if

What-if for these policies runs on the claim lines of the selected policy in the connected database. It calls the same six payment engines used for the population simulation. The independent oracle is compared afterward and is not copied into observations or baselines.

Checked in the API and, for MPPR, MRI, and the two-policy rejection, in the signed-in browser:

- Default MPPR, site of service, PTP, unit cap, therapy, and infusion match the oracle and the population impacts above.
- Site of service at 100 percent of allowed is a real zero. At 110 percent the payer difference is −225,000 (simulated allowed is higher).
- MRI, NCD 220.2, and LCD L34425 return `NOT_MEASURABLE` with null dollars. The MRI screen says an outcome-based what-if is unavailable and shows Unavailable, not $0.
- Two policies in one run are rejected. Ordered composition is not implemented, because summing policies could count one line twice.
- A secondary-procedure percent outside 0 to 1 is rejected.
- The result says it is not measured savings, not a confidence interval, and not real adjudication. No p-value is returned.
- The result is shown on the page. It is not written into the legacy what-if scenario table, so older scenario rows cannot appear as this population.

The six payment formulas were not changed.

## Browser acceptance

Signed in at http://127.0.0.1:3155. Screenshots: `docs/production/releases/synthetic_payer_500k_browser/`.

| Journey | Result | What was checked |
| --- | --- | --- |
| Dataset banner | PASS | 500,000 lives, member-months, database name, policy-event wording, no real adjudication |
| Executive dashboard | PASS | −1.26, simulated-allowed label, utilization Unavailable, member-months, paid-dollar sketch labeled as not a confidence interval |
| Executive, 390px wide | PASS | Navigation collapses. Horizontal overflow 15px |
| Policy list | PASS | All nine names, including MRI, NCD 220.2, and LCD L34425 |
| Policy workspace | PASS | MPPR workspace `d0eeb370-df14-4478-8755-dad6c3a35a47` |
| Baselines | PASS | Baseline screen loads against this database |
| Observations | PASS | Observation list opens the MPPR row |
| Verdicts | PASS | Nine inconclusive rows. Column is dollars per enrolled member-month |
| Evidence | PASS | Imaging site-of-service pack: inconclusive because no endpoint contract |
| Objectives health | PASS | Page loads. API count is 9 no-data |
| What-if, MPPR | PASS | Baseline allowed $14,000,000, simulated allowed $12,000,000, oracle agrees, 20,000 lines, database `synthetic_payer_500k` |
| What-if, MRI | PASS | Not measurable. Dollars unavailable |
| What-if, two policies | PASS | Rejected on screen |
| Page errors | PASS | No page errors during the run |

## Performance

These are application and browser times against `synthetic_payer_500k`, not the earlier in-memory engine benchmark.

| Call | Seconds |
| --- | ---: |
| Identity, cold, including member-months | 5.23 |
| Identity, cached | 0.02 |
| Dashboard | 0.03 |
| Policy list, 9 policies | 0.01 |
| Baselines, 10 rows | 0.01 |
| Observations, 9 rows | 0.01 |
| Verdicts | 0.01 |
| What-if MPPR, 20,000 lines | 0.62 |
| What-if PTP, 10,000 lines | 0.30 |
| What-if MRI, source events only | 0.29 |
| Other single-policy what-if runs | 0.07–0.15 |
| Evidence pack | 0.00 |
| Signed-in page loads | about 1.1–1.6, including a short settle before the screenshot |

No query in this pass was slow enough to justify a new index. The member-month total is cached in the API process after the first read. The claims read for one policy uses the policy category and the stored policy key.

## Remaining blockers

- No endpoint contracts, so all nine verdicts stay inconclusive. That is intentional.
- MRI prior authorization, NCD 220.2, and LCD L34425 can show source events. They cannot show a population outcome.
- The infusion codeset is not closed. Codes remain candidates. Operational activation remains prohibited.
- The file is a policy-event extract: 300,000 members have no claims, and there is no pharmacy book.
- What-if will not combine two policies. A documented ordered composition is still future work.
- What-if results are not stored in the legacy scenario history.
- The executive paid-dollar sketch remains a labeled extrapolation, not a confidence interval.
- The Gate A observation and executive fixes are in this local application. They are not redeployed to staging.
- This environment does not replace the December 4 demo.

## Demo readiness

Use http://127.0.0.1:3155 for a local rehearsal of the nine mechanisms. A prospective payer can see the covered population, the policy-event extract, six reconciled payment simulations, three blocked clinical policies, inconclusive verdicts, and a what-if that changes the payment parameter on this population.

Do not deploy this dataset. Do not point staging or the December 4 demo at it. Do not describe the −1.26 figure as savings, and do not describe the three clinical policies as executable population outcomes.

The next step is a rehearsal on this local application and a separate decision about whether it stays a local demonstration. It is not a release cutover.
