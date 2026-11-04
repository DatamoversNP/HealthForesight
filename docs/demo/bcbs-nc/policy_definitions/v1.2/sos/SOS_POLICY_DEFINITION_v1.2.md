# Freestanding Imaging Steerage — Policy Definition v1.2

| Field | Value |
|---|---|
| Document ID | `HF-RP-SOC-IMG-001` |
| Platform policy ID | `d7441dd9-3bfe-405e-ae6c-0377204bbb7e` |
| Template | Derived from HF-RP-UM-MRI-001 v1.2 quality standard |
| Definition status | **DEFINITION_REVIEW_REQUIRED** |
| Mechanism | `SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL` |
| Intended scope band | `OUTPATIENT_IMAGING_SITE` |
| Synthetic analytics | Independent of definition approval; fixtures: reimbursement-sos-v1 known-answer $520 |

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
| Technical closure | **Not asserted PASS** — see `SOS_TECHNICAL_CLOSURE_VALIDATION_REPORT.json` |
| Release blockers | `SOS_RELEASE_BLOCKERS.json` (hard blockers) |
| Adverse outcomes | `ADVERSE_REVIEW_REQUIRED` / `ADVERSE_DETERMINATION_ISSUED` |
| Dec 4 fixtures | Unchanged |

## Release
DEFINITION_REVIEW_REQUIRED. Do not assert production readiness.
