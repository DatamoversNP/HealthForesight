# Synthetic payer execution — 10,000-life pilot

Date: 2026-11-06. Local only. No staging rows, no December 4 demo, no Azure, no PHI.

Every dollar below is **SYNTHETIC / ILLUSTRATIVE**. It is not real-world savings, CMS adjudication, clinical certification, or a causal effect.

## What is running

Generator `synthetic-payer-v1`, seed `20261106`. It does not use the legacy `SyntheticDataGenerator`.

Partial-month convention `SYNTHETIC_PARTIAL_MONTH_V1`: coverage is half-open `[start, end)`, and a month counts as enrolled days divided by the days in that month.

10,000 members are enrolled on 2025-07-01. Window is 2024-01-01 through 2026-09-30. 6,000 members have no claims. Coverage intervals: 10,468. Claim rows: 5,128, of which 4,300 are active. Measured exposure: 179,817.163 member-months in the window, 106,325.685 in calendar 2025. That is the counted exposure, not 10,000 × 12.

Dataset: `data/synthetic/pilot_10k/` (`members.csv`, `coverage_intervals.csv`, `providers.csv`, `claim_lines.csv`, `reconciliation.json`). That directory is gitignored.

Allowed amount equals plan paid plus member cost share on every line. Paid is not copied from allowed. Service dates sit inside coverage. Reversals net to zero. LCD events use CPT 70540 (orbit, face, and neck candidate) and are not lumbar 72148. Codes are stamped `CANDIDATE_NOT_APPROVED`. No pharmacy claims: none of the nine policies require a dispensing record.

## Nine policies

| Policy | Execution | Events | Synthetic payment difference | Screen verdict |
| --- | --- | ---: | ---: | --- |
| MPPR | Simulation, secondary 50% | 400 lines | $40,000 payer pays less | INCONCLUSIVE |
| Imaging site of service | Simulation, hospital 80% | 100 | $9,000 | INCONCLUSIVE |
| PTP | Simulation | 200 | $32,000 | INCONCLUSIVE |
| Unit cap | Simulation, demo cap 4, not a CMS MUE | 100 | $3,800 | INCONCLUSIVE |
| Therapy | Simulation, pay medically necessary units only | 100 | $8,000 | INCONCLUSIVE |
| Infusion site | Simulation, per claim, codeset still not closed | 100 | $135,000 | INCONCLUSIVE |
| Lumbar MRI prior auth | NOT_MEASURABLE | 200 lines, decisions NOT_ADJUDICATED | none | INCONCLUSIVE |
| NCD 220.2 | NOT_MEASURABLE | 100 brain MRI candidate lines | none | INCONCLUSIVE |
| LCD L34425 | NOT_MEASURABLE | 100 orbit lines | none | INCONCLUSIVE |

No endpoint contract is declared, so the screen verdict stays INCONCLUSIVE. Stored historical verdicts were not written.

Scenarios on the same imaging lines: hospital percent 80 is favorable to the payer, 100 is neutral ($0), 110 is adverse (−$4,500). MPPR at 50% is the favorable payment case.

The published fixture checks still match the independent oracle: MPPR 3150 / 2550 / 600, site of service 4000 / 3480 / 520, PTP 4400 / 3600 / 800 with 3 pairs and 1 modifier bypass, unit cap 650 / 550 / 100, therapy 420 / 340 / 80, infusion fixture 18200 / 14600 / 3600. The population infusion run applies that price rule inside each claim. It does not steer only the first two lines in the file.

## Oracle

`uepi_common.synthetic_payer.oracle` does not call the application engines. `synthetic_population.simulate_payment_population` does. On the 10,000-life lines and on the 100,000-life lines, baseline paid, post paid, and payment impact match within $0.02 for all six payment runs, including the neutral and adverse site-of-service scenarios.

A zero or missing denominator does not become a rate. A non-positive baseline does not become a percent.

## Tests

- `packages/common/tests/test_synthetic_payer_pilot.py`
- `apps/api/tests/synthetic/test_population_engines.py`
- `apps/web/src/pages/__tests__/syntheticJourneyStatus.test.tsx`
- Gate A UI tests in `gateAAcceptanceRemediation.test.tsx` still pass

8 Python tests passed. 6 UI tests passed.

## Scale

| Run | Time | Claim rows | Where |
| --- | ---: | ---: | --- |
| 10,000 lives, generate and reconcile | 0.34 s | 5,128 | local files |
| 100,000 lives, all six engines vs oracle | 0.53 s | 51,286 | memory only |

100,000 neutral site-of-service impact is $0. Adverse impact is −$45,000. The 500,000-life function is the same `run_pilot(lives=500000)`. It was not executed, and no cloud run was started. At the measured rate a local 500,000-life pass is a few seconds of CPU. That is not authorization to load it into Azure.

Claim density is what this seed produced: about 0.43 active lines per member across the window, because 60% of members have no claims. The blueprint’s 8 lines per member-year was a capacity assumption, not a target to hit.

## Gate A

The observation screen verdict and the executive rollup fixes are in the working tree and covered locally. Lean staging was not redeployed, so the signed-in staging pages still show the previous behavior. Local evidence: `docs/production/releases/gate_a_browser_acceptance_remediation/local-corrected-screens.png` and `docs/production/releases/GATE_A_BROWSER_ACCEPTANCE_REMEDIATION.md`.

## Release blockers

- Staging browser re-acceptance of the Gate A screens, which needs a deploy authorization.
- The pilot is not loaded into an application database, so product pages do not yet read it.
- MRI, NCD 220.2, and LCD L34425 have no outcome engine. Events exist. Outcomes were not invented.
- Infusion codeset schema is still not closed.
- Candidate codes are not approved includes.
- No endpoint contracts, so every journey verdict is INCONCLUSIVE.
- 500,000-life cloud generation is not authorized.
