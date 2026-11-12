# Nine Mock Policies — Synthetic Data Realism Assessment

**Mode:** Read-only against lean staging CY2025 claims/enrollment  
**Evidence:** `NINE_POLICY_AUDIT_RESULTS.json`  
**Scope:** Suitability for credible mock-client demos — not certification as a real commercial book.

## 1. Overall CY2025 financial picture

| Statistic | Value |
|---|---:|
| Claim lines | 1,013,937 |
| Median allowed / line | $327.07 |
| Mean allowed / line | $473.68 |
| Max allowed / line | $5,249.45 |
| Negative allowed lines | **0** |
| Zero allowed lines | **0** |
| Lines > $100,000 | **0** |

500K longitudinal mean allowed ≈ $457; 5K nine-policy book mean ≈ $1,054 (policy-dense, higher acuity codes by design).

## 2. Procedure-level allowed distributions (combined book)

| Code | Lines | Mean | P10 | P50 | P90 | Generator anchor |
|---|---:|---:|---:|---:|---:|---|
| 72148 | 22,845 | $983 | $889 | $900 | $1,137 | FEE / 5K range ~$900–2200 |
| 72149 | 2,806 | $1,545 | $1,025 | $1,538 | $2,065 | 5K MRI range |
| 70551 | 17,372 | $757 | $537 | $700 | $1,004 | FEE $700 |
| 70553 | 11,771 | $1,063 | $647 | $1,100 | $1,387 | FEE $1,100 |
| 70540 | 6,660 | $686 | $643 | $650 | $679 | FEE $650 |
| 96413 | 17,720 | $2,011 | $691 | $697 | $5,000 | FEE $5,000 HOPD / lower office |
| J1745 | 2,594 | $884 | $530 | $532 | $2,193 | 5K infusion drug |
| 97110 | 14,016 | $286 | $158 | $300 | $355 | therapy / MUE units |
| 27447 | 13,461 | $1,402 | $588 | $1,400 | $1,463 | FEE $1,400 |
| 64483 | 11,290 | $426 | $396 | $400 | $419 | FEE $400 |

Distributions are tightly clustered around the synthetic fee table. That is **internally consistent synthetic pricing**, not a random underpricing bug.

96413 is **bimodal** (P50 ≈ $697, P90 = $5,000), matching the longitudinal generator’s office vs HOPD site assumption. That is intentional synthetic variation, not corruption.

## 3. Utilization / concentration notes

- MRI selected population: 14,396 lines / 9,411 members ≈ 1.5 lines per claimant-year — repeat imaging is present but not extreme.
- MPPR: 22,580 lines / 11,290 headers = **exactly 2 lines/header** on average — consistent with paired multiple-procedure generation.
- PTP: 14,720 lines / 7,360 headers = **2.0** — consistent with pair generation.
- Therapy/MUE unit-bearing lines exist; mean allowed for 97110 (~$286–$311 in selected sets) is higher than the bare $50 FEE unit price because units accumulate on the line.
- Generator documentation (`longitudinal.py` ASSUMPTIONS) states background intensity is **intentionally low** and frequencies are **not** cited commercial benchmarks.

## 4. Longitudinal / entity caveats (already known)

| Topic | Assessment |
|---|---|
| 500K operational claims/enrollment | Present and dominant in CY2025 |
| 5K full entity pack | Loaded additively; richer than 500K for auth/episodes/contracts |
| Authorization events | Exist in 5K pack; **not** used in these baselines (claims-only) |
| Voids/reversals in selected CY2025 sets | No negative allowed lines observed |
| Real commercial benchmark fit | **Not established** — generators explicitly disclaim benchmark authority |

## 5. Realism verdict

| Classification | Finding |
|---|---|
| DATA_REALISM_ISSUE | **Not confirmed** for “amounts too low to explain PMPM.” Unit prices are fee-table consistent. |
| Expected synthetic behavior | Low book-level specialty PMPMs with realistic per-service allowed amounts |
| Regeneration needed? | **No** — not for the purpose of raising PMPM |
| External benchmarks | Not invented. Internal consistency + MRI fixture $2.40 PMPM are the available anchors |

**Do not regenerate synthetic dollars solely to inflate policy PMPMs.** The current distributions support mock-client demos if metrics are labeled correctly (book-level service PMPM vs eligible-cohort rates) and NCD/LCD authority is not overstated.
