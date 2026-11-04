# Day 1 Lifecycle Execution Progress

Generated: `2026-11-04T09:33:43.931081+00:00`

## Headline (execution, not catalog health)

| Metric | Count |
|---|---|
| Definition-complete universe | 267 |
| Lifecycle attempted so far | **34** |
| Mechanism execution success (tightened rule) | **10** |
| Supported lifecycle complete | **33** |
| Baseline PASS | 8 |
| Prediction PASS | 31 |
| Observation PASS | 3 |
| Prediction without claim cohort (not counted as mech success) | 23 |
| Unresolved definitions retained | 22 |
| Approved live levers | **0** (156 candidate persisted) |

**Success rule:** baseline PASS **or** (prediction PASS **and** observation PASS) **or** verify/provenance bounded modes. Candidate levers ≠ approved.

## Batch 0 — Dec4 nine verify
- 9/9 mechanism execution success (verify-only; KA freeze preserved)
- MRI levers classified `FROZEN_DEMO_LEVERS`

## Batch 1 — PRIOR_AUTH (25)
- 1 baseline PASS (Cardiac CT Angiography)
- 24 baselines DATA_INSUFFICIENT (codes not in NC claim markets)
- Predictions often PASS but observation DATA_INSUFFICIENT — **not** counted as mechanism success after reclassification

## Unresolved 22 (blockers retained)
- NDC_DRUG_PRODUCT: 11
- PLACEHOLDER_UM_RULES: 3
- LICENSED_MCG_CRITERIA: 2
- MUE_SOURCE_AND_SEMANTICS: 2
- TRANSPLANT_ORGAN_SCHEDULE: 2
- REIMBURSEMENT_RATES: 1
- LICENSED_CLINICAL_PATHWAY: 1

## Overnight platform-health
Tracked separately — HIGH ≠ definition or lifecycle completeness.
