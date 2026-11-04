# Ambulatory Surgery Center Preference — Representative Payer Definition

**Policy ID:** `ce65ce76-ea5b-4a7d-8260-84c11ae54bb2`  
**Archetype:** `SITE_OF_CARE`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Ambulatory Surgery Center Preference»

## Scope

- LOB: COMMERCIAL, MA
- States: NC
- Markets: ALL
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Representative ASC-eligible elective procedures

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 27447 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 29827 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43239 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 66984 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

