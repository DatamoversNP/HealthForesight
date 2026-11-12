# Nine Mock Policies — Scope & Applicability Validation

**Mode:** Read-only  
**Evidence:** stored policy metadata + independent CY2025 claim selection in `NINE_POLICY_AUDIT_RESULTS.json`

## 1. Common selection contract used by stored baselines

For each policy, selected history = claim lines where:

1. `service_date` in CY2025  
2. CPT/HCPCS ∈ configured codeset (scope + levers)  
3. `service_category` ∈ configured synthetic categories (e.g. `mri`, `sos`, `mppr`)  
4. No `preferred_source_system` filter  
5. After directional alignment: NCD/LCD **lob/markets cleared** for measurement  

Authoritative PDF intent and synthetic measurement must stay distinct.

## 2. Policy-by-policy

### Outpatient MRI Prior Authorization — `mri`

| Check | Result |
|---|---|
| Codes | 72148, 72149 |
| Excluded E/M in selected set | **0** lines with 99213/99214 in `service_category=mri` |
| Setting | Synthetic POS present in generator; operational filter did not require POS in baseline script |
| Product | Commercial/SYNTHETIC book (no LOB filter) |
| Auth decisions inferred from claims? | **No** |
| Verdict | Codeset selection is coherent for a lumbar MRI mock. Book-level PMPM ≈ $2.48 is plausible. |

### NCD 220.2 — `ncd`

| Check | Result |
|---|---|
| Codes used in measurement | 70551, 70553 + `service_category=ncd` |
| Authoritative intent | Medicare NCD study — MEDICARE LOB was configured at seed |
| What changed for baselines | MEDICARE filter **cleared** → commercial/synthetic **analytical proxy** (`synthetic_scope_alignment`) |
| Certified as NCD-applicable commercial population? | **No — must not be** |
| Verdict | **REVIEW_REQUIRED.** Preserve authoritative MEDICARE scope separately from proxy measurement labels. |

### LCD L34425 — `lcd`

| Check | Result |
|---|---|
| Codes | 70540, 70542 + `lcd` |
| Authoritative intent | Contractor/state LCD — MEDICARE + NC were seeded |
| Measurement | MEDICARE/NC cleared for directional commercial proxy |
| Verdict | Same as NCD — proxy only; do not certify NC LCD applicability on this book. |

### Infusion Site of Care — `infusion`

| Check | Result |
|---|---|
| Codes | 96413, J1745 |
| Financial split | Operational baseline sums line allowed only; drug vs admin vs facility not fully decomposed in `claims_lines` |
| Site variation | 96413 bimodal allowed supports site mix |
| Verdict | Candidate infusion spend measurable; mechanism site-of-care differentials need entity-pack site/episode fields for deeper analysis. |

### Outpatient Therapy — `therapy`

| Check | Result |
|---|---|
| Codes | 97110, 97112, 97140 |
| Units | Present; mean line allowed reflects multi-unit therapy |
| Benefit limits | Not parameterized in this baseline |
| Verdict | Therapy monitoring population is code-consistent; not a visit-cap outcome. |

### MUE — `mue`

| Check | Result |
|---|---|
| Codes | 97110 + `mue` |
| Baseline meaning | Candidate unit-bearing spend, **not** MUE edit violations |
| Edit table / thresholds | Not configured (`AWAITING_CONFIGURATION_PARAMETERS` originally) |
| Verdict | Do not interpret $0.36 PMPM (or line counts) as edit opportunity. |

### PTP — `ptp`

| Check | Result |
|---|---|
| Codes | 70551, 70553 |
| Claim shape | 2 lines / header — pair-like |
| Baseline meaning | Candidate co-occurring codes, **not** proven PTP violations |
| Modifiers / edit indicators | Not applied in baseline selection |
| Verdict | Exposure set only until edit-table parameters exist. |

### Imaging Site of Service — `sos`

| Check | Result |
|---|---|
| Codes | 72148, 72149 (same anatomy family as MRI) |
| Separation from MRI | Via `service_category=sos` vs `mri` |
| POS | Generator uses 11/22; baseline script did not filter POS |
| Verdict | Synthetic partition works; POS/facility classification for true SOS differentials needs explicit POS filters if claimed. |

### MPPR — `mppr`

| Check | Result |
|---|---|
| Codes | 27447, 64483 |
| Claim shape | ≈2 lines/header |
| Baseline meaning | Candidate multiple-procedure spend, **not** applied MPPR reductions |
| Pricing factors | Not applied in FIXED baseline |
| Verdict | Correct as exposure; incorrect if read as savings. |

## 3. Authoritative scope vs synthetic proxy

| Policy | Authoritative configuration | Synthetic measurement used for FIXED baseline |
|---|---|---|
| MRI, Therapy, Infusion, MUE, PTP, SOS, MPPR | Mock commercial candidate codesets | Same commercial/SYNTHETIC book |
| NCD | MEDICARE / NCD 220.2 study | **Proxy:** commercial book after clearing MEDICARE |
| LCD | MEDICARE + NC / L34425 | **Proxy:** commercial book after clearing MEDICARE+NC |

Clearing filters for directional measurement did **not** certify those populations as Medicare/NC applicable. It created an explicitly labeled analytical proxy (see `synthetic_scope_alignment` on policy metadata).

## 4. Service-category as applicability dimension

Shared codes (e.g. 72148 on MRI and SOS; 70551/70553 on NCD and PTP) are split by synthetic `service_category` tags. That is a **generator bookkeeping device**. It is not the same as a payer coverage schedule.

Recommendation (awaiting authorization): document whether `service_category` is (a) an official applicability axis for these mock policies, or (b) only a synthetic partition that should be replaced by POS/product/benefit rules when definitions mature.
