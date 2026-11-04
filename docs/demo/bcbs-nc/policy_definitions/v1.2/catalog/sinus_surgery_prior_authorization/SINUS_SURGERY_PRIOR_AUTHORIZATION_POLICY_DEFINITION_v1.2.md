# Sinus Surgery Prior Authorization — Representative Payer Definition

**Policy ID:** `afd40d1a-198a-4be8-b21e-758ce5a2fcbf`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Sinus Surgery Prior Authorization»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Endoscopic sinus surgery family

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 31253 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31254 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31255 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31256 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31267 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31276 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31287 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 31288 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

