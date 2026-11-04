# Bariatric Revisional Surgery Prior Authorization — Representative Payer Definition

**Policy ID:** `d8318a2f-f0d8-47c2-b54c-a9f936d1aeff`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Bariatric Revisional Surgery Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Revisional / conversion bariatric procedures

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 43775 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43644 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43645 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43848 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43860 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

