# Policy definition documents (Dec 4 configured set)

Generated: 2026-11-03 14:38 UTC

Complete definitions for frozen Dec 4 + expansion policies.

| # | Policy | Type | Assumptions | Guardrails | Codes | Medicare links | Docs |
|--:|---|---|---:|---:|---:|---:|---|
| 1 | Outpatient MRI Prior Authorization | `PRIOR_AUTH` | 4 | 4 | 0 | 5 | [Outpatient_MRI_Prior_Authorization.md](./Outpatient_MRI_Prior_Authorization.md) · [Outpatient_MRI_Prior_Authorization.json](./Outpatient_MRI_Prior_Authorization.json) |
| 2 | Multiple Procedure Payment Reduction | `PAYMENT_POLICY` | 3 | 2 | 3 | 0 | [Multiple_Procedure_Payment_Reduction.md](./Multiple_Procedure_Payment_Reduction.md) · [Multiple_Procedure_Payment_Reduction.json](./Multiple_Procedure_Payment_Reduction.json) |
| 3 | Freestanding Imaging Steerage | `SITE_OF_CARE` | 3 | 2 | 3 | 0 | [Freestanding_Imaging_Steerage.md](./Freestanding_Imaging_Steerage.md) · [Freestanding_Imaging_Steerage.json](./Freestanding_Imaging_Steerage.json) |
| 4 | NCCI Procedure-to-Procedure Bundling | `CODING_AND_BILLING` | 3 | 3 | 2 | 1 | [NCCI_Procedure-to-Procedure_Bundling.md](./NCCI_Procedure-to-Procedure_Bundling.md) · [NCCI_Procedure-to-Procedure_Bundling.json](./NCCI_Procedure-to-Procedure_Bundling.json) |
| 5 | NCCI Medically Unlikely Units | `CODING_AND_BILLING` | 2 | 2 | 1 | 1 | [NCCI_Medically_Unlikely_Units.md](./NCCI_Medically_Unlikely_Units.md) · [NCCI_Medically_Unlikely_Units.json](./NCCI_Medically_Unlikely_Units.json) |
| 6 | Outpatient Therapy Coverage and Payment | `COVERAGE` | 2 | 2 | 2 | 2 | [Outpatient_Therapy_Coverage_and_Payment.md](./Outpatient_Therapy_Coverage_and_Payment.md) · [Outpatient_Therapy_Coverage_and_Payment.json](./Outpatient_Therapy_Coverage_and_Payment.json) |
| 7 | Infusion Site-of-Care Optimization | `SITE_OF_CARE` | 3 | 2 | 0 | 0 | [Infusion_Site-of-Care_Optimization.md](./Infusion_Site-of-Care_Optimization.md) · [Infusion_Site-of-Care_Optimization.json](./Infusion_Site-of-Care_Optimization.json) |
| 8 | NCD 220.2 MRI Coverage Change Study | `COVERAGE` | 1 | 1 | 6 | 2 | [NCD_220_2_MRI_Coverage_Change_Study.md](./NCD_220_2_MRI_Coverage_Change_Study.md) · [NCD_220_2_MRI_Coverage_Change_Study.json](./NCD_220_2_MRI_Coverage_Change_Study.json) |
| 9 | LCD L34425 NC MRI Coverage Criteria | `COVERAGE` | 1 | 1 | 3 | 4 | [LCD_L34425_NC_MRI_Coverage_Criteria.md](./LCD_L34425_NC_MRI_Coverage_Criteria.md) · [LCD_L34425_NC_MRI_Coverage_Criteria.json](./LCD_L34425_NC_MRI_Coverage_Criteria.json) |

Bundle: [ALL_POLICIES_BUNDLE.json](./ALL_POLICIES_BUNDLE.json)

## MRI reference-quality specification (post-review)

The exported MRI `.md`/`.json` above reflect **live platform configuration**, including known defects (NYC/DFW markets, E/M codes in scope, etc.).

For the review-standard definition:

- [Outpatient_MRI_Prior_Authorization_REFERENCE_SPEC.md](./Outpatient_MRI_Prior_Authorization_REFERENCE_SPEC.md) — source-grounded specification with evidence tags; **DEFINITION_REVIEW_REQUIRED**
- [Outpatient_MRI_Prior_Authorization_DISCREPANCY_REPORT.md](./Outpatient_MRI_Prior_Authorization_DISCREPANCY_REPORT.md) — field-by-field live-config vs reference; safe implementation order

**Do not** treat the live export as authoritative. Analytical lifecycle readiness ≠ policy-definition readiness.
