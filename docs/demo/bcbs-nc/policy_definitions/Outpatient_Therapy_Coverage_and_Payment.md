# Outpatient Therapy Coverage and Payment

**Policy ID:** `f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b`  
**Type:** `COVERAGE`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `COVERAGE_DETERMINATION`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Outpatient physical therapy coverage and payment rules aligned to Palmetto JM LCD L34428 (Outpatient Physical Therapy). Pays only medically necessary units under the configured coverage frequency rule.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["THERAPY", "OUTPATIENT"] |
| procedure_codes | ["97110", "97140"] |
| applies_to_all | false |

## Enforcement

```json
{
  "mechanism": "HARD",
  "touchpoint": [
    "CLAIMS_ADJUDICATION",
    "COVERAGE_REVIEW"
  ],
  "override_allowed": true
}
```

**Version enforcement strength:** `STRONG`

## Policy levers

```json
[
  {
    "targets": {
      "codes": [
        "97110",
        "97140"
      ],
      "code_type": "CPT"
    },
    "lever_type": "COVERAGE_CRITERIA",
    "parameters": {
      "lcd_id": "L34428",
      "pay_medically_necessary_units_only": true
    }
  }
]
```

## Codes

| Type | Code | Group |
|---|---|---|
| CPT | 97110 | THERAPY |
| CPT | 97140 | THERAPY |

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| UTILIZATION | Units billed above medically necessary threshold are non-payable | medically_necessary_units_cap | 0.8 | Coverage frequency known-answer fixture |
| COST | Payment impact is price/unit effect with volume of necessary units held | price_effect_only | 0.85 | coverage-therapy-v1 |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| therapy_units_denied_pct | max | 40.0 | alert | Alert if >40% of therapy units are denied as not medically necessary |
| member_access_complaints | max | 25.0 | alert | Alert if therapy access complaints exceed threshold |

## Standards basis

- Palmetto GBA Jurisdiction M LCD L34428
- Medicare outpatient therapy coverage principles

## Medicare / source links

| Role | Family | Document ID | Title | Authority |
|---|---|---|---|---|
| REFERENCES_LCD | mac_lcd_nc | L34428 | Outpatient Physical Therapy | Palmetto GBA |
| REFERENCES_LCD | mac_lcd_nc | L34428 | Outpatient Physical Therapy | Palmetto GBA |

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
    "validation_target": "FULLY_VALIDATED_DEMO",
    "representative_payer": true,
    "not_blue_cross_nc_proprietary": true
  }
}
```

---
_Machine-readable twin: `Outpatient_Therapy_Coverage_and_Payment.json`_
