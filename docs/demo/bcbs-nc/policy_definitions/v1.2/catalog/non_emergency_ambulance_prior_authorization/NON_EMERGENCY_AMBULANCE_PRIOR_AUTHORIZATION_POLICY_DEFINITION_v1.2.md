# Non-Emergency Ambulance Prior Authorization — Representative Payer Definition

**Policy ID:** `37d49884-84d8-4dfe-b18a-9c2cdebc225b`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Non-Emergency Ambulance Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Ground ambulance ALS/BLS non-emergency + mileage

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | A0426 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A0428 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A0425 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

