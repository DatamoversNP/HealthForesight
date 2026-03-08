# What-If Analysis: Gap Analysis and Fixes

This document summarizes the current state of the what-if (scenario) analysis feature, **gaps to fill**, and **issues fixed** so you can complete the feature.

---

## What Exists Today

| Layer | Status | Notes |
|-------|--------|--------|
| **API** | ✅ | `POST /analyses/simulate`, `GET /analyses/{id}/results` (whatif_scenario from DB), list/get analyses |
| **Worker** | ✅ | `whatif_scenario_job` runs simulation, stores in `WhatIfScenarioResult` |
| **Simulation** | ✅ | `uepi_worker.whatif.simulate_scenario` – elasticity, projections, Monte Carlo, sensitivity, tradeoff, risk |
| **Frontend** | ✅ | WhatIfAnalysisPage – policy select, scenario params, run, results, comparison, elasticity, scenario accuracy |
| **Scenario accuracy** | ✅ | Link scenario to policy, compute accuracy vs observations; **now reads from DB** when `data_uri` is null |
| **Auth** | ⚠️ | Analyses use `verify_token`; dashboard uses `get_demo_current_user` – see gaps below |

---

## Issues Fixed (This Pass)

1. **Worker return bug**  
   After storing results in the DB, the worker returned `result_uri: f"{settings.object_storage.bucket}/{result_key}"` but `settings` and `result_key` were undefined → `NameError`.  
   **Fix:** Return `"result_uri": "database"` when results are stored in the database.

2. **Scenario accuracy with DB-stored results**  
   `link_scenario_to_policy` and `compute_scenario_accuracy` only read from `data_uri` (file://). When the worker stores in `WhatIfScenarioResult`, `data_uri` is null, so both functions failed.  
   **Fix:** In `storage_scenario_accuracy.py`, when `data_uri` is null/empty, load scenario result from `WhatIfScenarioResult` by `analysis_id` (and tenant_id); keep file:// as fallback for legacy data.

---

## Gaps to Fill

### 1. **Celery / worker must be running**

- The API only **enqueues** the job: `whatif_scenario_job.delay(...)`. The actual simulation runs in the **worker**.
- If Celery is not running, analyses stay **PENDING** and the UI will poll until timeout.
- **Action:** Document and/or script: start Celery worker (e.g. `celery -A uepi_worker worker -l info`). Optionally add a health check that confirms worker is connected.

### 2. **Baseline data source (claims)**

- `whatif_scenario_job` calls `load_claims_data(tenant_id, baseline_filters, start, end)` from `uepi_worker.analytics`.
- That function loads from **S3** (object storage) with partition paths like `{tenant_id}/curated/claims/year=.../month=.../lob=.../market=.../data.parquet`.
- If you use **DB or local Parquet** instead of S3, baseline can be empty → simulation runs on empty data → unhelpful or zero results.
- **Action:** Either (a) ensure curated claims are written to S3 in that layout, or (b) add a DB/local path in `load_claims_data` (or a separate loader) and use it when S3 is not configured.

### 3. **Auth consistency for local/demo**

- Analysis endpoints use `verify_token`; dashboard and policy-performance use `get_demo_current_user`.
- With only a dev token, what-if calls may work if the client sends the token; without it, 401.
- **Action (optional):** For local/dev, use `get_demo_current_user` for analyses (or a subset) so what-if works without real login. Keep `verify_token` for production.

### 4. **Analysis name**

- `create_simulate_analysis` does not set `Analysis.name`; it stays null. List analyses still returns `name`.
- **Action (optional):** Set a default name when creating SIMULATE analysis, e.g. `f"What-If {policy_name} {created_at}"` or allow the client to send `name` and persist it.

### 5. **get_analysis_results and file://**

- `get_analysis_results` checks DB first (e.g. `WhatIfScenarioResult`), then **S3** via `data_uri`. It does **not** handle `file://` URIs.
- If you have old file-based result indices with `data_uri=file://...`, those results are not loaded.
- **Action (optional):** If you need to support legacy file-based results, add a branch in `get_analysis_results` to read from `file://` when `data_uri` starts with `file://`.

### 6. **Error handling and user feedback**

- If the worker fails (e.g. missing baseline, elasticity error), analysis status becomes FAILED; the API does not persist a structured error message per analysis.
- **Action (optional):** Store a short `error_message` or `failure_reason` on Analysis (or AnalysisRun) when status is FAILED so the UI can show “Why did this fail?”.

### 7. **Elasticity models**

- Simulation uses elasticity curves; worker loads “latest” from `storage_learning.get_latest_elasticity_model`.
- If no elasticity model exists for the policy type, simulation still runs (with defaults or no curves), but projections may be less meaningful.
- **Action:** Ensure at least one elasticity run (or seed data) exists for the policy types you use in what-if, or document “best effort without elasticity.”

### 8. **Scenario comparison and history**

- UI loads “previous scenarios” by listing SIMULATE analyses and fetching results for each. This works with DB-stored results.
- **Action:** None required for basic completion; optional: add filters (by policy, date range) or pagination if the list grows large.

---

## Suggested Priority

| Priority | Item | Effort |
|----------|------|--------|
| P0 | Worker return bug, scenario accuracy DB path | Done |
| P1 | Celery worker running + docs/script | Small |
| P1 | Baseline data: S3 vs DB/local and empty baseline handling | Medium |
| P2 | Auth: demo user for analyses in dev | Small |
| P2 | Analysis name and optional file:// in get_analysis_results | Small |
| P3 | FAILED analysis error message, elasticity docs | Small |

---

## How to Validate End-to-End

1. **Start API + worker**  
   - API: `uvicorn` (or your start script).  
   - Worker: `celery -A uepi_worker worker -l info` (from worker app directory).

2. **Create a what-if run**  
   - In the UI: pick a policy, set scenario params (e.g. lever adjustments), set baseline filters, Run.  
   - Or: `POST /api/v1/analyses/simulate` with `policy_id`, `scenario_params`, `filters`.

3. **Wait for completion**  
   - Poll `GET /api/v1/analyses/{id}` until `status` is COMPLETED or FAILED.

4. **Fetch results**  
   - `GET /api/v1/analyses/{id}/results?result_type=whatif_scenario` → should return `results.whatif_scenario` from DB.

5. **Scenario accuracy (optional)**  
   - Link scenario to policy: `POST /api/v1/scenario-accuracy/link`.  
   - Compute accuracy: `POST /api/v1/scenario-accuracy/compute` with `observation_id`.  
   - Both should succeed now when the scenario result is stored in the DB (data_uri null).

---

## Files Touched in This Pass

- `apps/worker/src/uepi_worker/tasks.py` – return `result_uri: "database"` instead of undefined `settings`/`result_key`.
- `apps/api/src/uepi_api/storage_scenario_accuracy.py` – when `data_uri` is null/empty, load scenario result from `WhatIfScenarioResult` in both `link_scenario_to_policy` and `compute_scenario_accuracy`.
