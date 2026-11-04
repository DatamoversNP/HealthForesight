# Source Acquisition Status by Family

**As of:** 2026-11-03T09:33:41Z (reconcile batch `reconcile-20261103T093205Z`)  
**Tenant:** `00000000-0000-0000-0000-000000000001`  
**Demo target:** 2026-12-04 — **population readiness: NOT claimed**

## Classification (corrected)

| Catalog class | Default product label | Meaning |
|---------------|----------------------|---------|
| `DEMO_SYNTHETIC` | **Representative Payer Policies** | Blue Cross NC-**like** illustrative configs. Not proprietary BCBS NC. No BCBS NC authorization required. |
| `AUTHORITATIVE_PUBLIC` | Public CMS / NCCI | Actual public Medicare NCD/LCD/articles/NCCI when acquired with provenance. |

Contextual label when audience needs it: **Representative Payer Policies (Blue Cross NC-like)**.

## Acquisition states (replacing catch-all INACCESSIBLE)

`NOT_ATTEMPTED` → `ACCESS_BLOCKED` → `SOURCE_UNAVAILABLE` → `ACQUIRED` → `PARSED` → `RECONCILED` → `CONFIGURED` → `ANALYTICALLY_READY`

Demo-only: `DEMO_SYNTHETIC_CATALOG` / `DEMO_SYNTHETIC_ANALYTICS`.

A demo-host network restriction alone must **not** permanently mark a public CMS source `SOURCE_UNAVAILABLE`.

## Honesty flags (API)

| Flag | Value |
|------|-------|
| `representative_payer_is_blue_cross_nc_like_not_verbatim` | true |
| `cms_ncci_remain_authoritative_public_when_acquired` | true |
| `requires_bcbs_nc_authorization` | **false** |
| `demo_payer_catalog_ready` | **true** (synthetic catalog loaded) |
| `authoritative_public_ready` | **false** |
| `dec4_population_ready` | **false** |

---

## Family-by-family acquisition

### DEMO_SYNTHETIC — Representative Payer (Blue Cross NC-like)

| Family | Endpoint / method | State | Discovered | Notes |
|--------|-------------------|-------|------------|-------|
| `bcnc_commercial_reimbursement` | Demo catalog JSON + optional `data/policy_sources/…` drop | `DEMO_SYNTHETIC_CATALOG` | 13 | Commercial reimbursement-like rules |
| `bcnc_medicare_reimbursement` | Demo catalog | `DEMO_SYNTHETIC_CATALOG` | 73 | MA / Medicare-like payment exhibits |
| `bcnc_medical` | Demo catalog | `DEMO_SYNTHETIC_CATALOG` | 172 | Medical / UM (includes MRI demo path) |
| `bcnc_administrative` | Demo catalog | `DEMO_SYNTHETIC_CATALOG` | 53 | Admin / network / benefit-like |
| `bcnc_pricing` | Demo catalog | `DEMO_SYNTHETIC_CATALOG` | 6 | Pricing exhibits — not plan fee schedules |
| `payer_adaptations` | Demo catalog | `DEMO_SYNTHETIC_CATALOG` | 11 | Illustrative adaptations of industry/Medicare patterns |

**Retrieval method:** Load `scripts/demo/catalog/bcbs_nc_aligned_policy_catalog.json` rows flagged `not_verbatim_bcbsnc_policy` / `illustrative_standards_aligned`. Optional JSONL override under `data/policy_sources/<family>/`.

**DNS/TLS/HTTP/auth:** N/A for catalog seed (local file). No tokens logged.

**Do not:** Present these as actual Blue Cross NC policies or overwrite them when CMS titles match.

### AUTHORITATIVE_PUBLIC — CMS / NCCI

| Family | Authoritative endpoint | Retrieval methods | State | Disc. | Blocker |
|--------|------------------------|-------------------|-------|-------|---------|
| `cms_ncd` | [CMS Medicare Coverage Database](https://www.cms.gov/medicare-coverage-database); API `https://api.coverage.cms.gov` | (1) `CMS_COVERAGE_API_TOKEN` / `CMS_MCD_API_TOKEN` (2) JSONL file-drop `data/policy_sources/cms_ncd/` | `NOT_ATTEMPTED` | 0 | No token + empty drop |
| `mac_lcd_nc` | CMS MCD — Palmetto JM / NC | Token API (jurisdiction filter TBD) or drop `mac_lcd_nc/` | `NOT_ATTEMPTED` | 0 | Same |
| `lcd_billing_coding_articles` | CMS MCD articles | File-drop `lcd_billing_coding_articles/` | `NOT_ATTEMPTED` | 0 | Empty drop |
| `ncci_ptp` | [CMS NCCI edits](https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits) | Quarterly PTP file drop `ncci_ptp/` | `NOT_ATTEMPTED` | 0 | No quarterly export |
| `ncci_mue` | CMS NCCI MUE releases | Authorized/complete MUE drop `ncci_mue/` | `NOT_ATTEMPTED` | 0 | No release; confidential values must not be fabricated |
| `medicare_other_payment` | CMS fee schedule / MPPR / global / modifiers / POS pubs | File-drop `medicare_other_payment/` | `NOT_ATTEMPTED` | 0 | Empty drop |

**Diagnostic rules applied**

1. Endpoint + method recorded per family (above).
2. Live CMS/NCCI HTTP not forced from this host without credentials — state stays `NOT_ATTEMPTED`, not permanent inaccessible.
3. Distinguishes: missing credentials (`NOT_ATTEMPTED`) vs failed request after attempt (`ACCESS_BLOCKED`) vs empty/unparseable (`SOURCE_UNAVAILABLE`).
4. Supports authorized API, downloadable-file, and file-drop.
5. User action for CMS: obtain MCD export or set `CMS_COVERAGE_API_TOKEN`; place JSONL under `data/policy_sources/<family>/`; POST `/api/v1/enterprise/policy-sources/reconcile`. For NCCI: drop quarterly PTP/MUE files with release version + effective dates.
6. Tokens and source contents are not logged by adapters.
7. Demo-host network limits do not finalize `SOURCE_UNAVAILABLE` for public CMS sources.

---

## Pipeline counts (actual)

Separating **demonstration / synthetic** from **authoritative public**.

### Demonstration — Representative Payer Policies

| Stage | Count | Evidence class |
|-------|------:|----------------|
| Discovered (catalog families sum) | 328* | DEMO_SYNTHETIC definitions from illustrative catalog |
| Acquired / catalog-ingested (inventory) | 328* | Same — not CMS provenance |
| Reconciled (demo families) | 6/6 families | `DEMO_SYNTHETIC_CATALOG` |
| Configured (DB policies with rules/workspace) | 283 | Existing tenant catalog (illustrative flagged: **244**) |
| Baseline-ready (persisted jobs) | 257 | Synthetic/demo analytics — **not** empirical BCBS NC |
| Forecast-ready | 265 | Same |
| Observed | 265 | Same |
| Verdict-ready (lifecycle artifacts) | 265 | Same; full B+P+O = **257** |
| Impact assessable (validated causal) | 0 | No production-qualified causal on real payer claims |

\*Family discover sums (13+73+172+53+6+11) can overlap the same underlying illustrative titles across heuristic buckets; **unique configured policies in DB = 283**.

### Authoritative public — CMS NCD / LCD / NCCI

| Stage | Count |
|-------|------:|
| Discovered | **0** |
| Acquired | **0** |
| Reconciled | **0** |
| Configured (source-grounded) | **0** |
| Baseline / forecast / observed / verdict (authoritative provenance) | **0** |

Named examples in current catalog (1 NCD, 1 LCD, 1 NCCI/MUE pattern) are **illustrative**, not reconciled inventory.

### Claims substrate

| Metric | Value |
|--------|------:|
| `claims_lines` | 3,505,919 |
| Classification | `DATA_GENERATOR` / demo loaders — **synthetic** |
| Not claiming | Actual Blue Cross NC claims experience |

---

## What Dec 4 can still show (without claiming full population)

1. Complete **MRI** Representative Payer lifecycle (existing demo).
2. Validated reimbursement lifecycle on a **published public** Medicare definition **once acquired**, with **labeled synthetic** claims.
3. North Carolina Medicare **applicability** example using public jurisdiction rules **once LCD/NCD exports are present**.

Comprehensive authoritative inventory + empirical outcomes remain a larger milestone after source acquisition.

## Artifacts

- `SOURCE_ACQUISITION_RECONCILE.json` — raw reconcile response  
- `CLAIMS_FEASIBILITY_REPORT.json` / `.md` — field-level claims feasibility  
- `POLICY_INVENTORY_283_AUDIT.json` — prior 283-row audit  
- `data/policy_sources/README.md` — drop layout + states  
