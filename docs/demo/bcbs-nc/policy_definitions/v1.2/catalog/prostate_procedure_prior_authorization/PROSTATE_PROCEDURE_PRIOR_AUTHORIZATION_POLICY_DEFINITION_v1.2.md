# Prostate Procedure Prior Authorization — Representative Payer Definition

**Policy ID:** `60615c97-11f9-458c-880e-cb76ae3bd65a`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Prostate Procedure Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Prostatectomy / TURP representative

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 55866 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 55840 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 55842 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 55845 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 52601 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

