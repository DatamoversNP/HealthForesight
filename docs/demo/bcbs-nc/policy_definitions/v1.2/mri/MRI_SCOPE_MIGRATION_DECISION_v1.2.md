# MRI Scope Migration Decision — General OP MRI → Proposed Lumbar-Only (v1.2)

| Field | Value |
|---|---|
| Decision ID | `MRI-SCOPE-MIG-2026-11-03` |
| Status | **PROPOSED** — not activated |
| Baseline title/config | Outpatient MRI Prior Authorization (general OP MRI framing) |
| Proposed v1.2 band | Outpatient **lumbar spine** MRI (`72148` / `72149` / `72158` candidates) |
| Controlled reference | HF-RP-UM-MRI-001 **v1.1** remains the controlled narrative baseline |
| Structured proposal | v1.2 / v1.2.1 technical closure artifacts |

## Why this is a design change (not a doc tweak)

The historical platform object and demo title describe **general outpatient MRI**.  
v1.2 **proposes** narrowing operative anatomy to **lumbar spine** to:

1. Align candidate lever codes (72148/72149/72158)  
2. Prevent incorrect inheritance of orbit/face/neck LCD L34425 / A56729  
3. Make clinical criteria schedules anatomically coherent  

This must be recorded as a **versioned proposed scope change**.

## Explicit non-inheritance rules

| Artifact | Relationship to proposed lumbar-only definition |
|---|---|
| Frozen synthetic MRI demo (known-answer / causal DiD / FULLY_VALIDATED_DEMO) | **Must NOT silently inherit** lumbar-only operative meaning. Demo remains general OP MRI analytics fixture unless a separate approved migration renames/version-pins it. |
| Historical baselines / observations / predicted impacts on policy id `d403f101-…` | Remain interpretable under **pre-migration** general OP MRI framing; annotate analyses with `policy_scope_version=PRE_LUMBAR_NARROWING` until migration approved. |
| Cohorts built on broad MRI CPT sets (brain/spine/extremity) | Not automatically reclassified as lumbar-only. |
| Platform policy **name** | Remains “Outpatient MRI Prior Authorization” until product/clinical owners approve rename. |

## Impact assessment (required before activation)

| Area | Impact if activated without migration plan | Mitigation |
|---|---|---|
| Historical analytics continuity | Cohort mismatch / false trend breaks | Version-pin scope; dual-run period |
| Medicare link UX | L34425/A56729 may still appear as related partial | Applicability flags: not lumbar authority |
| Synthetic fixtures | Wrong clinical story if labeled lumbar-only | Keep fixture catalog_class SYNTHETIC; separate scope tag |
| Other body-region MRI demand | Would fall OUT_OF_BAND under proposed PA | Explicit product decision: expand schedule or separate policies |

## Decision record (unsigned)

| Role | Approve lumbar-only operative scope? | Date | Signature |
|---|---|---|---|
| Clinical owner | UNRESOLVED | | |
| Product owner | UNRESOLVED | | |
| Analytics owner (demo continuity) | UNRESOLVED | | |

**Until signed:** proposed lumbar-only band is specification-only; live enforcement and frozen demo semantics remain under pre-migration framing + DEFINITION_REVIEW_REQUIRED / OPERATIONAL_ACTIVATION_PROHIBITED.
