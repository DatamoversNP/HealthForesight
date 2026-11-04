# PAP Therapy Initiation and Compliance — Representative Payer Definition

**Policy ID:** `3be7daf8-c492-46d4-9980-e9c860b8cca7`  
**Archetype:** `THERAPY_REHAB`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «PAP Therapy Initiation and Compliance»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: PAP initiation supplies

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | E0601 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A7030 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | A7034 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

