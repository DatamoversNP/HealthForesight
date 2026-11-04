# MRI Source Evidence Register (v1.2.1 technical closure)

| evidence_id | assertion | class | locator | retrieved / notes |
|---|---|---|---|---|
| EV-NCD-220.2 | National MRI coverage determination exists (CMS) | VERIFIED_SOURCE | Coverage API NCD report `NCD220.2` / ncdid 177; MCD | content_hash `7f8301d92aa8ac15e8e18012d5c748dbc950c06b34ace7d19a587438f965e277`; last_updated 12/03/2024; ver 6 |
| EV-LCD-L34425 | Palmetto JM LCD for MRI orbit/face/neck | VERIFIED_SOURCE | Coverage API NC LCD catalog | content_hash `b5ab4139d9dcc9a7a9aa684be2a2fcb9f12d07c0a125a7ebf0a15d1a29d7e19c`; ver 43; effective_start 2025-03-27 |
| EV-ART-A56729-HCPCS | Article lists CPT 70540/70542/70543 | VERIFIED_SOURCE | Coverage API article HCPCS + sidecar `codes/A56729.json` | retrieved_at `2026-11-03T13:02:24.568026+00:00`; source_version `24`; sha256 `80d90feed877911cbebeebe15e0d83f3c814dfc6a52a7b698008e63aacacf731`; applicability_period_start `2026-10-01`; OUT_OF_BAND for proposed lumbar PA |
| EV-CLIN-APP | Lumbar/brain PA portfolio ≠ orbit LCD | VERIFIED_SOURCE | `docs/demo/bcbs-nc/MRI_MEDICARE_CLINICAL_APPLICABILITY.md` | Jurisdiction ≠ clinical match |
| EV-CFG-LIVE-EM | Live MRI config includes E/M in scope | CONFIG_DEFECT | `policy_definitions/Outpatient_MRI_Prior_Authorization.json` | Quarantine; EXCLUDE_PA_TARGET in codeset |
| EV-SYN-PTP | Demo PTP pair 70553/70551 | SYNTHETIC_FIXTURE | expansion NCCI stub | Not published CMS authority |
| EV-ACR-LBP | Appropriateness guidance for LBP imaging | UNRESOLVED attach | ACR Appropriateness Criteria® (licensed) | **Do not paste copyrighted criteria**; attach approved excerpt under license/approval |
| EV-NCCI-QTR | Full quarterly NCCI files | ACCESS_BLOCKED on demo host | cms.gov ZIP | Not required for lumbar PA clinical criteria |
| EV-PRODUCT | NC commercial product IDs | UNRESOLVED | Payer product schedule | Required before activation |
| EV-LEGAL-CLOCKS | UM notice/appeal timelines | UNRESOLVED | NC + federal mapping by counsel | Required before activation |
| EV-SCOPE-MIG | General OP MRI → proposed lumbar-only | PROPOSED | `MRI_SCOPE_MIGRATION_DECISION_v1.2.md` | Unsigned; frozen demo must not silently inherit |

## VERIFIED_SOURCE minimum evidence object (codeset schema)

Required non-null for any code row labeled `VERIFIED_SOURCE`:

1. `evidence_id`  
2. `source_system` + `source_document_id` + `source_version`  
3. `retrieved_at`  
4. `content_checksum_sha256`  
5. `applicability_period_start` (end may be null if open)  
6. Program/applicability keys in `medicare_applicability`

A narrative reference to “prior CMS API enrichment” alone is **insufficient**.

## Verification protocol before promoting any row to VERIFIED operative

1. Document version + URL + retrieval date + checksum  
2. Applicable code scope list  
3. Program (commercial vs Medicare FFS)  
4. Clinical owner + compliance sign-off  
5. Explicit decision that the code is in-band for this PA (orbit codes remain OUT_OF_BAND for proposed lumbar PA)  
