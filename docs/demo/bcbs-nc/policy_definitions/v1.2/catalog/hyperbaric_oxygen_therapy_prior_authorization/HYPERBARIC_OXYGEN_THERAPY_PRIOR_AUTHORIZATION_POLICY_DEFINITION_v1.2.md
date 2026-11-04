# Hyperbaric Oxygen Therapy Prior Authorization — Representative Payer Definition

**Policy ID:** `4ea16ea6-9434-4c0d-b864-cfc9c06cc20a`  
**Archetype:** `THERAPY_REHAB`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Hyperbaric Oxygen Therapy Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: HBOT physician attendance / facility

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT/HCPCS | 99183 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT/HCPCS | G0277 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

