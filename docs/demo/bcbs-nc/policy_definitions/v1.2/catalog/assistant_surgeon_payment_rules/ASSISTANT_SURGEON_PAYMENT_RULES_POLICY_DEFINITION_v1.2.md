# Assistant Surgeon Payment Rules — Representative Payer Definition

**Policy ID:** `b889bcf0-0c68-4950-bd24-4ac656ebe0ae`  
**Archetype:** `PAYMENT_REIMBURSEMENT`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Assistant Surgeon Payment Rules»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Assistant surgeon modifiers — % reduction is Representative design not contracted rate

| System | Code | Status | Evidence |
|---|---|---|---|
| MODIFIER | 80 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| MODIFIER | 81 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| MODIFIER | 82 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| MODIFIER | AS | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

