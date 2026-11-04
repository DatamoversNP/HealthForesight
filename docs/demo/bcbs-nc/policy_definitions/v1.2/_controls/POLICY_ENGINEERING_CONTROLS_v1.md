# Policy Engineering Controls v1

**Source:** MRI v1.2.1 technical closure (frozen reference)  
**Apply to:** All nine Representative Payer policy packages  
**Do not:** Copy MRI clinical indication logic into non-MRI policies; expand catalog; alter December 4 frozen demo fixtures

## Independent control dimensions

1. **Structural / technical completeness** — schema, evidence, decision determinism, tests  
2. **Analytical validation** — FULLY_VALIDATED_DEMO (or not) independently  
3. **Operational authorization** — requires cleared RELEASE_BLOCKERS + owner sign-off  

A package may be structurally closed while activation remains PROHIBITED.

## Required controls (R1–R8)

| ID | Control | Requirement |
|---|---|---|
| R1 | Strict codeset schema | Every code record validates `POLICY_CODESET_RECORD.schema.json`; optional fields explicitly null |
| R2 | VERIFIED_SOURCE evidence | Non-null evidence_id, source_version, retrieved_at, checksum, applicability_period_start |
| R3 | Non-operative proposed rules | Unsigned criteria/schedules cannot emit operative APPROVED / ADVERSE_DETERMINATION_ISSUED / APPLY_EDIT as live determination |
| R4 | Urgency-before-routine | Where clinical/UM pathways exist: DT-URGENCY before routine evidence/incomplete branches. Payment-only mechanisms document N/A with rationale |
| R5 | Adverse split | `ADVERSE_REVIEW_REQUIRED` ≠ `ADVERSE_DETERMINATION_ISSUED`; issued requires reviewer, notice, appeal, timestamps, audit |
| R6 | Scope migration | Material scope changes recorded as versioned decisions; historical analytics remain interpretable |
| R7 | Deterministic tests | Positive, negative, boundary, missing-data coverage; first-match ordered tables |
| R8 | Status triad | DEFINITION_REVIEW_REQUIRED · FULLY_VALIDATED_DEMO (independent) · OPERATIONAL_ACTIVATION_PROHIBITED |

## Mandatory artifacts per policy

- `*_POLICY_DEFINITION_v1.2.md` (or later)  
- `*_CODESET_AND_APPLICABILITY.json` + schema validation  
- `*_DECISION_TABLES.json`  
- `*_OPERATIONAL_REQUIREMENTS_MATRIX.md`  
- `*_SOURCE_EVIDENCE_REGISTER.md`  
- `*_POLICY_ACCEPTANCE_TESTS.json`  
- `*_CONFIG_RECONCILIATION_REPORT.md`  
- `*_RELEASE_BLOCKERS.json` (hard blockers)  
- `*_TECHNICAL_CLOSURE_VALIDATION_REPORT.json` (PASS only after independent checks)  
- Criteria/mechanism schedule as appropriate (clinical **or** payment/coding schedule — mechanism-specific)

## Release blocker rule

Unresolved dependencies listed as RELEASE_BLOCKERS **block** operational activation. They are not warnings.
