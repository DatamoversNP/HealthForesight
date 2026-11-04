# MRI Config Reconciliation Report (v1.2.1 technical closure)

**Live policy:** `d403f101-08dd-45c9-ab83-d42e37c62018`  
**Spec:** HF-RP-UM-MRI-001 v1.2 / v1.2.1  
**Controlled baseline:** v1.1  
**Migration stance:** **Do not overwrite active executable rules or frozen demo fixtures without explicit approved migration.**  
**Scope migration:** Proposed lumbar-only band recorded in `MRI_SCOPE_MIGRATION_DECISION_v1.2.md` — live title remains general OP MRI until signed; historical analytics tagged conceptually as `PRE_LUMBAR_NARROWING`.

| Field | Live value | v1.2 required | Action now | Overwrite live? |
|---|---|---|---|---|
| anatomical scope framing | General outpatient MRI | Proposed lumbar-only (unsigned) | Record migration decision; dual-run until signed | **No** — frozen demo must not silently inherit |
| markets | NYC, DFW | NC-only / schedule | Quarantine defect in docs + backlog fix ticket | Only with approval |
| procedure_codes scope | 99213,99214,72148,72149 | Exclude E/M; align lumbar set | Document EXCLUDE; backlog | Only with approval |
| policy_levers codes | 72148,72149,72158 | Match approved schedule | Align when schedule signed | Only with approval |
| enforcement.override_allowed | false | Exceptions required | Spec only until ops matrix approved | No silent change |
| assumptions elasticity -0.3 | present as sourced | UNESTIMATED/demo | Relabel in metadata when approved honesty patch runs | Honesty patch OK if non-behavioral |
| Medicare L34425/A56729 links | present | PARTIAL / not lumbar authority | Keep links; enforce applicability flags in rule engine metadata | Do not delete evidence links |
| NCCI synthetic pair | may be linked | SYNTHETIC_FIXTURE | Relabel | Do not claim CMS published |
| versions v1/v2 same start | collision | Resolve precedence | Open decision | No implicit pick |
| analytical lifecycle | COMPLETED baselines/simulates exist | FULLY_VALIDATED_DEMO independent | Preserve fixtures | **Do not break demo** |
| definition status | UI ACTIVE | DEFINITION_REVIEW_REQUIRED for enforcement | Dual-status documentation | Do not confuse UI ACTIVE with clinical approval |

## Approved honesty patches (safe without clinical approval)

These change **labels/classification only**, not clinical criteria or denial behavior:

1. Tag elasticity/substitution as `UNESTIMATED` / Layer B.  
2. Tag NCCI demo as `SYNTHETIC_FIXTURE`.  
3. Add enterprise flag `definition_status=DEFINITION_REVIEW_REQUIRED`.  
4. Record `lcd_clinical_match=PARTIAL` / `not_authority_for_lumbar_pa` on L34425/A56729 links.

## Explicitly blocked without human approval

- Rewriting clinical criteria into executable APPROVED/DENIED automation  
- Inventing UM clocks or notice templates  
- Changing frozen MRI known-answer / causal demo numbers  
- Deleting Medicare source documents from inventory  
