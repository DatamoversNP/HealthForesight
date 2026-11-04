# Air Ambulance Medical Necessity Review — Representative Payer Definition

**Policy ID:** `993e9110-2623-4e41-b87c-ad8666cbb92c`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Air Ambulance Medical Necessity Review»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Fixed/rotary wing air ambulance + mileage

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | A0430 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A0431 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A0435 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A0436 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

