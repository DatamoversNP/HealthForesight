# Home Infusion Preference — Representative Payer Definition

**Policy ID:** `b5d48dc5-2d6a-4a32-b3c7-54d4f9e77b77`  
**Archetype:** `SITE_OF_CARE`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Home Infusion Preference»

## Scope

- LOB: COMMERCIAL, MA
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Infusion admin — prefer home when clinically appropriate

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 96413 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 96365 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

