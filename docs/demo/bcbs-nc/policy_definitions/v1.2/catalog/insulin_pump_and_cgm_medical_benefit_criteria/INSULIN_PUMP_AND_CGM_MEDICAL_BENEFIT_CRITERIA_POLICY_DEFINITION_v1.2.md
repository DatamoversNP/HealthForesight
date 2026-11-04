# Insulin Pump and CGM Medical Benefit Criteria — Representative Payer Definition

**Policy ID:** `b6e298e6-0d9f-41d2-a8ac-1846448dd234`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Insulin Pump and CGM Medical Benefit Criteria»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Insulin pump + CGM supplies

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | E0784 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A9276 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A9277 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A9278 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | K0553 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | K0554 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

