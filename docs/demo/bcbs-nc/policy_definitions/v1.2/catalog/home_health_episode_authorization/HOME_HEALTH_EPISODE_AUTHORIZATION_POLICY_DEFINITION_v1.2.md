# Home Health Episode Authorization — Representative Payer Definition

**Policy ID:** `961da9ed-a175-4746-bdf0-304e6b5ab071`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Home Health Episode Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Home health discipline visit HCPCS

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | G0151 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0152 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0153 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0299 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0300 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

