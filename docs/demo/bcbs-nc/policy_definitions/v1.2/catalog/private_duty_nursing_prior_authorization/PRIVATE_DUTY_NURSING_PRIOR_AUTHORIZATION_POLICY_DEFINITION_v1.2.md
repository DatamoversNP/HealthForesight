# Private Duty Nursing Prior Authorization — Representative Payer Definition

**Policy ID:** `4fc8ae9e-51d8-47b2-a1f2-fee8697bf01e`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Private Duty Nursing Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Private duty / RN/LPN nursing hours

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | T1000 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | T1002 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | T1003 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

