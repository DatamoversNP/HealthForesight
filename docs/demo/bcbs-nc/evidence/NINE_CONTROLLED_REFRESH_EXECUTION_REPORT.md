# Nine Policy Controlled Refresh — Execution Report

Generated: `2026-11-04T06:13:09Z` (updated after in-process baseline retry)

## Claims mapping finding

Lumbar CPT `72148/72149/72158` exist **only** in claim markets `NYC/DFW/BOS` (zero rows in `market=NC`).  
`market=NC` has other MRI volume (e.g. `72141/72142`) but not the lumbar lever codes.

**MRI scope after refresh:** `states=['NC']` (jurisdiction) · `markets=['NYC','DFW']` (claim cohort for lumbar levers).

## What ran

| Key | Status | Baseline claims | Predicted | Observation | KA |
|---|---|---:|---|---|---|
| mri | REFRESHED | 6,722 | 200 OK | existing AT_RISK retained | frozen |
| mppr | REFRESHED | 193,386 | skip (no CPT levers) | existing retained | frozen |
| sos | REFRESHED | 149,695 | skip | existing retained | frozen |
| ptp | REFRESHED | 581,577 | skip (synthetic fixture) | existing retained | frozen |
| mue | REFRESHED | 581,577 | skip | existing retained | frozen |
| therapy | REFRESHED | 581,577 | skip | existing retained | frozen |
| infusion | REFRESHED | 1,452,520 | skip | existing retained | frozen |
| ncd | PROVENANCE_ONLY | — | — | — | frozen |
| lcd | PROVENANCE_ONLY | — | — | — | frozen |

**Summary:** refreshed **7** · provenance-only **2** · baseline failed **0**

## Guards

- Dec 4 known-answer fixtures **not overwritten**
- NCD/LCD remain provenance-only (no financial lifecycle)
- Catalog (~280) **not** mass-refreshed
- MRI Stage 3.5 regenerated; observation kept existing `AT_RISK` (no new IMPACT analysis row from predicted-impact POST)

Machine-readable: `NINE_CONTROLLED_REFRESH_EXECUTION_REPORT.json`
