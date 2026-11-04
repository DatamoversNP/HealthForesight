# Bariatric Surgery Prior Authorization — Representative Payer Definition

**Policy ID:** `56901c32-9b11-484e-aed3-dd100b4160f8`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Bariatric Surgery Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Primary bariatric sleeve/bypass

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 43775 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43644 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43645 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43846 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 43847 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

