# Telehealth Covered Services List — Representative Payer Definition

**Policy ID:** `e5a26938-d36d-40f8-9ebc-acc30db80c53`  
**Archetype:** `MEDICAL_NECESSITY_COVERAGE`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Telehealth Covered Services List»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Representative telehealth-covered E/M + psychotherapy

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 99213 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 99214 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 99441 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 99442 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 99443 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 90832 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 90834 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

