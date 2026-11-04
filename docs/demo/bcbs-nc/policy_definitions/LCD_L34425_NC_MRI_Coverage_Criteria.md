# LCD L34425 NC MRI Coverage Criteria

**Policy ID:** `649b4ac8-ca82-5b84-aa87-84834490731a`  
**Type:** `COVERAGE`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `COVERAGE_DETERMINATION`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Local coverage criteria for MRI soft tissue of head and neck under Palmetto JM LCD L34425 with related billing/coding article A56729 (codes 70540/70542/70543).

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["ADVANCED_IMAGING"] |
| procedure_codes | ["70540", "70542", "70543"] |
| applies_to_all | false |

## Enforcement

```json
{
  "mechanism": "HARD",
  "touchpoint": [
    "COVERAGE_REVIEW",
    "CLAIMS_ADJUDICATION"
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
        "70540",
        "70542",
        "70543"
      ],
      "code_type": "CPT"
    },
    "lever_type": "COVERAGE_CRITERIA",
    "parameters": {
      "lcd_id": "L34425",
      "article_id": "A56729"
    }
  }
]
```

## Codes

| Type | Code | Group |
|---|---|---|
| CPT | 70540 | MRI_HEAD_NECK |
| CPT | 70542 | MRI_HEAD_NECK |
| CPT | 70543 | MRI_HEAD_NECK |

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| COVERAGE | A56729 lists only 70540/70542/70543 — PARTIAL clinical match for broader MRI UM | PARTIAL_CODE_OVERLAP | 0.95 | Coverage API article HCPCS enrichment |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| lcd_denial_rate | max | 0.15 | alert | Alert if LCD L34425 denial rate exceeds 15% |

## Standards basis

- Palmetto GBA Jurisdiction M LCD L34425
- Billing and Coding Article A56729

## Medicare / source links

| Role | Family | Document ID | Title | Authority |
|---|---|---|---|---|
| REFERENCES_LCD | mac_lcd_nc | L34425 | Magnetic Resonance Imaging of the Orbit, Face, and/or Neck | Palmetto GBA |
| HAS_RELATED_ARTICLE | lcd_billing_coding_articles | A56729 | Billing and Coding: Magnetic Resonance Imaging of the Orbit, Face, and/or Neck | Palmetto GBA |
| REFERENCES_LCD | mac_lcd_nc | L34425 | Magnetic Resonance Imaging of the Head and Neck | Palmetto GBA |
| HAS_RELATED_ARTICLE | lcd_billing_coding_articles | A56729 | Billing and Coding: Magnetic Resonance Imaging of the Head and Neck | Palmetto GBA |

## Versions

- **v1** — INITIAL — strength `STRONG` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {
    "engine_id": null,
    "mechanism": "COVERAGE_DETERMINATION"
  },
  "enterprise_classification": {
    "mechanism": "COVERAGE_DETERMINATION",
    "catalog_class": "DEMO_SYNTHETIC",
    "sub_mechanism": null,
    "dec4_expansion": true,
    "validation_target": "PROVENANCE_VALIDATED",
    "representative_payer": true,
    "not_blue_cross_nc_proprietary": true
  }
}
```

---
_Machine-readable twin: `LCD_L34425_NC_MRI_Coverage_Criteria.json`_
