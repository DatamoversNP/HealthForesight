# Freestanding Imaging Steerage

**Policy ID:** `d7441dd9-3bfe-405e-ae6c-0377204bbb7e`  
**Type:** `SITE_OF_CARE`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Steers advanced imaging to freestanding centers vs hospital outpatient when equivalent. Illustrative industry-standard program definition aligned with typical Blues / North Carolina payer UM structures. Not a verbatim Blue Cross NC medical policy, clinical guideline, or formulary row.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["PRIMARY_CARE", "ADVANCED_IMAGING"] |
| procedure_codes | ["99213", "99214", "72148", "72149"] |
| applies_to_all | false |

## Enforcement

```json
{
  "mechanism": "SOFT",
  "touchpoint": [
    "PRIOR_AUTH",
    "SITE_OF_CARE_REVIEW"
  ],
  "override_allowed": true
}
```

**Version enforcement strength:** `MODERATE`

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
    "lever_type": "SITE_OF_CARE",
    "parameters": {
      "redirect_to": "FREESTANDING",
      "allowed_sites": [
        "FREESTANDING",
        "OFFICE"
      ],
      "disallowed_sites": [
        "HOSPITAL_OP"
      ],
      "deny_if_disallowed": false
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
| COST | Hospital outpatient imaging paid at reduced % of allowed vs freestanding | hospital_pct_0.80_base | 0.85 | reimbursement-sos-v1 known-answer |
| UTILIZATION | Volume held constant — site differential is price/mix, not UM elasticity | 0 | 0.95 | Analytical strategy registry |
| QUALITY | Quality outcomes maintained at freestanding sites for eligible imaging |  | 0.7 | Site-of-care quality assumption |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| hospital_imaging_share | max | 0.5 | alert | Alert if hospital outpatient share of eligible imaging remains above 50% |
| sos_payment_impact_pct | min | 5.0 | alert | Alert if SOS payer savings fall below 5% of baseline paid |

## Standards basis

- U.S. payer UM common practice
- Blues-style medical/pharmacy program structure
- CMS/ACA/MHPAEA concepts where noted by LOB

## Medicare / source links

_No Medicare source links._

## Versions

- **v1** — INITIAL — strength `MODERATE` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {
    "engine_id": "reimbursement_sos_v1",
    "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
    "registry_version": "analytical-strategy-registry-v1",
    "calculation_version": "reimbursement-sos-v1"
  },
  "enterprise_classification": {
    "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
    "stamped_at": "2026-11-03T09:07:04.414608Z",
    "stamped_by": "stamp_catalog_classification.py",
    "catalog_class": "DEMO_SYNTHETIC",
    "display_label": "Representative Payer Policies",
    "code_sets_status": "MISSING",
    "provenance_status": "MISSING_AUTHORITATIVE_SOURCE",
    "calculation_version": "reimbursement-sos-v1",
    "data_classification": "illustrative_catalog",
    "lifecycle_validation": "FULLY_VALIDATED_DEMO",
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
_Machine-readable twin: `Freestanding_Imaging_Steerage.json`_
