# Medicare Source Acquisition Report

**As of:** 2026-11-03  
**Stack:** demo7867 → Azure Postgres  
**Decision:** Bounded authoritative ingest via file-drop + adapter reconcile. Full CMS bulk/API universe **not** claimed complete.

## Authoritative source map

| Family | Official source | Method used today | State |
|---|---|---|---|
| `cms_ncd` | [CMS MCD](https://www.cms.gov/medicare-coverage-database) / [Coverage API](https://api.coverage.cms.gov/docs/swagger/index.html) | JSONL drop (`data/policy_sources/cms_ncd/`) | **RECONCILED** (2 docs) |
| `mac_lcd_nc` | MCD LCDs for Palmetto JM / NC | JSONL drop | **RECONCILED** (2 docs: L34425 NC-applicable + L35175 negative control) |
| `lcd_billing_coding_articles` | MCD articles | JSONL drop | **RECONCILED** (2 docs: A56729 + legacy A54118) |
| `ncci_ptp` | [CMS NCCI](https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits) | Bounded demo subset drop | **RECONCILED** (2 docs — not full quarter) |
| `ncci_mue` | CMS NCCI MUE releases | Policy note + synthetic demo MUE | **RECONCILED** (2 docs — confidential values not invented) |
| `medicare_other_payment` | [PFS RVU files](https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files) | Methodology note drop | **RECONCILED** (1 note) |

## Provenance correction (critical)

| ID | Prior claim | Verified finding | Action |
|---|---|---|---|
| L35175 | Linked as NC/JM MRI LCD | **Noridian J-F**; retired 2025-10-23; not NC | Removed from MRI links; kept as `NOT_APPLICABLE_OTHER_JURISDICTION` |
| A54118 | MRI article | Unverified / wrong chain | Removed from MRI links |
| L34425 | — | **Palmetto JM** includes NC | Linked to MRI |
| A56729 | — | Billing/coding article for L34425 | Linked to MRI |
| NCD220.2 | MRI NCD | Verified national (`NCDId=177`) | Kept / URL corrected |

## Upkeep model

1. **Weekly:** MCD bulk download check + Coverage API incremental (license-token flow where required).  
2. **Quarterly:** Full NCCI PTP/MUE file replace + release-to-release diff.  
3. **Versioning:** Never overwrite; store `source_version`, checksum, effective dates.  
4. **NC filter:** Demonstrate LCDs must pass Palmetto JM / NC applicability; library may hold other jurisdictions.  
5. **Honesty:** Drop stubs and demo subsets are labeled; never silently promoted as complete CMS inventory.

## Actual reconcile counts (batch `reconcile-20261103T115616Z`)

See companion `MEDICARE_INVENTORY_RECONCILIATION.md`.

## Blockers / incomplete

- Live Coverage API license-token automation not productionized (drop-first path works).  
- Full NCD/LCD/article historical versions not reconstructed.  
- Full quarterly NCCI files not loaded — bounded demo subsets only.  
- Unpublished MUE values will never be fabricated.
