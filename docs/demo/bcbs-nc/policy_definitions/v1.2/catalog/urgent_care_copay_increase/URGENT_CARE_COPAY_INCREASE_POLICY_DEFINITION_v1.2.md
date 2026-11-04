# Urgent Care Copay Increase — Representative Payer Definition

**Policy ID:** `b815e37b-98c9-40b4-8e17-b0821566fcaf`  
**Archetype:** `PAYMENT_REIMBURSEMENT`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Urgent Care Copay Increase»

## Scope

- LOB: COMMERCIAL
- States: NC
- Markets: ALL
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: UC E/M anchors — copay amount is Representative design parameter UNRESOLVED numeric

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 99213 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 99214 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

