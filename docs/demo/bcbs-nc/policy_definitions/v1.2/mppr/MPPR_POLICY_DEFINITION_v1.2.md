# Multiple Procedure Payment Reduction — Policy Definition v1.2

| Field | Value |
|---|---|
| Document ID | `HF-RP-PAY-MPPR-001` |
| Platform policy ID | `d0eeb370-df14-4478-8755-dad6c3a35a47` |
| Template | Derived from HF-RP-UM-MRI-001 v1.2 quality standard |
| Definition status | **DEFINITION_REVIEW_REQUIRED** |
| Mechanism | `MULTIPLE_PROCEDURE_PAYMENT_REDUCTION` |
| Intended scope band | `MULTI_PROCEDURE_SAME_CLAIM` |
| Synthetic analytics | Independent of definition approval; fixtures: reimbursement-mppr-v1 known-answer $600 / +$120 what-if |

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
| Technical closure | **Not asserted PASS** — see `MPPR_TECHNICAL_CLOSURE_VALIDATION_REPORT.json` |
| Release blockers | `MPPR_RELEASE_BLOCKERS.json` (hard blockers) |
| Adverse outcomes | `ADVERSE_REVIEW_REQUIRED` / `ADVERSE_DETERMINATION_ISSUED` |
| Dec 4 fixtures | Unchanged |

## Release
DEFINITION_REVIEW_REQUIRED. Do not assert production readiness.
