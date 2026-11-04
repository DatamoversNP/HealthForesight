# HealthForesight — December 4 Final Readiness Report

**Generated:** 2026-11-03 (local demo7867 stack → Azure Postgres)  
**Decision:** **DEMO_READY_WITH_DISCLOSED_LIMITATIONS**  
**Scope claimed:** Three-policy **synthetic** demonstration (MRI + MPPR + SOS) plus verified Medicare applicability links — **not** the full 283-policy catalog, **not** production qualification, **not** actual Blue Cross NC financial outcomes.

### Expansion addendum (2026-11-03 evening → clinical pass)

- **Jurisdiction corrected:** Prior **L35175 / A54118** removed (Noridian J-F).  
- **Clinical applicability verified:** **NCD 220.2** = primary national MRI authority. **L34425 / A56729** = NC/JM OK but **PARTIAL** (orbit/face/neck CPT 70540/42/43 only) — **not** general MRI PA authorities. See `MRI_MEDICARE_CLINICAL_APPLICABILITY.md`.  
- **Primary live Dec 4 path:** MRI → MPPR → SOS → Medicare Rules Explorer → Objective Health.  
- **Six expansion scenarios** = extensibility evidence / in development — not counted as FULLY_VALIDATED_DEMO.  
- **Causal:** all domains remain `estimation_eligible`; MPPR/PTP are `CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT` (not permanently excluded).  
- Next milestone: independently validate PTP, MUE, infusion SOC, and one NC LCD coverage study lifecycles.

---

## Executive decision

| Outcome | Value |
|---|---|
| Readiness | `DEMO_READY_WITH_DISCLOSED_LIMITATIONS` |
| Production qualified | **No** |
| Catalog fully validated | **No** (3 of 283) |
| Authoritative CMS inventory | **No** (example ingest only) |
| Blue Cross NC proprietary data | **Not used / not claimed** |

**Demo story that is supported:** One governed policy lifecycle across utilization management and reimbursement. MRI demonstrates synthetic causal/utilization impact; MPPR and site-of-service differential demonstrate mechanism-specific payment engines with persisted known-answer math; Medicare NCD/LCD/article/NCCI links inform MRI applicability and verdict lineage without fabricating Medicare financial outcomes.

---

## Gate matrix

| Gate | Status | Evidence | Blocker |
|---|---|---|---|
| MRI lifecycle | **PASS** (synthetic) | Causal DiD known-answer; workspace + prior browser/API evidence; return visit in rehearsals | — |
| MPPR lifecycle | **PASS** | API `$600` / `+$120`; `MPPR_REIMBURSEMENT_VERTICAL.json`; rehearsal screenshots | — |
| SOS lifecycle | **PASS** | API `$520` / `+$260`; browser workspace/baseline/predicted/verdicts/what-if; `SOS_REIMBURSEMENT_VERTICAL.json` | — |
| Medicare rule architecture | **PASS** (bounded) | `medicare_rules.py`; source docs + typed links; explorer + Applicable Medicare Rules panel | Not a full CMS inventory |
| Medicare source provenance | **PARTIAL** | 6 public/example source documents; MRI linked to NCD220.2, L35175, A54118, NCCI-PTP example | Full NCD/LCD/NCCI reconciliation unfinished |
| Medicare applicability | **PASS** (demo resolver) | FFS NC → Palmetto JM; MA/commercial exclusions explicit; `MATCHED_FFS_CHAIN` | Resolver uses illustrative fixture chain + linked docs |
| Medicare analytical integration | **PASS** (lineage) | `rule_set_id` on applicable-rules + MRI verdict-evidence lineage | Does not drive claims cohort SQL yet |
| Mechanism registry | **PASS** 9/9 | `analytical-strategy-registry-v1`; SOS name no longer falls through to UM | — |
| Unified verdict | **PASS** | Forecast / causal / governance remain separate; `financial_vs_verdict` note | — |
| Objective Health stability | **PASS** | API summary 283/186/79/18; prior browser gates; rehearsal OH step | — |
| Cross-policy browser regression | **PASS** | MRI → MPPR → SOS → Medicare → MRI → OH ×2 | Concurrent second-session isolation not separately scripted |
| Rehearsal 1 | **PASS** 156.3s | `dec4_final_gates/r1_*.png` | — |
| Rehearsal 2 | **PASS** 157.6s | `dec4_final_gates/r2_*.png` | — |

Machine-readable gate run: `docs/demo/bcbs-nc/evidence/dec4_final_gates/DEC4_FINAL_GATES.json`.

---

## Independently reconciled financial calculations

Sign convention (enforced in registry + vertical APIs): **positive `payment_impact` / `delta_payment_impact` = payer savings**; provider payment change is the negation, ceteris paribus. No utilization elasticity on MPPR/SOS paths (`utilization_change_per_1k` is null).

### MPPR — Multiple Procedure Payment Reduction

| Metric | Expected | Observed (API 2026-11-03) |
|---|---|---|
| Baseline paid | $3,150 | $3,150 |
| Post-policy paid | $2,550 | $2,550 |
| Payer savings | $600 | $600 |
| What-if secondary 50% → 40% additional savings | $120 | $120 |
| Calculation version | `reimbursement-mppr-v1` | confirmed |

Arithmetic total scenario savings if narrated against base: `$600 + $120 = $720` (scenario delta only; no other factors).

### SOS — Freestanding Imaging Steerage (site-of-service payment differential)

| Metric | Expected | Observed (API 2026-11-03) |
|---|---|---|
| Baseline paid | $4,000 | $4,000 |
| Post-policy paid | $3,480 | $3,480 |
| Payer savings | $520 | $520 |
| What-if hospital share 80% → 70% additional savings | $260 | $260 |
| Volume / mix effects | 0 | 0 |
| Calculation version | `reimbursement-sos-v1` | confirmed |
| Browser lifecycle | required | **PASS** (workspace, baseline, predicted, verdicts, what-if) |

Arithmetic total scenario savings if narrated against base: `$520 + $260 = $780`.

### MRI — Outpatient MRI Prior Authorization

Synthetic DiD known-answer remains approximately **−9.417 January-index points** (not util/1k). Labeled synthetic; not BCBS NC empirics.

---

## Medicare: policies vs rules (how they are used)

| Entity | Role in HealthForesight |
|---|---|
| **NCD** | First-class **coverage determination**; independently browsable; linkable to a Representative Payer policy (`REFERENCES_NCD`) |
| **LCD** | First-class **local coverage determination** (NC Original Medicare → Palmetto GBA JM); linkable (`REFERENCES_LCD`); cannot override NCD |
| **Billing/coding article** | **Supporting document** (`HAS_RELATED_ARTICLE`), version-linked to LCD/NCD |
| **NCCI PTP / MUE** | **Coding/payment rules**, not medical-necessity policies (`USES_CODING_EDIT`) |
| **Representative Payer Policy** | Primary analytical workspace; may **reference / adapt** the above |

**MRI demo example (seeded):** policy links NCD220.2, L35175, A54118, NCCI-PTP-2024Q4-EXAMPLE → `rule_set_id`  
`medicare-ruleset:d403f101-…:Original_Medicare_FFS:North_Carolina:2024-06-01:4`  
attached to verdict lineage. Outcomes remain **synthetic**.

UI:
- `/medicare-rules` — Medicare Rules Explorer  
- Policy Workspace → Applicability → Applicable Medicare Rules  

---

## 283-policy validation classifications (honest)

| Class | Count (approx / reported) | Claim allowed |
|---|---|---|
| FULLY_VALIDATED_DEMO | **3** (MRI, MPPR, SOS) | Yes — synthetic demo |
| ARTIFACTS_PRESENT_UNVALIDATED | ~254 | No lifecycle validation claim |
| PARTIAL / INAPPLICABLE / BLOCKED | ~26 combined (prior audit) | Show readiness honesty only |
| Configured Representative Payer catalog | **283** | Catalog size ≠ validated analysis |

Do **not** state that 283 policies are validated or that CMS/NCCI inventories are complete.

---

## Code and migration changes (this qualification pass)

Additive / qualifying work (not a production cutover):

- `apps/api/src/uepi_api/services/medicare_rules.py` — list/seed/applicable rule-set
- `apps/api/src/uepi_api/routers/enterprise_intelligence.py` — medicare + SOS/MPPR verticals
- `apps/api/src/uepi_api/services/analytical_strategy_registry.py` — SOS name dispatch before SITE_OF_CARE→UM
- `apps/api/src/uepi_api/services/enterprise_intelligence_fixtures.py` — `financial_vs_verdict` + medicare rule-set on MRI verdict
- `apps/web/src/pages/MedicareRulesExplorerPage.tsx`
- `apps/web/src/components/policy/EnterpriseIntelligencePanels.tsx` — `ApplicableMedicareRulesPanel`
- `apps/web/src/pages/PolicyWorkspacePage.tsx`, `App.tsx`, `Layout.tsx`, `lib/api.ts`
- Gate runner: `docs/demo/bcbs-nc/evidence/run_dec4_final_gates.py`
- Evidence: `docs/demo/bcbs-nc/evidence/dec4_final_gates/*`

Prior same-day foundation (still in tree): MPPR/SOS engines, registry, source inventory adapters, OH stability, inventory manifest v2.

---

## Tests executed

| Suite | Result |
|---|---|
| Inline analytical strategy registry (9 checks) | **9/9 PASS** |
| MPPR `verify_known_answer` | **PASS** |
| SOS `verify_known_answer` | **PASS** |
| API SOS / MPPR verticals | **PASS** (`$520/$260`, `$600/$120`) |
| Medicare seed + applicable rules (4 links) | **PASS** |
| SOS browser lifecycle | **PASS** |
| Cross-policy rehearsals ×2 | **PASS** |
| OH API summary | **PASS** (283 policies responsive) |

---

## Browser evidence locations

- `docs/demo/bcbs-nc/evidence/dec4_final_gates/sos_*.png`
- `docs/demo/bcbs-nc/evidence/dec4_final_gates/r1_*.png`, `r2_*.png`
- `docs/demo/bcbs-nc/evidence/dec4_final_gates/DEC4_FINAL_GATES.json`
- Prior OH gates: `docs/demo/bcbs-nc/evidence/OBJECTIVES_HEALTH_BROWSER_GATES.json`

Stack under test: API `http://127.0.0.1:7867`, Web `http://127.0.0.1:7868` (Data Voyager demo7867), Azure Postgres via `.env.demo7867`.

---

## Known limitations that **must** be disclosed in the demo

1. **Synthetic demonstration scenarios only** — MRI, MPPR, and SOS financial/causal figures are known-answer / labeled synthetic, **not** Blue Cross NC results.
2. **Default catalog label:** Representative Payer Policies (Blue Cross NC-**like**). No proprietary BCBS NC authorization asserted.
3. **283 ≠ validated** — most policies have artifacts without independent mechanism validation.
4. **Medicare** examples are a **bounded** linked set (6 source docs), not a reconciled CMS/NCCI inventory; applicability resolver still mixes illustrative fixture identifiers with ingested document IDs.
5. **Medicare rules inform applicability/lineage**; they do **not** yet fully drive claims cohort selection SQL for every analysis stage.
6. **Claims substrate** (~3.5M lines) has known field gaps (e.g., modifiers) that **block** some coding-edit mechanisms.
7. **Not production-qualified** — no claim of production readiness or real-claims causal qualification.

---

## Remaining work (post–Dec 4 demo, not required to claim the three-policy story)

- Authoritative public NCD/LCD/article/NCCI inventory acquisition + checksums
- Persist rule-set identity into baseline/prediction/observation rows for all stages
- Concurrent two-browser isolation script (soft-covered by sequential rehearsals)
- Validate remaining ~280 policies by readiness class
- Real claims-based causal designs

---

## Explicit readiness decision

**DEMO_READY_WITH_DISCLOSED_LIMITATIONS**

Defensible December 4 demonstration of one governed lifecycle across UM (MRI), reimbursement (MPPR, SOS), and Medicare applicability (linked NCD/LCD/article/NCCI on MRI), with mechanism-specific engines and persisted synthetic evidence — provided the disclosed limitations above are stated aloud and on-screen.
