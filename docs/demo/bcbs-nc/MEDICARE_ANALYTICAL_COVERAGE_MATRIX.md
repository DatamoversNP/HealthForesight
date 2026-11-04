# Medicare Analytical Coverage Matrix

How Medicare authorities feed the lifecycle (configuration → applicability → analytics).

| Scenario | Mechanism engine | Medicare rules used | Mechanical calc | Causal status | Validation class |
|---|---|---|---|---|---|
| Outpatient MRI PA (frozen) | UM elasticity + DiD | NCD220.2, L34425, A56729, PTP demo | Utilization / DiD synthetic | **CAUSAL_ESTIMATE_SUPPORTED** (synthetic) | FULLY_VALIDATED_DEMO |
| MPPR (frozen) | reimbursement-mppr-v1 | Methodology note only | $600 / +$120 | DESCRIPTIVE_ONLY | FULLY_VALIDATED_DEMO |
| SOS (frozen) | reimbursement-sos-v1 | — | $520 / +$260 | DESCRIPTIVE_ONLY | FULLY_VALIDATED_DEMO |
| NCCI PTP bundling | reimbursement-ncci-ptp-v1 | PTP demo pair | $800 | DESCRIPTIVE_ONLY | Mechanical PASS — promote after browser gates |
| NCCI MUE units | reimbursement-ncci-mue-v1 | Demo MUE 97110=4 | $100 | DESCRIPTIVE_ONLY | Mechanical PASS — synthetic MUE labeled |
| OP therapy coverage | coverage-therapy-v1 | (none yet — needs therapy LCD) | $80 | NOT_IDENTIFIABLE / DESCRIPTIVE | PARTIAL_SYNTHETIC |
| Infusion site-of-care | infusion-soc-v1 | — | $3600 | DESCRIPTIVE_ONLY | Mechanical PASS |
| NCD 220.2 coverage study | COVERAGE_DETERMINATION | NCD220.2 | Provenance | NOT_IDENTIFIABLE | PROVENANCE_VALIDATED |
| LCD L34425 coverage study | COVERAGE_DETERMINATION | L34425, A56729 | Provenance | NOT_IDENTIFIABLE | PROVENANCE_VALIDATED |

## Effect-layer rule

Always separate: **mechanical payment** | **predicted behavior** | **observed descriptive** | **causal estimate (only if supported)**.
