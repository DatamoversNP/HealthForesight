# Medicare Inventory Reconciliation

**Batch:** `reconcile-20261103T115616Z`  
**Tenant:** `00000000-0000-0000-0000-000000000001`

## Family totals

| Family | Catalog class | Acquisition state | Discovered | Ingested |
|---|---|---|---:|---:|
| cms_ncd | AUTHORITATIVE_PUBLIC | RECONCILED | 2 | 2 |
| mac_lcd_nc | AUTHORITATIVE_PUBLIC | RECONCILED | 2 | 2 |
| lcd_billing_coding_articles | AUTHORITATIVE_PUBLIC | RECONCILED | 2 | 2 |
| ncci_ptp | AUTHORITATIVE_PUBLIC / DEMO subset | RECONCILED | 2 | 2 |
| ncci_mue | AUTHORITATIVE_PUBLIC / DEMO subset | RECONCILED | 2 | 2 |
| medicare_other_payment | AUTHORITATIVE_PUBLIC | RECONCILED | 1 | 1 |
| bcnc_* + payer_adaptations | DEMO_SYNTHETIC | DEMO_SYNTHETIC_CATALOG | 328* | 328* |

\*Family discover sums overlap; unique configured policies remain **283** (+ **6** expansion demo policies seeded separately).

## Completeness declaration

| Question | Answer |
|---|---|
| Complete CMS NCD inventory? | **No** — 2 documents |
| Complete JM LCD inventory? | **No** — 1 NC-applicable + 1 negative control |
| Complete NCCI quarterly? | **No** — bounded demo subset |
| Historical MCD versions complete? | **No** |
| Safe for Dec 4 demo provenance? | **Yes** for verified MRI chain NCD220.2 / L34425 / A56729 |

## NC applicability rule

- **NCD:** national  
- **LCD for NC demo:** Palmetto GBA Jurisdiction M (NC, SC, VA, WV)  
- Other-jurisdiction LCDs may exist in the library but must resolve `NOT_APPLICABLE_OTHER_JURISDICTION` for NC FFS
