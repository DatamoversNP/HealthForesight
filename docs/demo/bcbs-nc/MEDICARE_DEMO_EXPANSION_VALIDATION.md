# Medicare Demo Expansion Validation

**Generated:** 2026-11-03  
**Frozen three remain:** MRI / MPPR / SOS — regression **PASS** ($600/+120, $520/+260)

## Source codesets (reference library — not catalog seeds)

| Family | Count | State |
|--------|------:|-------|
| cms_ncd | 345 | RECONCILED (Coverage API) |
| mac_lcd_nc | 938 | RECONCILED (NC; 195 Palmetto JM) |
| lcd_billing_coding_articles | 2118 | RECONCILED |
| ncci_ptp / ncci_mue | 0 authoritative | ACCESS_BLOCKED (cms.gov 403) |

See `evidence/SOURCE_CODESET_REPORT.md`. No new Representative Payer catalog seed rows from codeset ingest.

## Four independent lifecycles

| Policy | ID | Mechanical | What-if | Validation class |
|---|---|---|---|---|
| NCCI PTP Bundling (Demo) | `58b839b5-…` | $800 PASS (modifier-59 bypass) | indicator 0 → +$400 | **FULLY_VALIDATED_DEMO** (fixture; quarterly NCCI blocked) |
| NCCI MUE Units (Demo) | `e11b049d-…` | $100 PASS | mue 4→3 delta PASS | **FULLY_VALIDATED_DEMO** (synthetic MUE labeled) |
| Outpatient Therapy Coverage (Demo) | `f2b8e7f3-…` | $80 PASS | coverage what-if N/A | **FULLY_VALIDATED_DEMO** (mechanical + **L34428** JM LCD link) |
| Infusion Site-of-Care (Demo) | `11218053-…` | $3600 PASS | steer 2→3 HOPD +$1800 | **FULLY_VALIDATED_DEMO** |

Machine evidence: `evidence/EXPANSION_LIFECYCLE_VALIDATION.json`, `evidence/EXPANSION_VALIDATION.json`.

**Disclosed limitations:** synthetic fixtures; NCCI quarterly files not on this host; empirical PTP needs modifier column on claims_lines.

## Dec 4 live-demo path (unchanged)

**Primary:** MRI → MPPR → SOS → Medicare Rules → Objectives Health  
**Expansion:** independently validated above — optional add-ons, not substitutes for the frozen three.
