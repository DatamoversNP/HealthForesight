# Spine Surgery Prior Authorization — Representative Payer Definition

**Policy ID:** `ef853bdb-40fb-4e68-8013-a4f8bf8d9b2c`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Spine Surgery Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA
- States: NC
- Markets: ALL
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Mixed decompression/fusion/instrumentation — prefer split policies when product-defined

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 63030 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 63047 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 22612 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 22633 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 22842 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 22853 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

