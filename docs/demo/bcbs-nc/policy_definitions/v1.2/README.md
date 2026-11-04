# Policy definitions v1.2 index

Updated: 2026-11-03T15:32:32.189928+00:00

## Control dimensions (keep separate)

| Dimension | Meaning |
|---|---|
| Structurally / technically closed | Schema, evidence, decision determinism, tests |
| Analytics validated | FULLY_VALIDATED_DEMO (independent) |
| Operationally authorized | RELEASE_BLOCKERS cleared + owner approval |

## Reference implementation

**MRI v1.2.1** is the frozen reference for structural policy-definition quality (`mri/`).  
Reusable controls: [`_controls/POLICY_ENGINEERING_CONTROLS_v1.md`](./_controls/POLICY_ENGINEERING_CONTROLS_v1.md).

Board: [`NINE_POLICY_TECHNICAL_CLOSURE_BOARD.json`](./NINE_POLICY_TECHNICAL_CLOSURE_BOARD.json)

| Policy | Folder | Structural closure | Activation |
|---|---|---|---|
| Outpatient MRI PA | [mri/](./mri/) | Provisional PASS (independent verification required) | PROHIBITED |
| MPPR | [mppr/](./mppr/) | Controls applied — not closed PASS | PROHIBITED |
| Imaging steerage (SOS) | [sos/](./sos/) | Controls applied — not closed PASS | PROHIBITED |
| NCCI PTP | [ptp/](./ptp/) | Controls applied — not closed PASS | PROHIBITED |
| NCCI MUE | [mue/](./mue/) | Controls applied — not closed PASS | PROHIBITED |
| OP Therapy | [therapy/](./therapy/) | Controls applied — not closed PASS | PROHIBITED |
| Infusion SOC | [infusion/](./infusion/) | NOT_CLOSED (empty codeset blocker) | PROHIBITED |
| NCD 220.2 study | [ncd_study/](./ncd_study/) | Controls applied — not closed PASS | PROHIBITED |
| LCD L34425 study | [lcd_study/](./lcd_study/) | Controls applied — not closed PASS | PROHIBITED |

Do **not** expand the catalog or change December 4 demonstration fixtures in this workstream.  
Do **not** copy MRI lumbar clinical logic into other mechanisms.
