# MRI Prior Authorization — Policy Definition v1.2

| Field | Value |
|---|---|
| Document ID | `HF-RP-UM-MRI-001` |
| Baseline | v1.1 reference specification (controlled) |
| Structured package | v1.2 / **v1.2.1 technical closure** (proposed; not activated) |
| Platform policy ID | `d403f101-08dd-45c9-ab83-d42e37c62018` |
| Date | 2026-11-03 |
| Definition status | **DEFINITION_REVIEW_REQUIRED** |
| Synthetic analytics | May remain **FULLY_VALIDATED_DEMO** independently |
| Operational activation | **PROHIBITED** until clinical/compliance approvals recorded |
| Scope migration | See `MRI_SCOPE_MIGRATION_DECISION_v1.2.md` (general OP MRI → proposed lumbar-only) |

## 0. Change from v1.1

v1.1 established architecture, defect quarantine, and three-layer separation.  
v1.2 adds **executable structures**: versioned code schedule, indication decision tables (proposed representative, not approved), operational requirements matrix, decision outcomes model, acceptance tests, and config reconciliation — without inventing payer approvals or proprietary criteria text.

Evidence tags: `VERIFIED_SOURCE` | `REPRESENTATIVE_DESIGN` | `PROPOSED_REPRESENTATIVE_NOT_APPROVED` | `SYNTHETIC_FIXTURE` | `UNRESOLVED` | `CONFIG_DEFECT`

## 1. Three-layer separation (normative — unchanged)

| Layer | Contents | Operative? |
|---|---|---|
| A. Policy definition | Scope, codes, clinical criteria, exceptions, outcomes | Only after approval |
| B. Analytical assumptions | Elasticity, lag, substitution, causal params | Never as enforcement |
| C. Synthetic fixtures | Known-answer demo calculations | Never as clinical authority |

## 2. Intended anatomical scope (resolved design intent)

| Scope band | Status | Notes |
|---|---|---|
| **Lumbar spine MRI** (candidate platform codes 72148/72149/72158) | `REPRESENTATIVE_DESIGN` — intended primary PA band pending product approval | Do **not** apply L34425/A56729 |
| Orbit / face / neck MRI (70540/70542/70543) | Separate clinical domain | Governed only if a distinct product adoption exists; **not** this PA’s lumbar band |
| Brain / other body regions | `UNRESOLVED` for this definition | May be added only via versioned code schedule + criteria |

**Design decision (v1.2):** This Representative Payer MRI PA definition’s **intended operative anatomy** is **outpatient lumbar spine MRI**, aligning candidate platform lever codes and avoiding orbit/face/neck LCD inheritance. Expansion to other anatomies requires a new criteria schedule version.

## 3. Policy identity

- **Goal:** Prospective clinical review of selected non-emergent outpatient **lumbar** MRI requests against an approved criteria schedule, protecting medically necessary access.  
- **Non-goals:** Automatic denial; Medicare FFS adjudication; E/M targeting; volume reduction for its own sake; treating synthetic analytics as clinical authority.

## 4. Companion artifacts (normative)

| Artifact | Role |
|---|---|
| `MRI_CLINICAL_CRITERIA_SCHEDULE.md` | Indication tables + **non-operative lock** |
| `MRI_CODESET_AND_APPLICABILITY.json` | Versioned CPT schedule + Medicare applicability |
| `MRI_CODESET_RECORD.schema.json` | Strict per-code schema (required keys; explicit nullability) |
| `MRI_OPERATIONAL_REQUIREMENTS_MATRIX.md` | NC commercial ops matrix (unresolved clocks explicit) |
| `MRI_DECISION_TABLES.json` | Ordered branches; urgency before evidence; adverse split |
| `MRI_SCOPE_MIGRATION_DECISION_v1.2.md` | General OP MRI → proposed lumbar-only (unsigned) |
| `MRI_SOURCE_EVIDENCE_REGISTER.md` | Traceability |
| `MRI_POLICY_ACCEPTANCE_TESTS.json` | Gate tests (pos/neg/boundary/missing-data) |
| `MRI_CONFIG_RECONCILIATION_REPORT.md` | Live config vs v1.2 — **no silent overwrite** |
| `MRI_V1_2_TECHNICAL_CLOSURE_VALIDATION_REPORT.json` | Machine-readable closure results |

## 5. Decision outcome vocabulary (normative)

| Outcome | Meaning |
|---|---|
| `NOT_APPLICABLE` | Product/service/setting out of scope — not a denial |
| `PENDING_INFORMATION` | Missing necessary clinical info on **standard** path; clock tracked |
| `CLINICAL_REVIEW_REQUIRED` | Requires qualified clinical reviewer (includes emergency/urgent routing) |
| `APPROVED` | Meets **signed** criteria / exception granted — blocked while schedule unsigned |
| `ADVERSE_REVIEW_REQUIRED` | Referral into authorized adverse process — **not** a final denial |
| `ADVERSE_DETERMINATION_ISSUED` | Completed adverse determination: reviewer + notice + appeal + timestamps + audit |
| `MANUAL_SCOPE_REVIEW` | Ambiguous code/product mapping — **no auto PA imposition, no auto denial** |

Retired: `ADVERSE_DETERMINATION_AUTHORIZED` (ambiguous).

### Ambiguous mapping behavior (refined)

1. Do **not** automatically deny.  
2. Do **not** automatically impose PA on an ambiguous service.  
3. Route to authorized administrative/clinical mapping review.  
4. Preserve applicable member protections and processing deadlines (`UNRESOLVED` exact clocks by product).  
5. Record resolution, effective version, and reviewer.

### Evaluation order (normative)

`DT-ELIGIBILITY` → `DT-APPLICABILITY` → **`DT-URGENCY`** → `DT-EVIDENCE` → `DT-CLINICAL`.  
Emergency/urgent indicators short-circuit past routine incomplete-information and conservative-care gates.

### Proposed criteria lock (normative)

Unsigned clinical schedule rows may execute only in isolated `SYNTHETIC_SIMULATION` and must not emit operative `APPROVED` or `ADVERSE_DETERMINATION_ISSUED`.

## 6. Release classification

| Dimension | Status |
|---|---|
| Definition | DEFINITION_REVIEW_REQUIRED |
| Synthetic analytics | FULLY_VALIDATED_DEMO (independent) |
| Operational activation | OPERATIONAL_ACTIVATION_PROHIBITED |
| Source applicability | PARTIALLY_RECONCILED |
| Structural technical closure (v1.2.1) | See `MRI_V1_2_TECHNICAL_CLOSURE_VALIDATION_REPORT.json` |
| Production readiness / clinically complete | **Not asserted** — do not self-approve clinical, legal, product, or guardrail thresholds |
