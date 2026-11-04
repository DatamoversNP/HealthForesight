# Partial Hospitalization and IOP Authorization — Representative Payer Definition

**Policy ID:** `1a49ed4c-f5f7-473b-9f39-b3caaefdc99c`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Partial Hospitalization and IOP Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: PHP/IOP behavioral health HCPCS

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | H0035 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | S9480 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0129 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0176 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | G0177 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

