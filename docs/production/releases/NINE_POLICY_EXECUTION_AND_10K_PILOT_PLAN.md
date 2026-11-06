# Nine-policy execution capability and 10,000-life pilot plan

Date: 2026-11-06. Commit inspected: `ec3007f` on `measurement-integrity-gate-a`.

This is a read-only assessment. No staging rows were rewritten. No new population outcome engine was built. The 500,000-life dataset was not generated.

Authority for the nine policies remains `docs/demo/bcbs-nc/policy_definitions/v1.2/NINE_POLICY_TECHNICAL_CLOSURE_BOARD.json`. All nine are operationally prohibited. Candidate codes are not approved includes.

## What a fixture proves

Local calls of the known-answer functions passed on 2026-11-06:

| Policy | Function | Result |
| --- | --- | --- |
| MPPR | `verify_known_answer` | passed. Baseline paid 3150, post 2550, impact 600, 3 secondary lines |
| Freestanding imaging | `reimbursement_sos.verify_known_answer` | passed. Baseline 4000, post 3480, impact 520 |
| PTP | `verify_ptp_known_answer` | passed. Baseline 4400, post 3600, impact 800 |
| Unit cap | `verify_mue_known_answer` | passed. Baseline 650, post 550, impact 100. Cap value 4 is a demo cap, not a CMS MUE |
| Therapy | `verify_therapy_known_answer` | passed. Baseline 420, post 340, impact 80 |
| Infusion site | `verify_infusion_known_answer` | passed. Baseline 18200, post 14600, impact 3600 |
| NCD 220.2 | catalog note | passed as provenance only. Financial known-answer is not applicable |
| LCD L34425 | catalog note | passed as provenance only |

These checks use the fixture lines inside the engine modules. They do not prove the same rule over a member population, exclusions, or many claims.

The payment engines still turn a missing `allowed_amount` into 0 (`reimbursement_mppr.py`, `reimbursement_sos.py`, `expansion_demo_scenarios.py`). A population run has to reject missing allowed amounts before those functions see them.

## Execution matrix

| Policy | Platform ID | Version on the codeset | Engine that exists | Population execution | Before a 10,000-life pilot |
| --- | --- | --- | --- | --- | --- |
| Lumbar MRI prior authorization | `d403f101-08dd-45c9-ab83-d42e37c62018` | v1.2.1 technical closure, definition review required | Registry name path resolves prior auth to `um_elasticity_v1`. That is a utilization elasticity lookup, not an authorization decision engine. Eight release blockers. Clinical approval withheld | Not executable as a population outcome. Class `SIMULATION_ONLY` or `NOT_MEASURABLE` | Build an authorization-event engine, or keep the journey as configuration, applicability, and blocked execution |
| MPPR | `d0eeb370-df14-4478-8755-dad6c3a35a47` | v1.2.1-structural-controls | `reimbursement_mppr_v1`. `apply_mppr` accepts a list of lines | Candidate. Fixture only today | Run the engine on generated multi-procedure claims and reconcile allowed, paid, and secondary lines to an independent sum |
| Freestanding imaging | `d7441dd9-3bfe-405e-ae6c-0377204bbb7e` | v1.2.1-structural-controls | `reimbursement_sos_v1` | Candidate. Fixture only today | Generate place-of-service and allowed amounts. Reconcile the site differential independently |
| PTP | `58b839b5-b6e0-59e0-9406-d817877c3ce8` | v1.2.1-structural-controls | `reimbursement_ncci_ptp_v1` when metadata says Dec 4 expansion. Without that stamp the registry stays on the blocked modifier path | Candidate only on the fixture path. Empirical claims have no modifier column | Carry pair, modifier, and allowed amount on synthetic lines. Do not present the fixture edit as a certified CMS quarterly file |
| Unit cap | `e11b049d-fcce-55cc-bcd7-71329038383b` | v1.2.1-structural-controls | `apply_ncci_mue` exists. A name-only `resolve_strategy` call for this title returned `um_elasticity_v1`, not the unit-cap engine | Not safe to dispatch by name | Stamp the mechanism explicitly and test that elasticity is not used. Missing units must stay unavailable |
| Therapy | `f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b` | v1.2.1-structural-controls | Fixture `apply_therapy_coverage`. Registry family is `coverage_criteria_v1` | Fixture arithmetic only | Decide whether the pilot runs the fixture function or stops at `NOT_MEASURABLE` |
| Infusion site | `11218053-bdc0-569f-a415-fb61c5dcda37` | v1.2.1-structural-controls | Fixture `apply_infusion_soc` | Not closed. Codeset schema requirement failed | Do not treat the codeset as authoritative. Pilot may show the fixture math only if labeled synthetic |
| NCD 220.2 study | `4f8c34e3-015b-509d-90ba-521261464258` | v1.2.1-structural-controls | No financial outcome function. Catalog validation target `PROVENANCE_VALIDATED` | Not executable as savings or utilization | Show source, applicability, and missing evidence |
| LCD L34425 study | `649b4ac8-ca82-5b84-aa87-84834490731a` | v1.2.1-structural-controls | No financial outcome function. Codes 70540, 70542, 70543. Separate from lumbar MRI | Not executable as savings or utilization | Keep it separate from the lumbar prior-authorization policy |

Effective dates on the codeset records are null. Geography and line of business are representative design, not an approved benefit. Endpoint contracts are not stored on these nine policies, so Gate A scores a verdict `INCONCLUSIVE` until a contract is declared.

Staging execution-eligibility blocks were not read or changed in this step. The pilot must not clear them.

## 10,000-life pilot

The pilot is a new database namespace. It does not use `hfleanstg`, the December 4 demo database, or the legacy observation generator.

Population:

- 10,000 distinct members on a stated reference date.
- Coverage intervals with joins, terminations, and gaps. Member-months are counted from those intervals.
- Partial-month convention written down before any member-month is published. That convention still needs its own approval.
- Medical claim lines with heterogeneous use, including members with no claims.
- Pharmacy rows only for a policy that has a drug rule. None of the nine currently have a pharmacy outcome engine.
- Provider, network, and place of service where the payment engines need them.
- Deterministic seed, generator version, and policy version recorded on every run.

Pathways that can be implemented with the engines that exist now:

- MPPR, freestanding imaging, PTP, and the unit-cap fixture, after the unit-cap dispatch stamp is fixed and missing amounts fail closed.
- Therapy and infusion only as labeled fixture calculations, not as closed clinical policies.

Pathways that need a separate engine before they can show an executed outcome:

- Lumbar MRI prior authorization.
- NCD 220.2.
- LCD L34425.

Those three journeys in the pilot show configuration, scope, missing evidence, and blocked execution. They do not show a savings or utilization result.

Acceptance, all required:

- Member count and member-months match the coverage intervals.
- Allowed, paid, and cost share reconcile on claim lines.
- Each policy is either executed by its real function or marked `SIMULATION_ONLY` or `NOT_MEASURABLE`.
- The fixture totals in the table above still match when the fixture inputs are used.
- An independent oracle, not a call into the engine under test, matches eligible exposure, numerator, denominator, paid versus allowed, percent change, and verdict.
- A missing denominator or missing allowed amount does not become zero.
- No p-value of 0.01 or 0.50, and no confidence score invented from a missing input.
- Stored and recomputed verdicts both remain visible.
- No row is written to the current staging database or the demo database.

A failed reconciliation stops the program. The 500,000-life build stays unauthorized until this pilot passes and a separate approval names the new database.

## Approvals still required

1. Publish Gate A on the existing lean staging apps, then confirm the live staging screens. That publish is in progress from `ec3007f` and does not replace staging observations.
2. Approve the partial-month member-month convention.
3. Approve a 10,000-life database that is neither staging nor the demo.
4. Approve mechanism stamps so unit cap and prior authorization cannot fall through to utilization elasticity.
5. Approve any new authorization, NCD, or LCD outcome engine as its own build. A larger claims file does not create those engines.
6. Approve scale-up to 500,000 lives only after the pilot reconciles.
7. Approve any later demo promotion separately. The cutover phrase remains “CUTOVER DEMO TO STAGING.”
