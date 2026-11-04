# Infusion Site-of-Care Optimization

**Policy ID:** `11218053-bdc0-569f-a415-fb61c5dcda37`  
**Type:** `SITE_OF_CARE`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NC`  

## Description

Steers eligible specialty infusion episodes from hospital outpatient (HOPD) to lower-cost ASC/office sites when clinically appropriate.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["INFUSION", "SPECIALTY_DRUG"] |
| procedure_codes | [] |
| allowed_sites | ["ASC_OR_OFFICE", "HOPD"] |
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
      "code_groups": [
        "INFUSION_SPECIALTY"
      ]
    },
    "lever_type": "SITE_OF_CARE",
    "parameters": {
      "preferred_sites": [
        "ASC_OR_OFFICE"
      ],
      "hospital_allowed_when": "clinical_exception",
      "office_allowed_amount": 3200.0
    }
  }
]
```

## Codes

_No code set._

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| COST | HOPD to office steerage saves hospital−office differential per episode | 1800_per_steered_episode_fixture | 0.8 | Infusion SOC known-answer fixture |
| QUALITY | Quality outcomes maintained at preferred sites for eligible members |  | 0.7 | Site-of-care quality assumption |
| BEHAVIOR | Not all HOPD episodes are steerable; fixture steers 2 of 3 HOPD lines | 2/3 | 0.75 | reimbursement-infusion-soc-v1 |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| site_of_care_redirect_rate | min | 0.5 | alert | Monitor successful infusion site-of-care redirections |
| hopd_infusion_share | max | 0.4 | alert | Alert if HOPD share of infusion episodes remains above 40% |

## Standards basis

- Payer site-of-care optimization common practice
- Hospital outpatient vs freestanding/office differential payment

## Medicare / source links

_No Medicare source links._

## Versions

- **v1** — INITIAL — strength `MODERATE` — effective `2024-01-01T00:00:00` → `open`

## Analytical strategy

```json
{
  "analytical_strategy": {
    "engine_id": null,
    "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"
  },
  "enterprise_classification": {
    "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
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
_Machine-readable twin: `Infusion_Site-of-Care_Optimization.json`_
