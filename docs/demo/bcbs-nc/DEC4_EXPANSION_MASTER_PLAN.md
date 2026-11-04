# December 4 Expansion — Master Plan & Autonomous Execution Board

**Status:** ACTIVE EXECUTION (agent autonomy window)  
**Frozen fallback:** MRI + MPPR + SOS (`DEMO_READY_WITH_DISCLOSED_LIMITATIONS`)  
**Catalog label:** Representative Payer Policies (Blue Cross NC-like)  
**LCD rule:** NC → Palmetto GBA → Jurisdiction M (JM). NCDs are national.

---

## Critical provenance correction (executed first)

| Prior MRI link | Finding | Action |
|---|---|---|
| LCD **L35175** | Noridian **J-F** (AK/ID/OR/WA/…); **NOT** NC/JM; retired 2025-10-23 | Remove as NC-applicable; keep as `NOT_APPLICABLE_OTHER_JURISDICTION` library record if retained |
| Article **A54118** | Tied to wrong LCD chain | Replace |
| Replacement LCD | **L34425** — MRI of Orbit/Face/Neck — **Palmetto JM includes NC** | Link to MRI |
| Replacement article | **A56729** — Billing and Coding for L34425 | Link to MRI |
| NCD **220.2** | Verified national MRI NCD (`NCDId=177`) | Keep; fix URL to official MCD |

---

## Three-layer architecture

1. **Authoritative Medicare Reference Library** — all acquired NCD/LCD/article/NCCI/payment rules  
2. **Composable Policy Configuration** — Representative Payer policies + applicable rule links  
3. **Policy Lifecycle Intelligence** — baseline → prediction → observations → what-if → causal feasibility → verdict  

Do **not** create one analytical workspace per NCCI edit.

---

## Execution phases (dependency order)

| Phase | Work | Done when |
|---|---|---|
| 0 | Plan + provenance verification | This doc + L34425/A56729 live |
| A | MCD/NCCI/payment acquisition adapters + drops | Reconcile reports with counts |
| B | Rule graph + NC applicability engine | Deterministic `rule_set_id`; reject wrong-jurisdiction LCDs |
| C | Cross-domain causal feasibility (4 statuses) | API for every policy type |
| D | P0 scenarios: NCCI PTP, MUE, OP therapy, infusion SOC | Known-answer + lifecycle |
| E | Verified NCD + NC LCD coverage scenarios | Provenance + synthetic analytics |
| F | UI/API: explorer, applicability, causal workbench, coverage dashboard | Browser smoke |
| G | Regression MRI/MPPR/SOS/OH + new gates | Pass or documented blocker |
| H | Delivery reports listed below | Written with actual counts |

---

## P0 policies to add (synthetic payer configs; public CMS links)

1. NCCI PTP bundling / payment edit  
2. NCCI MUE unit limits  
3. Outpatient therapy coverage & payment (LCD/article linked when verified)  
4. Infusion site-of-care optimization  
5. NCD-linked coverage scenario (uses verified NCD 220.2)  
6. NC LCD-linked coverage scenario (uses L34425 / A56729)

Promotion to `FULLY_VALIDATED_DEMO` only after calculation + API + persistence + browser + regression gates.

---

## Causal impact design

- **Eligibility:** assessed for **all** policy types  
- **Estimation:** only when identification is defensible  
- Statuses: `CAUSAL_ESTIMATE_SUPPORTED` | `CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT` | `DESCRIPTIVE_ONLY` | `NOT_IDENTIFIABLE`  
- Mechanical payment effect ≠ causal savings  

---

## Medicare source map (upkeep)

| Source | Cadence | Method |
|---|---|---|
| MCD bulk + Coverage API | Weekly check / incremental | Bulk + license-token API + file-drop |
| Historical MCD versions | As needed | API/archive — never invent |
| NCCI PTP/MUE | Quarterly | Official CMS files → drop → reconcile |
| PFS / payment indicators | Annual / quarterly | CMS RVU / payment pubs |

Refresh jobs must be idempotent; failures must not silently promote synthetic stubs as authoritative.

---

## Required delivery artifacts

- `MEDICARE_SOURCE_ACQUISITION_REPORT.md`
- `MEDICARE_INVENTORY_RECONCILIATION.md`
- `MEDICARE_RULE_GRAPH_VALIDATION.md`
- `MEDICARE_ANALYTICAL_COVERAGE_MATRIX.md`
- `CROSS_POLICY_CAUSAL_FEASIBILITY_REPORT.md`
- `MEDICARE_DEMO_EXPANSION_VALIDATION.md`
- Updated `DEC4_FINAL_READINESS_REPORT.md` (frozen 3 remain stable; expansion gated separately)

---

## Non-claims

- Not all 283 validated  
- Not complete CMS inventory until reconcile says so  
- Not BCBS NC proprietary outcomes  
- Not production-qualified  
