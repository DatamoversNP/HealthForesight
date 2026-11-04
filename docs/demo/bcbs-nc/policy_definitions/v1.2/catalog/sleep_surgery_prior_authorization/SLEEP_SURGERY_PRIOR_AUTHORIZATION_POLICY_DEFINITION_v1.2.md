# Sleep Surgery Prior Authorization — Representative Payer Definition

**Policy ID:** `12dc4c83-bc61-48d7-ada2-3648b16c7c6c`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Sleep Surgery Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: UPPP / hyoid / pharyngoplasty representative

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 42145 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 21685 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 42950 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

