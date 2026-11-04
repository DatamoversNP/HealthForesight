# Outpatient MRI Prior Authorization

**Policy ID:** `d403f101-08dd-45c9-ab83-d42e37c62018`  
**Type:** `PRIOR_AUTH`  
**Status:** `ACTIVE`  
**Jurisdiction:** `NC`  

## Description

Require prior authorization for outpatient MRI to reduce inappropriate imaging.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL"] |
| markets | ["NYC", "DFW"] |
| network | ["IN"] |
| service_categories | ["PRIMARY_CARE", "ADVANCED_IMAGING"] |
| procedure_codes | ["99213", "99214", "72148", "72149"] |

## Enforcement

```json
{
  "mechanism": "HARD",
  "touchpoint": [
    "PA_WORKFLOW"
  ],
  "override_allowed": false
}
```

**Version enforcement strength:** `STANDARD`

## Policy levers

```json
[
  {
    "lever_type": "PRIOR_AUTH",
    "parameters": {
      "codes": [
        "72148",
        "72149",
        "72158"
      ],
      "site_of_care": "OUTPATIENT"
    }
  }
]
```

## Codes

_No code set._

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| ELASTICITY | Expected impact for Outpatient MRI Prior Authorization | TBD | 0.5 | Initial estimate |
| ELASTICITY | Price elasticity of demand for Outpatient MRI Prior Authorization | -0.3 | 0.75 | Historical claims analysis |
| SUBSTITUTION_RATE | Expected substitution to alternative services | 0.15 | 0.7 | Provider behavior modeling |
| LAG_DAYS | Expected lag before policy impact is observed | 60 | 0.8 | Policy implementation timeline |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| utilization_rate | change_pct | 20.0 | alert | Monitor utilization changes for Outpatient MRI Prior Authorization |
| UTILIZATION_INCREASE | max | 0.2 | alert | Alert if utilization increases more than 20% above baseline |
| COST_INCREASE | max | 0.15 | alert | Alert if cost per member per month increases more than 15% |
| ER_UTILIZATION | max | 0.1 | alert | Alert if ER utilization increases more than 10% (potential substitution effect) |

## Standards basis

- U.S. payer UM common practice
- Blues-style medical/pharmacy program structure
- CMS/ACA/MHPAEA concepts where noted by LOB

## Medicare / source links

| Role | Family | Document ID | Title | Authority |
|---|---|---|---|---|
| REFERENCES_NCD | cms_ncd | NCD220.2 | Magnetic Resonance Imaging | CMS |
| REFERENCES_NCD | cms_ncd | NCD220.2 | Magnetic Resonance Imaging | CMS |
| REFERENCES_LCD | mac_lcd_nc | L34425 | Magnetic Resonance Imaging of the Orbit, Face, and/or Neck | Palmetto GBA |
| HAS_RELATED_ARTICLE | lcd_billing_coding_articles | A56729 | Billing and Coding: Magnetic Resonance Imaging of the Orbit, Face, and/or Neck | Palmetto GBA |
| USES_CODING_EDIT | ncci_ptp | NCCI-PTP-PAIR-70553-70551 | Demo PTP pair 70553/70551 (synthetic edit illustration) | CMS NCCI |

## Versions

- **v1** — MINOR — strength `STANDARD` — effective `2024-01-01T00:00:00` → `open`
- **v2** — MINOR — strength `STANDARD` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {},
  "enterprise_classification": {
    "stamped_at": "2026-11-03T09:07:04.414978Z",
    "stamped_by": "stamp_catalog_classification.py",
    "code_sets_status": "MISSING",
    "provenance_status": "MISSING_AUTHORITATIVE_SOURCE",
    "data_classification": "illustrative_catalog",
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
_Machine-readable twin: `Outpatient_MRI_Prior_Authorization.json`_
