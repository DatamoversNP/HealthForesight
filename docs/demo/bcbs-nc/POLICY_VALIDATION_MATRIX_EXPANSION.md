# Policy Validation Matrix — Expansion (additive to frozen three)

| Policy | Type | Mechanical | Causal | Medicare provenance | Browser lifecycle | Class |
|---|---|---|---|---|---|---|
| Outpatient MRI PA | UM | PASS (prior) | SUPPORTED (synthetic DiD) | **NCD220.2 primary**; L34425/A56729 **PARTIAL** (orbit/face/neck only) | PASS (frozen) | FULLY_VALIDATED_DEMO |
| MPPR | Reimbursement | $600/+120 PASS | DESCRIPTIVE_ONLY | methodology note | PASS (frozen) | FULLY_VALIDATED_DEMO |
| SOS Freestanding Imaging | Reimbursement | $520/+260 PASS | DESCRIPTIVE_ONLY | — | PASS (frozen) | FULLY_VALIDATED_DEMO |
| NCCI PTP Bundling | Coding | $800 PASS (+ modifier-59 bypass) | DESIGN_POSSIBLE_DATA_INSUFFICIENT (eligible) | demo PTP pair | Workspace + calc PASS; full verdict browser pending | Mechanical validated |
| NCCI MUE Units | Coding | $100 PASS | DESIGN_POSSIBLE_DATA_INSUFFICIENT (eligible) | synthetic MUE labeled | Pending | Mechanical validated |
| OP Therapy Coverage | Coverage | $80 PASS | DESIGN_POSSIBLE_DATA_INSUFFICIENT | **L34428** (Palmetto JM) linked | Pending | PARTIAL_SYNTHETIC |
| Infusion Site-of-Care | Site-of-care | $3600 PASS | DESCRIPTIVE_ONLY | — | Pending | Mechanical validated |
| NCD 220.2 Coverage Study | Coverage | N/A | NOT_IDENTIFIABLE | NCD220.2 verified | Pending | PROVENANCE_VALIDATED |
| LCD L34425 NC Coverage | Coverage | N/A | NOT_IDENTIFIABLE | L34425+A56729 verified | Pending | PROVENANCE_VALIDATED |

OH portfolio count after seed: **289** (283 + 6 expansion).
