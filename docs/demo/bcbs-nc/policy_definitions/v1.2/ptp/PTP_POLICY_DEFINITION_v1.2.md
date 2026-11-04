# NCCI Procedure-to-Procedure Bundling — Policy Definition v1.2

| Field | Value |
|---|---|
| Document ID | `HF-RP-CODE-PTP-001` |
| Platform policy ID | `58b839b5-b6e0-59e0-9406-d817877c3ce8` |
| Template | Derived from HF-RP-UM-MRI-001 v1.2 quality standard |
| Definition status | **DEFINITION_REVIEW_REQUIRED** |
| Mechanism | `CODING_EDIT_MODIFIER` |
| Intended scope band | `PTP_PAIR_70553_70551` |
| Synthetic analytics | Independent of definition approval; fixtures: SYNTHETIC_FIXTURE PTP pair — not published CMS quarterly row |

## Three-layer separation
A) Policy definition (operative only after approval)  
B) Analytical assumptions (never enforcement)  
C) Synthetic fixtures (never clinical/payment authority beyond labeled demo)

## Design intent
Representative Payer NC-oriented policy. Not verbatim Blue Cross NC text.

## Decision outcomes
`NOT_APPLICABLE` | `PENDING_INFORMATION` | `CLINICAL_REVIEW_REQUIRED` (if clinical) | `APPLY_EDIT` / `APPROVED` / `ADVERSE_REVIEW_REQUIRED / ADVERSE_DETERMINATION_ISSUED` as mechanism-appropriate | `MANUAL_SCOPE_REVIEW`

Ambiguous mappings: **no auto-deny; no silent scope expansion**; route to authorized review; preserve member protections.

## Open decisions
Product schedule, approved thresholds, legal clocks, and (where clinical) signed criteria remain **UNRESOLVED**.


## Structural controls (v1.2.1)

| Field | Value |
|---|---|
| Controls standard | `../_controls/POLICY_ENGINEERING_CONTROLS_v1.md` |
| Reference implementation | MRI v1.2.1 (frozen) — **controls only**, not clinical logic |
| Operational activation | **PROHIBITED** |
| Technical closure | **Not asserted PASS** — see `PTP_TECHNICAL_CLOSURE_VALIDATION_REPORT.json` |
| Release blockers | `PTP_RELEASE_BLOCKERS.json` (hard blockers) |
| Adverse outcomes | `ADVERSE_REVIEW_REQUIRED` / `ADVERSE_DETERMINATION_ISSUED` |
| Dec 4 fixtures | Unchanged |

## Release
DEFINITION_REVIEW_REQUIRED. Do not assert production readiness.
