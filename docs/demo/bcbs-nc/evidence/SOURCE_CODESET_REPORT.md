# Source codeset acquisition (reference library)

**Generated:** 2026-11-03  
**Creates payer catalog rows:** No

## Counts (reconciled into `policy_source_*`)

| Family | Count | State | Provenance |
|--------|------:|-------|------------|
| cms_ncd | 345 | RECONCILED | Coverage API `/reports/national-coverage-ncd/` |
| mac_lcd_nc | 938 | RECONCILED | Coverage API `/reports/local-coverage-final-lcds/?stateabbrev=NC` (195 Palmetto JM) |
| lcd_billing_coding_articles | 2118 | RECONCILED | Coverage API `/reports/local-coverage-articles/?stateabbrev=NC` |
| ncci_ptp | 0 | ACCESS_BLOCKED | cms.gov quarterly ZIP HTTP 403 on this host |
| ncci_mue | 0 | ACCESS_BLOCKED | cms.gov quarterly ZIP HTTP 403; no fabricated MUEs |
| medicare_other_payment | 1 | RECONCILED | local drop (bounded) |

`authoritative_public_ready` remains **false** until NCCI quarterly files are dropped from a host with CMS access.

## Code relationships

- Selective licensed HCPCS enrichment via Coverage API license-agreement token.
- `A56729` → **70540 / 70542 / 70543** only (confirms PARTIAL MRI soft-tissue neck article scope).
- Sidecars under `data/policy_sources/lcd_billing_coding_articles/codes/`.

## Operator replay

```bash
cd apps/api && python3 scripts/acquire_cms_coverage_catalogs.py
# then POST /api/v1/enterprise/policy-sources/reconcile (or in-process reconcile_all_families)
```

Artifacts: `SOURCE_CODESET_ACQUISITION.json`, `SOURCE_ACQUISITION_RECONCILE.json`, `SOURCE_CODESET_PROVENANCE.json`.
