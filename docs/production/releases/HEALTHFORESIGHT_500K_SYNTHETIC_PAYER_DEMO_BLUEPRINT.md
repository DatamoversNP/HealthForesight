# HealthForesight 500,000-life synthetic payer demo blueprint

Status: design only. No enrollment, claims, baselines, or observations were generated. No database was opened. No cloud resource was created. The December 4 demo was not modified.

Gate A H1–H5 remediation is recorded in `MEASUREMENT_INTEGRITY_GATE_A_REAUDIT.md`. Isolated runtime validation of those fixes is the next Gate A step. It is not this document, and it is not authorization to build the 500,000-life dataset.

## 1. What this program is

The target is a fresh synthetic health plan of 500,000 covered lives, used to show the HealthForesight lifecycle for the nine December 4 demonstration policies. Displayed measures must be calculated from generated source records. They must not be typed into dashboards.

500,000 is the plan population, not a claim count. Full-year exposure of 6 million member-months is a design target for a stable year. Actual member-months have to be counted from generated coverage intervals, including joins, terminations, and gaps.

Synthetic known answers can prove that the product calculates a planted intervention correctly. They cannot prove real savings, real provider behavior, or a causal effect. Every customer-facing number from this program is **SYNTHETIC / ILLUSTRATIVE**.

## 2. Authority for the nine policies

The nine policies are the set in `docs/demo/bcbs-nc/policy_definitions/v1.2/NINE_POLICY_TECHNICAL_CLOSURE_BOARD.json`. That board is the December 4 nine-policy technical closure list. The payment known-answer fixtures are checks for some of these policies. They are not a substitute list, and they are not the nine client policies by themselves.

The 250-policy lean-staging catalog is a different set. It is not the December 4 nine.

All nine have `operational_activation: PROHIBITED` on their codeset records. None are clinically certified. Candidate codes are not approved includes. This blueprint does not upgrade any of them.

| Policy | Platform policy ID | Document | Mechanism | Closure on the board | Executable today |
| --- | --- | --- | --- | --- | --- |
| Outpatient lumbar MRI prior authorization | `d403f101-08dd-45c9-ab83-d42e37c62018` | HF-RP-UM-MRI-001 | Proposed lumbar outpatient MRI prior authorization | Provisional structural pass, 8 release blockers, clinical approval withheld | Definition and decision tables exist. No population outcome engine. Classify new results `SIMULATION_ONLY` or `NOT_MEASURABLE` until an authorization engine is approved. |
| Multiple-procedure payment reduction | `d0eeb370-df14-4478-8755-dad6c3a35a47` | HF-RP-PAY-MPPR-001 | Same-claim multiple procedure payment reduction | Controls in place, 5 blockers | Fixture engine in `reimbursement_mppr.py`. Known answer: baseline allowed 3150, post 2550, impact 600, three secondary lines. Not a 500,000-life adjudicator. |
| Freestanding imaging site of care | `d7441dd9-3bfe-405e-ae6c-0377204bbb7e` | HF-RP-SOC-IMG-001 | Freestanding imaging steerage | Controls in place, 5 blockers | Fixture engine in `reimbursement_sos.py`. Known answer: baseline 4000, post 3480, impact 520. |
| NCCI procedure-to-procedure edit | `58b839b5-b6e0-59e0-9406-d817877c3ce8` | HF-RP-CODE-PTP-001 | PTP bundling | Controls in place, 4 blockers | Fixture in `expansion_demo_scenarios.py`: baseline 4400, post 3600, impact 800, 3 pairs, 1 modifier bypass. |
| NCCI unit cap | `e11b049d-fcce-55cc-bcd7-71329038383b` | HF-RP-CODE-MUE-001 | Unit cap | Controls in place, 4 blockers | Fixture: baseline 650, post 550, impact 100. Demo cap value 4 is not a CMS MUE. |
| Outpatient therapy coverage | `f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b` | HF-RP-COV-THER-001 | Therapy coverage | Controls in place, 5 blockers | Fixture: baseline 420, post 340, impact 80. |
| Infusion site of care | `11218053-bdc0-569f-a415-fb61c5dcda37` | HF-RP-SOC-INF-001 | Infusion site of care | Not closed. Codeset schema requirement failed. 5 blockers | Fixture: baseline 18200, post 14600, impact 3600. Do not treat the codeset as authoritative. |
| NCD 220.2 coverage study | `4f8c34e3-015b-509d-90ba-521261464258` | HF-RP-COV-NCD2202-001 | Coverage study | Controls in place, 4 blockers | Study definition. No approved outcome engine. |
| LCD L34425 orbit, face, and neck study | `649b4ac8-ca82-5b84-aa87-84834490731a` | HF-RP-COV-L34425-001 | Coverage study | Controls in place, 5 blockers | Study definition. Explicitly not the lumbar MRI prior-authorization policy. |

Effective dates on the codeset records are null. Product, line of business, and geography are representative commercial design, not an approved BCBS-NC benefit. Endpoint contracts are not yet stored on these policies. Until a contract is declared, Gate A scores a verdict `INCONCLUSIVE`.

A dataset will not create the missing prior-authorization, pharmacy step-therapy, or care-management outcome engines. Policies without an engine stay `SIMULATION_ONLY` or `NOT_MEASURABLE`.

## 3. Synthetic plan design

Calendar design, not an observed payer history:

- History: January 2024 through December 2025.
- Baseline year: calendar 2025, unless a policy effective date says otherwise.
- Observations: January through September 2026.
- Policy effective dates: explicit per policy before generation. They are not implied by the calendar.

Population design targets:

- 500,000 distinct members enrolled on a stated reference date.
- Coverage intervals, not a flat 12 months for every member.
- Documented partial-month convention before any member-month is published. That convention needs its own approval. This blueprint does not pick one.
- Product segments: commercial medical, with a pharmacy benefit only where a policy requires dispensing records.
- Age bands, a chronic-condition cohort, multimorbidity, and a high-cost tail.
- Healthy non-users. Utilization is not a fixed claim count per member.
- Provider organizations, network status, and place of service.
- Medical claim headers and lines: diagnoses, procedures, units, service dates, allowed, paid, and member cost share.
- Reversals and replacements with coherent dates.
- Authorization events only for policies whose mechanism needs them.
- Seasonal variation and longitudinal histories.
- Deterministic seeds and a generator version.

Distributions that are not taken from a cited public or licensed source are labeled synthetic assumptions and get a sensitivity check. They are not payer benchmarks.

No direct identifiers, no PHI, and no real customer claims.

## 4. Source events each policy needs

| Policy | Minimum source events | Must not be invented |
| --- | --- | --- |
| Lumbar MRI PA | Members, coverage, outpatient MRI lines, ordering provider, diagnosis, place of service, authorization request and decision | Clinical approval, a real denial rate, or a savings claim |
| MPPR | Same-claim multiple procedure lines with units and allowed amounts | CMS adjudication |
| Imaging site of care | Imaging lines with place of service and allowed amount, network site | A measured steerage effect |
| PTP | Paired procedure lines and modifier presence | A national PTP edit vintage presented as certified |
| Unit cap | Lines with units above and below the demo cap | The demo cap of 4 as a CMS MUE |
| Therapy coverage | Therapy lines, units, and coverage rule inputs used by the fixture | A visit-limit outcome engine that the code does not have |
| Infusion site | Infusion lines, site, and allowed amount | Closure of the failed codeset schema |
| NCD 220.2 study | Study-eligible events defined by the study spec | An outcome engine |
| LCD L34425 study | Orbit, face, and neck study events, kept separate from lumbar MRI | Copying lumbar MRI criteria into this study |

## 5. Independent oracle

The oracle is a separate calculation, written before generation and not implemented by calling the application function under test.

For each policy the oracle records:

- Eligible members and exposure from the coverage intervals.
- In-scope events and exclusions.
- Numerator, denominator, and the denominator basis.
- Baseline utilization and cost, with paid and allowed kept apart.
- The rule or simulation that changes events.
- Expected post-policy events.
- Absolute and percent change. Percent change is null when the baseline is missing or not positive.
- Payment impact where the fixture engine applies.
- Verdict from the declared endpoint contract. No contract means `INCONCLUSIVE`.
- Evidence class and the statement that uncertainty is not a confidence interval.

Required cases: expected direction, opposite direction, zero change, missing denominator, missing paid amount, allowed-only amount, and one policy with no engine.

Outcomes are not forced to look successful. At least one policy scenario is adverse, one is neutral, and one is beneficial.

Known fixture dollars in section 2 stay the payment checks. They are not rewritten to look like a 500,000-life result.

## 6. Scale estimate

These are planning ranges, not measurements.

| Item | 10,000-life pilot | 500,000-life target |
| --- | --- | --- |
| Members | 10,000 | 500,000 |
| Coverage interval rows | about 12,000 to 15,000 | about 600,000 to 750,000 |
| Materialized member-months if every month is stored for 33 months | up to about 330,000 | up to about 16.5 million |
| Medical claim lines, assumption of about 8 lines per member per year across 2.75 years | about 220,000 | about 11 million |
| Raw claim storage, about 1 KB per line before indexes | under 1 GB | about 10 to 20 GB with indexes |
| Generator time | minutes on a laptop if the pilot is vectorized | hours, to be measured on the pilot and scaled, not guessed as a commitment |

The 8-lines-per-member-year figure is a synthetic assumption for capacity planning. It is not a verified commercial benchmark. The pilot measures the actual distribution and replaces this range.

Compute and storage for the full population need a separate authorization. This blueprint does not request Azure spend.

## 7. 10,000-life pilot acceptance

The pilot is not authorized to run until Gate A isolated runtime validation has passed and a separate approval names the local or other non-production location.

The pilot passes only when all of the following are true:

- Coverage intervals reconcile to the member count and to calculated member-months.
- Claim financial columns reconcile: allowed, paid, and cost share.
- Each of the nine policies is either executed by its real engine or explicitly `SIMULATION_ONLY` or `NOT_MEASURABLE`.
- Fixture known answers in section 2 still match when the fixture inputs are used.
- Oracle and application results match on eligible exposure, numerator, denominator, paid versus allowed, percent change, and verdict.
- A missing denominator does not become a rate of zero.
- Allowed dollars are not labeled paid or enrolled PMPM.
- No p-value of 0.01 or 0.50 is emitted.
- Stored and recomputed verdicts are both visible and different when the contract is missing and the stored status is not `INCONCLUSIVE`.
- No row is written to the existing staging database, the demo database, or the 2,250 stored observations.

A failed reconciliation stops the program. The 500,000-life phase does not start.

## 8. Later phases, not started

Phase 5, the 500,000-life build, needs a fresh database namespace and a new authorization. It must not overwrite staging or the December 4 demo.

Phase 6 records PASS, FAIL, or NOT_TESTED for every policy, formula, and customer screen. An HTTP 200 is not a pass.

Phase 7 is a separate demo-readiness report. Promotion into a demo environment is another authorization. The frozen December 4 demo stays frozen until that approval. The cutover phrase remains “CUTOVER DEMO TO STAGING” and is not granted here.

## 9. Controls

- Keep the 2,250 staging observations.
- Keep the 250 execution-eligibility blocks.
- Do not change the December 4 demo, its fixtures, or its App Service.
- Do not reuse the legacy observation generator.
- Do not mutate production or the current staging database.
- Do not create billable Azure resources.
- Do not use PHI.
- Do not invent policy codes or approval decisions.
- Do not force every policy to a utilization decrease.
- Do not skip a failed gate.
- Do not describe a simulation as an empirical prediction.

## 10. Decisions still required

1. Approve isolated runtime validation of Gate A on a local process, after this remediation.
2. Choose the partial-month member-month convention.
3. Choose which of the nine mechanisms may be simulated versus left `NOT_MEASURABLE`.
4. Approve a 10,000-life pilot location that is not staging and not the demo.
5. Approve the 500,000-life namespace, storage, and runtime only after the pilot reconciles.
6. Approve any future demo promotion separately.

Until those decisions are made, the next permitted work is Gate A isolated runtime validation, not data generation.
