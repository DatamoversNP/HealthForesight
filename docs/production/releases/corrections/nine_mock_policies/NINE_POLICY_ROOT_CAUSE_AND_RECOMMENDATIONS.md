# Nine Mock Policies — Root Cause & Recommendations

**Review status:** Diagnostic complete. **No data, baseline, formula, or demo/production mutations performed.**  
**API deploy:** Not part of this review (prior image build still failed; not assumed current).

## 1. Direct answer: are the low PMPMs wrong?

**No — not as arithmetic defects, and not as underpriced MRI/therapy dollars.**

They are **book-level service allowed PMPMs**:

```
policy service allowed ÷ ~5.55M tenant enrollment member-months
```

Per-line allowed amounts match the synthetic fee schedules (~$900 for 72148, etc.). The MRI lifecycle fixture’s illustrative **$2.40** PMPM is the same order of magnitude as the stored MRI **$2.48**.

What *is* wrong if left unlabeled: treating that figure as “PMPM among the MRI-eligible cohort” or as policy savings. Among members with a selected MRI claim, enrollment-based PMPM is ~$138.

## 2. Per-policy justified results

| Policy | Primary class | Secondary | Result | One-line justification |
|---|---|---|---|---|
| MRI | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE | **REVIEW_REQUIRED** | Arithmetic OK; label as book-level service PMPM |
| NCD 220.2 | EXPECTED_LOW_PMPM | POLICY_CONFIGURATION_ISSUE, DENOMINATOR_OR_GRAIN_ISSUE | **REVIEW_REQUIRED** | Proxy commercial measurement ≠ Medicare NCD authority |
| LCD L34425 | EXPECTED_LOW_PMPM | POLICY_CONFIGURATION_ISSUE, DENOMINATOR_OR_GRAIN_ISSUE | **REVIEW_REQUIRED** | Proxy commercial/NC-cleared measurement ≠ LCD authority |
| Infusion | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE, INSUFFICIENT_EVIDENCE | **REVIEW_REQUIRED** | Book PMPM OK; drug/admin/facility split incomplete on claims_lines |
| Therapy | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE | **REVIEW_REQUIRED** | Low book PMPM expected for PT codes |
| MUE | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE, INSUFFICIENT_EVIDENCE | **REVIEW_REQUIRED** | Candidate spend ≠ edit-eligible exposure |
| PTP | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE, INSUFFICIENT_EVIDENCE | **REVIEW_REQUIRED** | Pair-shaped claims ≠ proven PTP violations |
| Imaging SOS | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE | **REVIEW_REQUIRED** | Partitioned from MRI via service_category |
| MPPR | EXPECTED_LOW_PMPM | DENOMINATOR_OR_GRAIN_ISSUE, INSUFFICIENT_EVIDENCE | **REVIEW_REQUIRED** | Candidate multi-proc spend ≠ applied reduction |

**No policy received FAIL for a reproducible product calculation defect** on the formula that was stored.

## 3. What needs to change (recommendations only)

### A. Metric contract / labeling (smallest, highest leverage)

**Issue:** DENOMINATOR_OR_GRAIN_ISSUE (semantic), not bad SQL for the stored formula.  
**Recommend:** Persist and display explicit metric identity, e.g.:

- `allowed_pmpm_book_service` = selected allowed / enrolled book MM  
- `allowed_pmpm_selected_claimant_enrollment` = selected allowed / MM of members with ≥1 selected claim  

Do **not** change dollars to make book PMPM larger.

**Needs authorization** before any product code change.

### B. NCD / LCD configuration hygiene

**Issue:** POLICY_CONFIGURATION_ISSUE — authoritative MEDICARE/(NC) scope was cleared for directional measurement.  
**Recommend:** Keep two explicit objects:

1. Authoritative applicability (MEDICARE / NC / authority IDs) — review-only  
2. Synthetic commercial proxy measurement run — labeled `SYNTHETIC_ANALYTICAL_PROXY`  

Do not certify the commercial book as NCD/LCD-applicable.

### C. Mechanism baselines vs edit engines

**Issue:** INSUFFICIENT_EVIDENCE for MUE/PTP/MPPR “opportunity.”  
**Recommend:** Leave FIXED baselines as **candidate exposure**. Mechanism engines (edit tables, reduction factors) remain separate lifecycle steps; do not read baseline PMPM as savings.

### D. Synthetic data regeneration

**Issue:** DATA_REALISM_ISSUE — **not confirmed** for explaining low PMPM.  
**Recommend:** **Do not regenerate** claims to inflate PMPM. Optional later work (authorization required): enrich POS/facility/drug components for infusion/SOS demos without breaking longitudinal keys.

### E. Existing FIXED baselines

**Recommend:** **Retain** the nine CY2025 FIXED baselines as evidence of book-level service PMPM. If a future run needs eligible-cohort denominators, create **new versioned baselines** — do not overwrite these.

## 4. Acceptance checklist mapping

| Criterion | Status |
|---|---|
| 1. All nine PMPMs independently reconciled | **Met** (exact) |
| 2. Denominator known | **Met** (tenant MM ≈ 5.55M) |
| 3. Financial grain established | **Met** (claim lines) |
| 4. Realism via distributions | **Met** |
| 5. Policy applicability verified | **Met** (with NCD/LCD proxy callouts) |
| 6. NCD/LCD authority ≠ commercial proxy | **Documented** |
| 7. Reproducible calc defect test | **N/A — none confirmed** |
| 8. No baseline/canonical mutation | **Met** |
| 9. PASS / REVIEW_REQUIRED / FAIL per policy | **All REVIEW_REQUIRED** (labeling + NCD/LCD + mechanism semantics) |
| 10. Clear answer on what to change | **Data: none for PMPM. Config/labels: yes (awaiting auth). Engine: no defect for stored formula.** |

## 5. Authorized follow-up (2026-11-07)

User authorized **5K-only measurement-book re-baseline**.

Executed:

- New FIXED CY2025 baselines **version 2** on `SYNTHETIC_NINE_POLICY_5K_V1` only (claims + 60,000 enrollment MM)
- Prior combined-book baselines (**version 1**) preserved
- Policies stamped with explicit `measurement_book` contract

Evidence: `NINE_POLICY_BASELINE_2025_5K_REPORT.json`

## 6. Explicit non-actions still in force

- No synthetic regeneration to chase a target PMPM  
- No overwrite of v1 combined-book baselines  
- No formula patch “to improve PMPM”  
- No invented clinical criteria, payment factors, or savings  
- No Dec4 / production changes  
- No API redeploy claimed as part of this work
