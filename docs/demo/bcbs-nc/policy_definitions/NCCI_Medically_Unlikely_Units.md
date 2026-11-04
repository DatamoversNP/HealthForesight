# NCCI Medically Unlikely Units

**Policy ID:** `e11b049d-fcce-55cc-bcd7-71329038383b`  
**Type:** `CODING_AND_BILLING`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `FEE_SCHEDULE_UNIT_PRICE`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Applies NCCI Medically Unlikely Edits (MUE) unit caps at the claim-line level. Synthetic published-style MUE value used for known-answer validation until authorized quarterly MUE files are reconciled.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["THERAPY", "OUTPATIENT"] |
| procedure_codes | ["97110"] |
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
        "97110"
      ],
      "code_type": "CPT"
    },
    "lever_type": "UNIT_LIMIT",
    "parameters": {
      "edit_type": "NCCI_MUE",
      "mue_value": 4,
      "synthetic_mue": true,
      "mue_adjudication_indicator": "2"
    }
  }
]
```

## Codes

| Type | Code | Group |
|---|---|---|
| CPT | 97110 | THERAPY |

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| COST | Units above MUE are unpaid (hard MAI-style limit in fixture) | unpaid_excess_units | 0.85 | NCCI MUE mechanical known-answer fixture |
| DATA | MUE value 4 for 97110 is SYNTHETIC — not asserted as live CMS confidential value | 4 | 1.0 | Disclosed synthetic fixture |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| mue_cap_rate | max | 0.2 | alert | Alert if more than 20% of 97110 lines are MUE-capped |
| avg_units_per_line | max | 8.0 | alert | Alert if average billed units per 97110 line exceed 8 |

## Standards basis

- CMS NCCI Medically Unlikely Edits framework
- MUE adjudication indicator semantics

## Medicare / source links

| Role | Family | Document ID | Title | Authority |
|---|---|---|---|---|
| USES_CODING_EDIT | ncci_mue | NCCI-MUE-97110-DEMO | Demo MUE for 97110 (synthetic published-style value) | CMS NCCI |

## Versions

- **v1** — INITIAL — strength `STRONG` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {
    "engine_id": null,
    "mechanism": "FEE_SCHEDULE_UNIT_PRICE"
  },
  "enterprise_classification": {
    "mechanism": "FEE_SCHEDULE_UNIT_PRICE",
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
_Machine-readable twin: `NCCI_Medically_Unlikely_Units.json`_
