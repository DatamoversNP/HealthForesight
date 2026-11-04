# Multiple Procedure Payment Reduction

**Policy ID:** `d0eeb370-df14-4478-8755-dad6c3a35a47`  
**Type:** `PAYMENT_POLICY`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `MULTIPLE_PROCEDURE_PAYMENT_REDUCTION`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Applies MPPR to secondary procedures in same session. Illustrative industry-standard program definition aligned with typical Blues / North Carolina payer UM structures. Not a verbatim Blue Cross NC medical policy, clinical guideline, or formulary row.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["PRIMARY_CARE", "ADVANCED_IMAGING"] |
| procedure_codes | ["99213", "99214", "72148", "72149"] |
| applies_to_all | false |

## Enforcement

```json
{
  "mechanism": "HARD",
  "touchpoint": [
    "CLAIMS_EDIT"
  ],
  "override_allowed": false
}
```

**Version enforcement strength:** `STRONG`

## Policy levers

```json
[
  {
    "targets": {
      "codes": [
        "72148",
        "72149"
      ],
      "code_type": "CPT",
      "code_groups": []
    },
    "lever_type": "PRIOR_AUTH",
    "parameters": {
      "requires_pa": true
    }
  }
]
```

## Codes

| Type | Code | Group |
|---|---|---|
| CPT | 72148 | MRI |
| CPT | 72149 | MRI |
| CPT | 70553 | MRI |

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| COST | Secondary procedure lines paid at reduced % of allowed under MPPR | secondary_pct_0.50_base | 0.9 | reimbursement-mppr-v1 known-answer |
| UTILIZATION | Volume held constant — MPPR is a payment-rule effect, not utilization elasticity | 0 | 0.95 | Analytical strategy registry |
| BEHAVIOR | Providers may resequence / unbundle claims; fixture does not model behavioral gaming | not_modeled | 0.7 | Disclosed limitation |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| mppr_payment_impact_pct | max | 30.0 | alert | Alert if MPPR payer savings exceed 30% of baseline paid on multi-procedure claims |
| secondary_lines_reduced_share | min | 0.4 | alert | Alert if share of secondary lines reduced falls below 40% of multi-proc claims |

## Standards basis

- U.S. payer UM common practice
- Blues-style medical/pharmacy program structure
- CMS/ACA/MHPAEA concepts where noted by LOB

## Medicare / source links

_No Medicare source links._

## Versions

- **v1** — INITIAL — strength `STRONG` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {
    "engine_id": "reimbursement_mppr_v1",
    "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
    "registry_version": "analytical-strategy-registry-v1",
    "calculation_version": "reimbursement-mppr-v1"
  },
  "enterprise_classification": {
    "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
    "stamped_at": "2026-11-03T09:07:04.414582Z",
    "stamped_by": "stamp_catalog_classification.py",
    "catalog_class": "DEMO_SYNTHETIC",
    "display_label": "Representative Payer Policies",
    "code_sets_status": "MISSING",
    "provenance_status": "MISSING_AUTHORITATIVE_SOURCE",
    "calculation_version": "reimbursement-mppr-v1",
    "data_classification": "illustrative_catalog",
    "lifecycle_validation": "FULLY_VALIDATED_DEMO",
    "display_label_contextual": "Representative Payer Policies (Blue Cross NC-like)",
    "catalog_accuracy_contract": {
      "why": "Proprietary BCBS NC policy text is not publicly reproducible at 100% fidelity; mislabeling would reduce credibility",
      "claim": "Industry-standard / Blues-aligned illustrative program catalog for NC-oriented demos",
      "not_claiming": "Verbatim Blue Cross NC medical policies, CUMG text, or formulary NDC lists"
    },
    "not_verbatim_bcbsnc_policy": true,
    "illustrative_standards_aligned": true,
    "authoritative_source_reconciled": false
  }
}
```

---
_Machine-readable twin: `Multiple_Procedure_Payment_Reduction.json`_
