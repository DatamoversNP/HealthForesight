# NCCI Procedure-to-Procedure Bundling

**Policy ID:** `58b839b5-b6e0-59e0-9406-d817877c3ce8`  
**Type:** `CODING_AND_BILLING`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `CODING_EDIT_MODIFIER`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Applies NCCI procedure-to-procedure bundling edits with modifier-indicator semantics (indicator 1 allows clinically appropriate modifiers such as 59/X{E,P,S,U}). Representative Payer coding-integrity policy for NC markets.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["ADVANCED_IMAGING"] |
| procedure_codes | ["70553", "70551"] |
| applies_to_all | false |

## Enforcement

```json
{
  "mechanism": "HARD",
  "touchpoint": [
    "CLAIMS_EDIT"
  ],
  "override_allowed": true,
  "override_requires": "clinically_appropriate_modifier"
}
```

**Version enforcement strength:** `STRONG`

## Policy levers

```json
[
  {
    "targets": {
      "codes": [
        "70553",
        "70551"
      ],
      "code_type": "CPT"
    },
    "lever_type": "CODING_EDIT",
    "parameters": {
      "edit_type": "NCCI_PTP",
      "column_one": "70553",
      "column_two": "70551",
      "modifier_indicator": "1",
      "appropriate_modifiers": [
        "59",
        "XE",
        "XP",
        "XS",
        "XU"
      ]
    }
  }
]
```

## Codes

| Type | Code | Group |
|---|---|---|
| CPT | 70553 | MRI_BRAIN |
| CPT | 70551 | MRI_BRAIN |

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| COST | Column-two denial under PTP reduces paid amount when no appropriate modifier is present | price_effect_only | 0.9 | NCCI PTP mechanical known-answer fixture |
| UTILIZATION | Volume held constant — PTP is a payment edit, not utilization management | 0 | 0.95 | Analytical strategy registry |
| BEHAVIOR | Some claims will bypass via clinically appropriate modifiers under indicator 1 | modifier_bypass_eligible | 0.7 | NCCI modifier-indicator guidance |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| ptp_pair_hit_rate | max | 0.35 | alert | Alert if PTP pair hit rate exceeds 35% of eligible imaging claims |
| modifier_bypass_rate | max | 0.5 | alert | Alert if modifier-59/X{E,P,S,U} bypass exceeds 50% of PTP hits |
| payment_impact_pct | max | 25.0 | alert | Alert if payer savings exceed 25% of baseline paid on PTP-eligible claims |

## Standards basis

- CMS National Correct Coding Initiative (NCCI) PTP edit framework
- Modifier indicator 0/1/9 semantics

## Medicare / source links

| Role | Family | Document ID | Title | Authority |
|---|---|---|---|---|
| USES_CODING_EDIT | ncci_ptp | NCCI-PTP-PAIR-70553-70551 | Demo PTP pair 70553/70551 (synthetic edit illustration) | CMS NCCI |

## Versions

- **v1** — INITIAL — strength `STRONG` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {
    "engine_id": "reimbursement_ncci_ptp_v1",
    "mechanism": "NCCI_PTP_FIXTURE"
  },
  "enterprise_classification": {
    "mechanism": "CODING_EDIT_MODIFIER",
    "catalog_class": "DEMO_SYNTHETIC",
    "sub_mechanism": "NCCI_PTP",
    "dec4_expansion": true,
    "validation_target": "FULLY_VALIDATED_DEMO",
    "representative_payer": true,
    "not_blue_cross_nc_proprietary": true
  }
}
```

---
_Machine-readable twin: `NCCI_Procedure-to-Procedure_Bundling.json`_
