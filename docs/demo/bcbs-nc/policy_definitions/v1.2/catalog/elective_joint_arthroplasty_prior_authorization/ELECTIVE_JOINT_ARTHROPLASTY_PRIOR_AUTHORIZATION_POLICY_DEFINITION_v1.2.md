# Elective Joint Arthroplasty Prior Authorization — Representative Payer Definition

**Policy ID:** `fae6bd6d-9a3f-4873-942c-9cd2bfb2b68f`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Elective Joint Arthroplasty Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: THA / TKA / TSA primary arthroplasty

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 27130 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 27447 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 23472 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

