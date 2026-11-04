# NCD 220.2 MRI Coverage Change Study

**Policy ID:** `4f8c34e3-015b-509d-90ba-521261464258`  
**Type:** `COVERAGE`  
**Status:** `ACTIVE`  
**Analytical mechanism:** `COVERAGE_DETERMINATION`  
**Catalog class:** `DEMO_SYNTHETIC`  
**Jurisdiction:** `NATIONAL`  

## Description

Coverage change study keyed to CMS NCD 220.2 (Magnetic Resonance Imaging). Used for Medicare applicability / provenance analytics.

## Scope

| Field | Value |
|---|---|
| lob | ["COMMERCIAL", "MA", "MEDICAID"] |
| states | ["NC"] |
| markets | ["NC"] |
| network | ["IN"] |
| service_categories | ["ADVANCED_IMAGING"] |
| procedure_codes | ["70551", "70552", "70553", "72148", "72149", "72158"] |
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
        "70551",
        "70552",
        "70553",
        "72148",
        "72149",
        "72158"
      ],
      "code_type": "CPT"
    },
    "lever_type": "COVERAGE_CRITERIA",
    "parameters": {
      "ncd_id": "NCD220.2"
    }
  }
]
```

## Codes

| Type | Code | Group |
|---|---|---|
| CPT | 70551 | MRI |
| CPT | 70552 | MRI |
| CPT | 70553 | MRI |
| CPT | 72148 | MRI |
| CPT | 72149 | MRI |
| CPT | 72158 | MRI |

## Assumptions

| Type | Description | Value | Confidence | Source |
|---|---|---|---:|---|
| COVERAGE | NCD 220.2 is the national Medicare coverage authority for MRI | NCD220.2 | 0.95 | CMS Coverage API national-coverage-ncd report |

## Guardrails

| Metric | Threshold | Value | Action | Description |
|---|---|---:|---|---|
| noncovered_mri_claim_rate | max | 0.05 | alert | Alert if non-covered MRI claim rate exceeds 5% |

## Standards basis

- CMS NCD 220.2 Magnetic Resonance Imaging

## Medicare / source links

| Role | Family | Document ID | Title | Authority |
|---|---|---|---|---|
| REFERENCES_NCD | cms_ncd | NCD220.2 | Magnetic Resonance Imaging | CMS |
| REFERENCES_NCD | cms_ncd | NCD220.2 | Magnetic Resonance Imaging | CMS |

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
_Machine-readable twin: `NCD_220_2_MRI_Coverage_Change_Study.json`_
