# Lifecycle Validation Matrix

**Generated:** 2026-11-03T10:52:38.727305+00:00

## Rule

FULLY_VALIDATED_DEMO requires independent calculation/lineage checks. Artifact presence alone → ARTIFACTS_PRESENT_UNVALIDATED.

## Counts

| Class | N |
|-------|--:|
| ARTIFACTS_PRESENT_UNVALIDATED | 254 |
| BLOCKED | 4 |
| FULLY_VALIDATED_DEMO | 3 |
| INAPPLICABLE_STAGE | 11 |
| PARTIAL | 11 |

Artifact full B+P+O (presence only): **257** / 283
Verdict without full B+P+O: **8**
MPPR known-answer vertical seeded: **True**

## December 4 readiness

- Claim completion: **False**
- Reason: FULLY_VALIDATED_DEMO limited to MRI + seeded reimbursement engines (MPPR=True, SOS=True); 254 unvalidated artifact rows; browser gates required; portfolio causal IMPACT_ASSESSABLE remains 0.

## Gap root causes (26 incomplete B+P+O)

- `CATALOG_ONLY_UNSEEDED`: 8
- `VERDICT_WITHOUT_BASELINE`: 8
- `NO_MECHANISM_SPECIFIC_ANALYTICS`: 4
- `INSUFFICIENT_OR_OUT_OF_SCOPE_CLAIMS`: 3
- `PREDICTION_ONLY_TEST_OR_ORPHAN`: 3

## Verdict-ready without complete B+P+O (8)

- Cardiac Stress Testing Prior Authorization — VERDICT_WITHOUT_BASELINE
- CAR-T and Cellular Therapy Prior Authorization — VERDICT_WITHOUT_BASELINE
- Diagnostic Cardiac Catheterization Appropriateness — VERDICT_WITHOUT_BASELINE
- Insulin Pump and CGM Medical Benefit Criteria — VERDICT_WITHOUT_BASELINE
- Interventional Pain Regenerative Injection Noncoverage — VERDICT_WITHOUT_BASELINE
- Intrathecal Drug Pump Prior Authorization — VERDICT_WITHOUT_BASELINE
- Oncology Genomic Profiling Prior Authorization — VERDICT_WITHOUT_BASELINE
- Prosthetic Limb Prior Authorization — VERDICT_WITHOUT_BASELINE

## Fully validated demo policies

- **Freestanding Imaging Steerage** (`d7441dd9-3bfe-405e-ae6c-0377204bbb7e`): Site-of-service payment differential known-answer (reimbursement-sos-v1); hospital OP % of allowed; not UM elasticity.
- **Multiple Procedure Payment Reduction** (`d0eeb370-df14-4478-8755-dad6c3a35a47`): MPPR payment-rule vertical with known-answer financial checks (reimbursement-mppr-v1); not UM elasticity.
- **Outpatient MRI Prior Authorization** (`d403f101-08dd-45c9-ab83-d42e37c62018`): MRI UM lifecycle: claims-backed baseline, elasticity prediction, observations, OH↔PV alignment evidence, browser gates.
