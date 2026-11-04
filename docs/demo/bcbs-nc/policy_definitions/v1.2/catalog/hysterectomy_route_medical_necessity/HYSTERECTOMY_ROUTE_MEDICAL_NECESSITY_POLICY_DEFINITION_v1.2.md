# Hysterectomy Route Medical Necessity — Representative Payer Definition

**Policy ID:** `dbab1f6e-ca9a-459d-9091-3fc2a412cf47`  
**Archetype:** `PRIOR_AUTH_UM`  
**Classification:** `REPRESENTATIVE_PAYER_POLICY`  
**Not claiming:** Authoritative Blue Cross NC operative proprietary policy text

## Intent

Representative Payer configuration for catalog policy «Hysterectomy Route Medical Necessity»

## Scope

- LOB: COMMERCIAL, MA, MEDICAID
- States: NC
- Markets: NC
- Note: Claim markets are for cohort matching in synthetic claims; states define Representative NC jurisdiction. NC geography ≠ complete configuration.

## Codeset

- Status: **CANDIDATE_SCHEDULE**
- Notes: Abdominal / vaginal / laparoscopic hysterectomy

| System | Code | Status | Evidence |
|---|---|---|---|
| CPT | 58150 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 58260 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 58570 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 58571 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 58572 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |
| CPT | 58573 | CANDIDATE_INCLUDE | REPRESENTATIVE_DESIGN |

## Governance

- Definition status: `DEFINITION_COMPLETE_CANDIDATE`
- Operational activation: **PROHIBITED**

