# What-If Analysis: Business-Perfect Solution (Analysis Only)

This document analyzes the current what-if (scenario simulation) flow and what would need to change for a **business-perfect** solution. **No code changes**—analysis only.

---

## Current Flow (Summary)

1. **API** `POST /analyses/simulate`: Accepts `policy_id`, `scenario_params`, `filters`. Loads policy from DB, builds **policy filters** via `build_policy_claims_filters(policy_dict)` (scope + levers merged), passes `worker_filters` (lob, markets, cpt_codes, service_categories) to the worker. Creates Analysis (type SIMULATE, status PENDING) and AnalysisConfig (treatment_filters = worker_filters). Enqueues Celery task `whatif_scenario_job(tenant_id, analysis_id, policy_id, scenario_params, baseline_filters)`.

2. **Worker** `whatif_scenario_job`:  
   - **Primary:** Loads baseline claims from **S3** via `load_claims_data(tenant_id, baseline_filters, start, end)` (partition paths by tenant/year/month/lob/market; then in-memory filter by cpt_codes, service_categories).  
   - **Fallback:** If S3 returns empty, loads from **database** via `load_claims_from_database(..., filters=db_filters)` where `db_filters` are built from `build_policy_claims_filters(policy_dict)` again (lob, markets, cpt_codes, service_categories).  
   - Runs `simulate_scenario(tenant_id, policy, baseline_df, scenario_params, elasticity_curves)`.  
   - `simulate_scenario` computes baseline metrics from the **claims DataFrame** (`compute_baseline_metrics(baseline_df)`), then runs projections, Monte Carlo, sensitivity, tradeoff, risk.  
   - Stores result in `WhatIfScenarioResult` and sets analysis status to COMPLETED (or FAILED).

3. **Simulation** (`uepi_worker.whatif.simulate_scenario`): Expects a **claims DataFrame** (not pre-computed baseline metrics). It derives baseline_metrics from that DataFrame and uses the same DataFrame for utilization/cost projections by service_category, Monte Carlo, and sensitivity. So baseline data is always “claims we loaded with filters.”

---

## What’s Already Aligned

| Area | Status |
|------|--------|
| **Policy filters (API)** | API builds `policy_dict` from `policy.policy_metadata_json` (scope, policy_levers, logic, policy_logic) and calls `build_policy_claims_filters(policy_dict)` → same helper as baselines, predicted impact, observations. |
| **Worker filters** | Worker receives `baseline_filters` from API. On DB fallback, worker rebuilds filters with `build_policy_claims_filters(policy_dict)` (same policy_metadata). So **filter logic is consistent** when DB path is used. |
| **Filter keys passed to worker** | API sends lob, markets, market, cpt_codes, service_categories. DB loader and S3 loader use these. |
| **Result storage** | Results stored in DB (`WhatIfScenarioResult`); scenario accuracy and links work with DB-stored results. |

---

## Gaps for Business-Perfect

### 1. **Baseline source and policy-specific baseline**

- **Today:** Baseline = claims loaded from S3 (by lob/market partition, then filtered by cpt/service_categories) or from DB with same filters. Baseline metrics are **recomputed** from that claims set in the worker.
- **Issue:** Baselines and predicted impact use **policy-specific stored baselines** (same filters, aggregate-only, no row limit). What-if uses a **separate load** (S3 or DB claims) and recomputes metrics. So:
  - If S3 is empty and DB has claims → what-if can use DB and stay aligned.
  - If S3 has data but DB is source of truth for “policy baseline” → what-if might use a different population (e.g. S3 partition layout doesn’t include procedure_codes), so baseline metrics can **diverge** from the stored policy baseline and from predicted impact/observations.
- **Business-perfect direction:**  
  - **Option A:** Use **policy-specific baseline** when available: `get_latest_baseline(tenant_id, policy_id=policy_id, baseline_type=None)`. If present, pass its `baseline_metrics` into the simulation and either (a) add a “metrics-only” simulation path that doesn’t need a claims DataFrame, or (b) still load claims for sensitivity/Monte Carlo but use stored baseline_metrics as the official baseline.  
  - **Option B:** If no stored baseline, keep current behavior but ensure the **only** source of claims is the **database** with **exactly** `build_policy_claims_filters(policy)` (and optionally deprecate or clearly document S3 as legacy).  
  So: **align what-if baseline with the same policy-scoped baseline used for baselines, predicted impact, and observations.**

### 2. **diagnosis_codes not passed to worker**

- **Today:** `worker_filters` from API include lob, markets, cpt_codes, service_categories. **diagnosis_codes** from `build_policy_claims_filters` are **not** included.
- **Issue:** Policies that scope by diagnosis (e.g. ICD-10) will have what-if run on a broader or wrong set of claims than baseline/predicted impact.
- **Business-perfect:** Include `diagnosis_codes` in the payload to the worker and in DB (and S3, if used) filter logic so what-if uses the same diagnosis scope as the rest of the product.

### 3. **Empty baseline behavior**

- **Today:** If both S3 and DB return no claims, `baseline_df` is empty. `compute_baseline_metrics(empty)` returns zeros. Simulation runs and produces zero-based projections.
- **Issue:** User sees a “successful” scenario with zeros instead of a clear “no data for this policy scope.”
- **Business-perfect:** If baseline is empty after both S3 and DB attempts: set analysis status to FAILED, store a short error (e.g. “No claims found for policy scope; check scope and data availability”) and optionally return a structured “no data” result so the UI can show a clear message instead of zeroed charts.

### 4. **S3 vs DB as source of truth**

- **Today:** Primary is S3 (`load_claims_data`); DB is fallback. S3 partition key is `tenant/year/month/lob/market` — no procedure_codes or service_categories in the path, so filtering by cpt/service_categories is in-memory after load.
- **Issue:** If production uses DB as source of truth (as with baselines/observations), what-if should not depend on S3 for “correct” baseline. Otherwise baseline can differ from policy baseline and predicted impact.
- **Business-perfect:** Treat **database** as the canonical source for what-if baseline (same as baselines/observations). Use `load_claims_from_database` with `build_policy_claims_filters(policy)` first; use S3 only as optional/legacy or remove it for this flow. Ensures one source of truth and same filters as elsewhere.

### 5. **Policy dict shape (API and worker)**

- **Today:** API builds `policy_dict` from `policy.policy_metadata_json` only (scope, policy_levers, logic, policy_logic). No `id`, `name`, or `metadata` key.
- **Note:** `build_policy_claims_filters` already supports scope/levers from top level or `policy_metadata_json`/`metadata`. So current shape is sufficient for filters. For consistency with `get_policy()` (e.g. if later you pass full policy to worker), you could add `policy_id`, `name`, and `metadata` (or `policy_metadata_json`) so the worker has the same shape as elsewhere.
- **Business-perfect (optional):** Build `policy_dict` in the same shape as storage’s `_policy_db_to_dict` (e.g. include id, name, scope at top level, metadata) so any code that expects “policy from get_policy” works unchanged.

### 6. **Analysis name and error message**

- **Today:** `create_simulate_analysis` does not set `Analysis.name`; it stays null. On FAILED, the worker sets status but a structured `error_message` is not always persisted for the UI.
- **Business-perfect (optional):** Set a default analysis name (e.g. “What-If &lt;policy_name&gt; &lt;date&gt;”) and persist a short `error_message` (or equivalent) when status is FAILED so the UI can show “Why did this fail?”

### 7. **Celery dependency and visibility**

- **Today:** Simulation runs only in the worker. If Celery is not running, analyses stay PENDING.
- **Business-perfect (operational):** Document and/or script worker startup; optionally add a health check that confirms worker connectivity so the UI or support can detect “worker not running” and show a clear message.

---

## Summary: What to Change (Conceptually)

| Priority | Change | Purpose |
|----------|--------|--------|
| **P0** | Use **policy-specific baseline** when available (same as predicted impact/observations); optionally “metrics-only” path or use stored baseline_metrics as baseline and load claims only where needed for sensitivity/Monte Carlo. | Align what-if baseline with rest of product; same numbers as policy baseline and predicted impact. |
| **P0** | Treat **DB as primary** (or only) source for baseline claims; same filters as baselines (`build_policy_claims_filters` + aggregate/load). | Single source of truth; no S3/DB divergence. |
| **P1** | Pass **diagnosis_codes** in worker_filters and apply in load (DB and, if kept, S3). | Full scope alignment for policies that use diagnosis filters. |
| **P1** | If baseline is **empty** after all load attempts: **FAIL** analysis and persist a clear “no data for policy scope” message. | Avoid zeroed, misleading results. |
| **P2** | Set **analysis name** and persist **error_message** on FAILED. | Better UX and support. |
| **P2** | Worker/ops: document and health-check **Celery worker**. | Clear operational model and failure mode. |

---

## Files Involved (Reference Only)

- **API:** `apps/api/src/uepi_api/routers/analyses.py` — `create_simulate_analysis`, policy_dict, worker_filters.
- **Worker:** `apps/worker/src/uepi_worker/tasks.py` — `whatif_scenario_job`, load_claims_data, DB fallback, simulate_scenario.
- **Worker:** `apps/worker/src/uepi_worker/analytics.py` — `load_claims_data` (S3).
- **Worker:** `apps/worker/src/uepi_worker/whatif.py` — `simulate_scenario`, `compute_baseline_metrics`, projections, Monte Carlo, sensitivity.
- **API:** `apps/api/src/uepi_api/database_claims_loader.py` — `load_claims_from_database` (DB fallback).
- **Shared:** `apps/api/src/uepi_api/services/policy_scoped_data_generation.py` — `build_policy_claims_filters`.
- **Storage:** `apps/api/src/uepi_api/storage_baselines.py` — `get_latest_baseline`.

No code changes were made in this pass; the above is analysis only for a business-perfect what-if solution.
