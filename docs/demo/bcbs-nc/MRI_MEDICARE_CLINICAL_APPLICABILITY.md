# MRI PA — Medicare Clinical Applicability Verification

**Date:** 2026-11-03  
**Policy:** Outpatient MRI Prior Authorization (frozen demo)  
**Principle:** Jurisdiction match ≠ clinical applicability.

## Findings

| Authority | NC / JM jurisdiction | Clinical match to MRI PA | Present as MRI PA authority? |
|---|---|---|---|
| **NCD 220.2** | National (yes) | **APPLICABLE** — national MRI coverage determination | **Yes** |
| **L34425** | Yes (Palmetto JM includes NC) | **PARTIAL_SERVICE_SCOPE** — orbit / face / neck only | **No** (related partial only) |
| **A56729** | Yes (article of L34425) | **PARTIAL** — CPT **70540, 70542, 70543** | **No** |
| NCCI PTP demo pair | National coding edit | Coding rule, not coverage | No |

## Code / service gap

Representative Outpatient MRI PA portfolio includes brain MRI (**70551–70553**), spine, and extremity codes.  
L34425/A56729 address **orbit/face/neck** only. Overlap with the PA portfolio CPT set is **empty** for brain/spine codes.

## Effective dates (verified for as_of 2024-06-01)

- NCD 220.2 effective of this version: 2018-04-10 → OK  
- L34425 original effective: 2015-10-01 → OK for jurisdiction/partial clinical use  

## Demo disclosure (required)

> For Original Medicare FFS in North Carolina, **NCD 220.2** is the primary national MRI coverage authority shown. **L34425 / A56729** are correctly Palmetto JM documents but apply only to MRI of the orbit, face, and/or neck — not the full outpatient MRI PA service set. No verified JM LCD currently covers the entire PA CPT portfolio; local medical necessity for other body regions may rely on the NCD plus documentation without a matching body-region LCD.

## API

`GET /api/v1/enterprise/medicare-rules/mri-clinical-applicability`
