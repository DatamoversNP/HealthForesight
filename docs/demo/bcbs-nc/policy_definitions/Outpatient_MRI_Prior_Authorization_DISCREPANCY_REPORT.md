# MRI PA — Field-by-field discrepancy report

**Compared:** live platform config for `d403f101-08dd-45c9-ab83-d42e37c62018`  
**Against:** `Outpatient_MRI_Prior_Authorization_REFERENCE_SPEC.md`  
**Date:** 2026-11-03  

**Rule for Cursor implementation:** implement **only** corrections that are (a) `CONFIG_DEFECT` fixes with verified evidence, or (b) explicitly approved policy decisions. Do **not** invent clinical criteria, numeric elasticities, or guardrail thresholds to “complete” the record.

| # | Field / area | Live config today | Reference requirement | Severity | Allowed next action |
|--:|---|---|---|---|---|
| 1 | Markets | `NYC`, `DFW` with `jurisdiction: NC` | NC commercial markets only (or empty until product schedule) | **Critical** | Correct/quarantine NYC/DFW |
| 2 | Procedure scope | `99213`, `99214`, `72148`, `72149` | Remove E/M from PA targets; MRI codes via approved schedule only | **Critical** | Remove 99213/99214 from PA targets |
| 3 | Lever vs scope codes | Lever has `72158`; scope omits it | Single aligned code schedule | **High** | Align or fail closed to MANUAL_SCOPE_REVIEW |
| 4 | Clinical criteria | None | Approved indication-specific criteria schedule required | **Critical** | Leave UNRESOLVED — do not invent |
| 5 | Enforcement | `HARD`, `override_allowed: false` | Exceptions, emergency/urgent, appeals required | **Critical** | Set override/exception paths; do not invent legal clocks |
| 6 | Assumptions | Elasticity `-0.3`, substitution `0.15`, lag `60` presented as sourced | Mark UNESTIMATED / demo-only until evidence | **High** | Relabel; do not fabricate studies |
| 7 | Guardrails | +20% util / related generic thresholds | Product-specific, owner-approved clinical/access/finance set | **High** | Quarantine as non-approved monitoring placeholders |
| 8 | Medicare L34425 / A56729 | Linked as MRI PA authorities | Partial orbit/face/neck only — not lumbar/brain portfolio | **Critical** | Keep as PARTIAL related; never full-portfolio authority |
| 9 | NCD 220.2 | Linked | Valid national MRI reference; commercial adoption UNRESOLVED | **Medium** | Keep as reference; document program boundary |
| 10 | NCCI PTP demo | Present as Medicare-linked coding edit | SYNTHETIC_FIXTURE only | **High** | Relabel; never claim CMS published pair |
| 11 | Versioning | v1 & v2 both start 2024-01-01 | Immutable IDs, supersession, rationale, approvals | **High** | Do not silently pick a winner |
| 12 | Analytical strategy stamp | Empty / incomplete vs claimed lifecycle | Separate FULLY_VALIDATED_DEMO analytics from definition readiness | **Medium** | Keep analytics status; do not equate to definition approval |
| 13 | Provenance flag | `MISSING_AUTHORITATIVE_SOURCE` while links exist | Distinct catalog vs linked-source meanings | **Medium** | Document both fields |
| 14 | Definition status | Platform `ACTIVE` | DEFINITION_REVIEW_REQUIRED for enforcement | **Critical** | Do not treat ACTIVE UI status as clinical approval |

## Recommended Cursor work order (safe)

1. Quarantine/correct **#1, #2, #3, #8, #10** (config defects with evidence).  
2. Relabel **#6, #7, #12, #13** (honesty / separation of layers).  
3. **Stop** before inventing **#4, #5 clocks, #7 thresholds** — those need human clinical/compliance decisions.  
4. Keep synthetic MRI lifecycle as FULLY_VALIDATED_DEMO; keep definition as DEFINITION_REVIEW_REQUIRED.

## What this report does *not* authorize

- Generating a complete clinical decision table from the model  
- Claiming BCBS NC verbatim policy text  
- Treating L34425/A56729 as lumbar MRI PA authority  
- Promoting synthetic elasticities into operative policy rules  
