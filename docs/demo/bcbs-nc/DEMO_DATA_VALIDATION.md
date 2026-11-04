# DEMO_DATA_VALIDATION — Blue Cross NC executive demo

**Policy under test:** Outpatient MRI Prior Authorization  
**Policy ID:** `d403f101-08dd-45c9-ab83-d42e37c62018`  
**Environment audited:** Azure API `https://healthforesight-api.azurewebsites.net` + Data Voyager UI  
**Audit date:** 2026-11-01  
**Data classification:** Synthetic / illustrative demonstration data — **not** Blue Cross NC production claims, medical policies, or Carelon program configurations.

---

## Continuity checklist

| Layer | Record | Compatible with MRI story? | Notes |
|---|---|---|---|
| Policy | `d403f101-…` ACTIVE, `PRIOR_AUTH` | PASS | Description: reduce inappropriate outpatient MRI imaging |
| Objectives / governance in metadata | empty `policy_metadata_json` on detail | FAIL (soft) | Narrate from description + Scope/Levers tabs in workspace; do not invent formal OKR IDs |
| Scope markets | `NYC`, `DFW` (not NC) | WARN | Explicitly call illustrative; do **not** say “your NC markets” |
| Policy-specific baseline (canonical) | `9f996021-60b9-4252-8e84-cacac048cca8` window **2024-12-31 → 2025-12-31** | PASS | 6,722 claims; 2,382 members; 30,966 member-months; paid ~$4.78M; allowed ~$5.32M; Advanced Imaging provider archetypes present |
| Older policy baselines | `4a1adda1-…` (2022–2023), `926abfe0-…` (2023–2025) | DO NOT USE on camera | Wrong window / thin denominators |
| General (portfolio) baseline | 3 general windows exist | DO NOT USE for MRI story | Portfolio ≠ policy population |
| Predicted impact | GET `/policies/{id}/predicted-impact` | PASS (with caveats) | Method `ELASTICITY_MODEL`; util **−14.4%**; cost **−13.0%**; cost_change_pmpm **−$22.26**; substitution toward URGENT_CARE / OFFICE_VISIT; provider/patient response blocks present |
| Predicted baseline linkage | API field `baseline_id` `51ad0671-…` resolves to same metrics as `9f996021-…` (2,382 members) | PASS | ID aliasing is messy; **metrics** match policy baseline population |
| Observation (canonical for verdict/latest) | `b227220e-f9e0-45a6-8938-d55aad1fe25d` period **2024-01-01 → 2026-08-14** | CONDITIONAL | vs_baseline: util **−10.1%**, cost **−12.5%**; `verdict_status` **ON_TRACK**; has `prediction_id` |
| Monday-demo observations | `obs-mon-20260731-d403f101` etc. | DO NOT USE as primary | Extreme util/1k (~11k) vs policy baseline (~217–492); incompatible absolute denominators; good for internal debugging only |
| What-If completed scenarios | `f73e506f-…` (2026-11-01), `95283231-…` | PASS (fallback) | Prefer prevalidated completed run on camera if live POST is slow |
| Policy verdicts (Azure post-deploy) | MRI = **ON_TRACK** / “Saving / on track”; obs `b227220e-…` | **PASS** | Fixed via `latest_only=True` on verdicts route; re-verified 2026-11-01 |
| Decisions | GET `/decisions?policy_id=…` returns approval decision | PASS (supporting) | Title includes Outpatient MRI Prior Authorization |

---

## Unit / denominator integrity

| Measure | Policy baseline (`9f996021`) | Predicted impact | Latest observation (`b227220e`) | Safe to show on camera? |
|---|---|---|---|---|
| Member count | 2,382 | baseline_reference.member_count 2,382 | unique_members **13,997** | **No** — do not claim same population |
| Member-months | 30,966 | 30,966 | **447,904** | **No** — observation window much wider |
| Utilization per 1k | not stored on baseline row; pred ref **217.1** | change −14.4% / −31.3 per 1k | baseline_in_obs **491.7** → obs **442.2** (−10.1%) | Speak in **% change** only; do not equate 217 vs 491 absolute levels |
| Cost PMPM | not on baseline metrics blob; pred ref **$171.77** | −$22.26 PMPM (−13%) | baseline_in_obs **$145.15** → obs **$127.04** (−12.5%) | Speak in **% / directional PMPM** only |
| Total claims | 6,722 | derived | 220,228 | Do not compare totals across layers |

**Rule for narration:** Never say the observation “used the same 2,382-member baseline.” Say: “relative to the pre-period reference embedded in this observation, utilization and cost moved down… expected directionally aligned with the prospective estimate.”

---

## Story that the data actually supports

**Supported (honest):**
1. There is a governed MRI PA policy asset.
2. There is a **policy-specific** pre-period baseline with imaging-relevant segments.
3. There is a prospective elasticity prediction (util/cost down; substitution flagged).
4. Latest observation is **ON_TRACK**: util and cost below its embedded baseline.
5. Completed What-If scenarios exist for MRI.
6. After the verdicts fix is deployed, climax can show MRI **ON_TRACK** with recommendation text from `compute_verdict`.

**Not supported (do not claim on camera):**
- “Actual Blue Cross NC / Carelon MRI program results”
- Causal proof or guaranteed savings
- Site-of-care mix shift proven in observation UI for this record
- “Appears successful on util but financial backfire” — latest obs shows **both** util and cost improved vs its baseline
- Exact PMPM continuity from predicted-impact card → observation card

---

## Pass/fail summary

| Gate | Status |
|---|---|
| Same policy ID across modules | PASS |
| Policy-specific baseline exists | PASS |
| Predicted impact returns values | PASS |
| Observation with vs_baseline / vs_predicted | PASS (latest) |
| Absolute denominator continuity | **FAIL** — narrate % only |
| Verdicts show MRI evidence (Azure live) | **PASS** (ON_TRACK) |
| What-If reproducible result | PASS (completed analyses) |
| Ready to record client video | **YES** (with narration caveats) |

---

## Cleared for recording

1. ~~Deploy verdicts `latest_only` fix~~ done  
2. Rehearse narration that avoids absolute denominator claims  
3. Prefer What-If **run history** completed scenario unless live simulate verified same day  
4. ~~Two consecutive full UI rehearsals ≤ 5:00~~ done (4:30 and 4:40)
