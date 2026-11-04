# Durable Medical Equipment Quantity Limits — Representative Payer Definition

**Policy ID:** `2b1a9c48-8352-4fd5-be6f-d12c7647de7d`  
**Archetype:** `PHARMACY_SPECIALTY`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Durable Medical Equipment Quantity Limits»

## Scope

- LOB: COMMERCIAL, MEDICARE, MA
- States: NC
- Markets: ALL
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Representative DME quantity-limit anchors

| System | Code | Status | Evidence |
|---|---|---|---|
| HCPCS | E0601 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | E0431 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| HCPCS | K0001 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

