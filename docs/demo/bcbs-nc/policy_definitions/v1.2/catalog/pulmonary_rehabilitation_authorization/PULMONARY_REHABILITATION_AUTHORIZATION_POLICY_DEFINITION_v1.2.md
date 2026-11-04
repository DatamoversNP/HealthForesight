# Pulmonary Rehabilitation Authorization — Representative Payer Definition

**Policy ID:** `f0ebff27-e3b9-4998-8d35-9cfe3c81d608`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Pulmonary Rehabilitation Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Pulmonary rehab sessions

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT/HCPCS | G0424 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT/HCPCS | 94625 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT/HCPCS | 94626 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

