# Fresh Demo Setup Plan – Most Impactful Demo

Goal: **Clean slate → 24 months historical (July 2023–June 2025) for 1000 members → load via pipeline → baselines + predicted impact → then July 2025–present data → one observation per month → refresh dashboards / Objectives Health / Policy Verdicts.**

---

## Implementation (scripts)

All scripts live under `scripts/` and are run from **repo root** with `python3 scripts/<name>.py [options]`.

| Phase | Script | Purpose |
|-------|--------|---------|
| 1 | `fresh_demo_clean.py` | Delete raw + derived data for demo tenant (`--dry-run` to preview) |
| 2 | `generate_24mo_historical_demo_data.py` | Generate 24 months historical CSVs (July 2023–June 2025), 1000 members |
| 3 | `load_fresh_demo_historical.py` | Load historical CSVs into DB via `CanonicalDataRepository` |
| 4 | `run_baseline_and_predicted_impact.py` | Baseline refresh + predicted impact for all policies |
| 5 | `generate_observation_period_demo_data.py` | Generate July 2025–present CSVs (same 1000 members) |
| 6 | `load_fresh_demo_historical.py --input-dir .../observation_period` | Load observation-period data into DB |
| 7 | `create_observations_per_month.py` | One observation per policy per month (mixed verdicts) |

**One-command full run:**

```bash
python3 scripts/run_fresh_demo_setup.py
```

**Single phase:**

```bash
python3 scripts/run_fresh_demo_setup.py --phase 3
```

**Dry-run (Phase 1 only, no deletes):**

```bash
python3 scripts/run_fresh_demo_setup.py --dry-run
```

---

## Overview

| Phase | What | Outcome |
|-------|------|--------|
| **0** | Prerequisites | DB up, migrations applied, API + worker (if used) running, demo tenant exists |
| **1** | Clean | Remove all source files (optional); truncate/delete raw PostgreSQL tables; delete baselines, predicted impact, observations, and optionally analyses/impact results/data_periods/ingestions for demo tenant |
| **2** | Generate historical source data | 24 months (July 2023–June 2025), 1000 members: claims + enrollment (+ providers) in pipeline-ready format (CSV/Parquet) in a single source folder |
| **3** | Load historical via pipeline | Point pipeline(s) at that folder/files; run Claims + Eligibility (and optionally Provider) pipelines so data lands in `claims_lines`, `enrollment_records`, `provider_records` |
| **4** | Baselines + predicted impact | Run baseline refresh for demo tenant; run predicted impact for all policies (script or API) |
| **5** | Generate observation-period data | Generate claims + enrollment for July 2025–current month; load via same pipeline (append or new run) |
| **6** | Observations per month | For each month from July 2025 to current: run impact analysis (or equivalent) and create one observation per policy (or one per month across policies) |
| **7** | Refresh / verify | Reload Policy Verdicts, Objectives Health, Dashboard; optionally run `run_demo_day.py` to add mixed verdicts if desired |

---

## Step-by-step

### Phase 0: Prerequisites

1. **Database**
   - PostgreSQL running; connection string configured (e.g. `.env` or `apps/api` env).
   - Migrations applied: `cd apps/api && alembic upgrade head`.

2. **App and worker**
   - API server running (e.g. `uvicorn` or `python -m uepi_api.main`).
   - If baseline/impact/observations use async worker (Celery), worker running and connected.

3. **Demo tenant**
   - Tenant exists (e.g. `00000000-0000-0000-0000-000000000001`). If not, run `scripts/dev/seed_demo_data.py` or ensure first API request creates it.

4. **Policies**
   - At least one policy (ideally 3–5) for the demo. Seed or create via API; ensure they have effective dates so “pre” vs “post” is clear (e.g. policy effective July 2025 for observation period).

---

### Phase 1: Clean (remove source data + PostgreSQL raw + derived)

**1.1 – Optional: remove existing source files**

- Decide the **source root** for the new demo (e.g. `data/source_data/00000000-0000-0000-0000-000000000001/historical` or `data/source_data/synthetic`).
- Delete or archive all files under that root so the next steps write the only source data.

**1.2 – Truncate/delete raw (target) tables in PostgreSQL**

Tables that hold “loaded” data:

- `claims_lines` (tenant_id = demo tenant)
- `enrollment_records` (tenant_id = demo tenant)
- `provider_records` (tenant_id = demo tenant)

Options:

- **Option A – Delete by tenant (recommended):**  
  One-time script or SQL:  
  `DELETE FROM claims_lines WHERE tenant_id = '<demo_tenant_uuid>';`  
  Same for `enrollment_records` and `provider_records`.  
  This keeps other tenants intact.

- **Option B – Truncate (full reset):**  
  If only demo tenant exists:  
  `TRUNCATE claims_lines, enrollment_records, provider_records CASCADE;`  
  (Ensure no critical FKs; adjust if your schema has dependencies.)

**1.3 – Delete derived analytics for demo tenant**

So baselines, predicted impact, and observations are recreated from the new data:

- **Baselines:**  
  `DELETE FROM baselines WHERE tenant_id = '<demo_tenant_uuid>';`  
  Or use existing logic (e.g. `scripts/cleanup_db.py` or `storage_baselines.delete_policy_level_baselines` + any global baselines).

- **Predicted impact:**  
  `DELETE FROM policy_predicted_impacts WHERE tenant_id = '<demo_tenant_uuid>';`

- **Observations:**  
  Use existing: `storage_observations.delete_all_observations(tenant_id)` or `DELETE FROM observations WHERE tenant_id = '<demo_tenant_uuid>';`

- **Optional but recommended for a truly fresh demo:**
  - **Analytics runs:**  
    `DELETE FROM analytics_runs WHERE tenant_id = '<demo_tenant_uuid>';`
  - **Analyses:**  
    `DELETE FROM analyses WHERE tenant_id = '<demo_tenant_uuid>';`
  - **Impact analysis results:**  
    `DELETE FROM impact_analysis_results WHERE tenant_id = '<demo_tenant_uuid>';`
  - **Data periods:**  
    `DELETE FROM data_periods WHERE tenant_id = '<demo_tenant_uuid>';`
  - **Ingestions:**  
    `DELETE FROM ingestions WHERE tenant_id = '<demo_tenant_uuid>';`
  - **Pipeline runs:**  
    Optional: delete pipeline_runs for demo tenant so history matches the new load.

Order: delete observations first, then baselines, then predicted_impacts, then analyses / impact_analysis_results / analytics_runs, then data_periods / ingestions (to avoid FK issues if any).

**1.4 – Single cleanup script (recommended)**

- Add or use a script, e.g. `scripts/fresh_demo_clean.py`, that:
  - Takes `--tenant-id` (default demo tenant).
  - Deletes from: `claims_lines`, `enrollment_records`, `provider_records`, then `observations`, `baselines`, `policy_predicted_impacts`, then optionally `analytics_runs`, `impact_analysis_results`, `analyses`, `data_periods`, `ingestions`.
  - Commits in a sensible order (child tables before parent where FKs exist).
  - Prints counts deleted.
- Run once before generating new data:  
  `python3 scripts/fresh_demo_clean.py`

---

### Phase 2: Generate historical source data (24 months, 1000 members)

**2.1 – Time window and scope**

- **Start:** 2023-07-01  
- **End:** 2025-06-30  
- **Members:** 1000 (fixed set of member IDs for reproducibility).  
- **Output:** Pipeline-ready files (CSV or Parquet) that match the pipeline’s expected schema (column names and types for Claims Lines and Eligibility Enrollment; optionally Provider Master).

**2.2 – What to generate**

- **Claims lines:**  
  One file (or one per month) with columns matching the pipeline’s Claims Lines mapping:  
  tenant_id, claim_id, claim_line_id, member_id, provider_id, service_date, paid_date, adjudication_date, lob, market, cpt_code/hcpcs_code/drg_code, icd10_diagnosis_codes, icd10_procedure_codes, service_category, place_of_service, units, allowed_amount, paid_amount, member_cost_share, in_network, requires_prior_auth, prior_auth_approved, prior_auth_id, facility_type, system_affiliation, etc.

- **Eligibility / enrollment:**  
  One file (or one per month) with columns matching the pipeline’s Eligibility Enrollment mapping:  
  tenant_id, member_id, enrollment_month, lob, market, age_band, gender, risk_score, network_tier, enrolled_flag, enrollment_start_date, enrollment_end_date, product_type, segment.

- **Providers (optional):**  
  If the pipeline loads provider master: provider_id, npi, provider_type, specialty, facility_type, market, state, zip_code, network_status, effective_date, termination_date, etc.

**2.3 – Realism**

- Use existing patterns from `apps/api/scripts/generate_comprehensive_realistic_data.py`:  
  service categories (primary care, imaging, specialty, rehab, etc.), LOBs (COMMERCIAL, MA, MEDICAID), markets, and policy-relevant codes (e.g. CPTs that policies reference).
- Spread claims across the 24 months; vary utilization and cost by month/member.
- Keep member set stable (1000 members) with enrollment spanning the 24 months (some churn allowed).

**2.4 – Output location**

- Write to the **source folder** that pipelines will use, e.g.:  
  `data/source_data/00000000-0000-0000-0000-000000000001/historical/`  
  or  
  `data/source_data/synthetic/`  
- Filenames: e.g. `claims_lines_202307_202506.csv`, `eligibility_enrollment_202307_202506.csv` (or one CSV per entity type). Match whatever the pipeline run expects (see Phase 3).

**2.5 – Script**

- New script, e.g. `scripts/generate_24mo_historical_demo_data.py`:
  - Args: `--tenant-id`, `--start 2023-07-01`, `--end 2025-06-30`, `--members 1000`, `--output-dir` (default = source root above).
  - Generates claims, enrollment, and optionally providers; writes CSV (or Parquet) into `--output-dir`.
  - Logs row counts and file paths.
- Run:  
  `python3 scripts/generate_24mo_historical_demo_data.py --output-dir data/source_data/00000000-0000-0000-0000-000000000001/historical`

---

### Phase 3: Load historical data via pipeline

**3.1 – Pipeline connection to source**

- Pipelines run with a **source file or URI** (e.g. upload or `source_uri` like `file:///abs/path/to/file.csv`). The “connection” to the right folder is: **the path you pass at run time** (or the path where you place the file for upload).
- Ensure the pipeline run is configured to write to the **database** (existing `PipelineDatabaseService` / `execute_pipeline_to_database`) and that the pipeline’s **target_dataset_type** and **field_mappings** match the canonical tables (`claims_lines`, `enrollment_records`, `provider_records`).

**3.2 – Which pipelines to run**

- **Claims Lines** pipeline: source = generated claims file(s). If the pipeline expects one file, concatenate monthly claims into one CSV or run once per file and use mode REPLACE for first run then APPEND (or run once with one big file).
- **Eligibility Enrollment** pipeline: source = generated enrollment file(s).
- **Provider Master** (optional): if you generated providers and have a pipeline for it.

**3.3 – Mode**

- For a **fresh** load after truncate: use **REPLACE** (or first run so no existing rows). If the pipeline loads by tenant, REPLACE per tenant is ideal so the new 24-month data is the only data for the demo tenant.

**3.4 – How to run**

- **Option A – API with file upload:**  
  For each pipeline:  
  `POST /api/v1/pipelines/{pipeline_id}/run` with `file=@/abs/path/to/claims_lines_202307_202506.csv` (and similarly for enrollment).  
  Use the pipeline IDs from `GET /api/v1/pipelines` (or your seeded pipeline list).

- **Option B – Script that uses source folder:**  
  Script that:  
  (1) Lists pipeline IDs for Claims and Eligibility (and optionally Provider).  
  (2) Resolves the path to the generated file(s) in the chosen source folder.  
  (3) Calls the run API with `source_uri=file:///abs/path/to/file` **if** the API supports `source_uri` (currently the router may require `file`; in that case script can use curl with `-F file=@...`).  
  So either: extend the router to accept `source_uri` and open the file from disk, or have the script upload the file (e.g. with `requests` and `files={'file': open(path, 'rb')}`).

**3.5 – Verify**

- After run(s):  
  `SELECT COUNT(*) FROM claims_lines WHERE tenant_id = '<demo_tenant>';`  
  Same for `enrollment_records` (and `provider_records`). Counts should match generated rows (or close if dedup is applied).

---

### Phase 4: Baselines and predicted impact

**4.1 – Baselines**

- Trigger **baseline refresh** for the demo tenant so baselines are computed from the newly loaded 24-month data.
- Use existing logic: e.g. `POST /api/v1/baselines/refresh` (with optional policy_id, baseline_type, window_months) or a script that calls `baseline_refresh.refresh_baseline(tenant_id, ...)`.
- Ensure at least one baseline exists (tenant-level or per policy) and that it’s the one used later for predicted impact and observations.

**4.2 – Predicted impact**

- For **all** policies (for the demo tenant), run predicted impact generation and **store** results in the database (`policy_predicted_impacts`).
- Use existing script or API: e.g. `apps/api/scripts/generate_all_predicted_impact_database.py` or the flow that calls the predicted-impact generator and `storage_policy_predicted_impact.store_predicted_impact`.
- Confirm: `GET /api/v1/policy-verdicts` or DB query shows each policy has a row in `policy_predicted_impacts`.

---

### Phase 5: Generate observation-period data (July 2025–present)

**5.1 – Time window**

- Start: 2025-07-01  
- End: current month (or last full month).

**5.2 – Same 1000 members**

- Generate claims and enrollment for the **same** 1000 members for each month in this range. Optionally introduce small policy-effect patterns (e.g. slight utilization/cost change after a “policy effective” date) so observations are meaningful.

**5.3 – Output and load**

- Write to the **same** source folder (or a subfolder, e.g. `daily/` or `observation_period/`) in the same format as Phase 2.
- Load via the **same** pipelines (Claims + Eligibility). Use **APPEND** (or equivalent) so the new rows are added to `claims_lines` and `enrollment_records` without removing the 24-month historical data.

**5.4 – Script**

- Either extend `scripts/generate_24mo_historical_demo_data.py` with a mode like `--period observation --start 2025-07-01 --end 2025-12-31` (and run again for 2026), or add a small script `scripts/generate_observation_period_demo_data.py` that generates July 2025–present and appends/writes files, then run pipeline(s) again.

---

### Phase 6: One observation per month (July 2025–present)

**6.1 – Per month**

- For each month from July 2025 to current (or last complete month):
  - Run **impact analysis** for the demo tenant and for each policy (or the set of policies you care about), using that month’s data as the “post” period (and previous months or the 24-month baseline window as “pre” if needed).
  - From each completed impact analysis, **create one observation** (e.g. via `create_observation_from_analysis` or the flow used by `daily_demo_workflow`).

**6.2 – How to run**

- **Option A – Daily demo workflow in a loop:**  
  For each month M (e.g. 2025-07, 2025-08, …):  
  - Call or run `daily_demo_workflow.run_daily_demo_workflow(tenant_id, target_date=last_day_of(M), generate_data=False, run_observations=True)` so it only runs impact and creates observations (no new data generation if data is already loaded).

- **Option B – Dedicated script:**  
  Script that, for each month:  
  (1) Determines the analysis period (e.g. that month as post).  
  (2) Triggers or runs impact analysis for each policy.  
  (3) Waits for completion (if async).  
  (4) Creates one observation per policy from the impact result.  
  This can wrap existing `create_observation_from_analysis` and the analysis trigger (worker or sync).

**6.3 – Policies**

- Use the same policies that have baselines and predicted impact. Result: one observation per (policy, month) for July 2025–present, so Policy Verdicts and Objectives Health show a time series.

---

### Phase 7: Refresh dashboards, Objectives Health, Policy Verdicts

**7.1 – No extra backend “refresh”**

- Dashboards, Objectives Health, and Policy Verdicts read from DB (observations, baselines, policies, predicted impact). Once Phase 1–6 are done, a **browser reload** (or reopening the app) is enough.

**7.2 – What to verify**

- **Policy Verdicts** (`/policy-verdicts`):  
  One row per policy; verdict (On track / At risk / Backfire risk) and latest observation; “View evidence” works.

- **Objectives Health** (`/objectives-health`):  
  Objectives and policy coverage show the new observations and any early-warning/backfire signals.

- **Dashboard** (`/`):  
  Summary counts and charts reflect new baselines and observations.

- **Observation Analysis** (`/observation-analysis`):  
  List shows observations by month; opening one shows verdict and “Download evidence pack.”

**7.3 – Optional: mixed verdicts for demo story**

- If you want a few “At risk” or “Backfire” examples for the demo, run:  
  `python3 scripts/run_demo_day.py --skip-seed`  
  This adds more observations with controlled verdicts (optional; can skip if the per-month observations already give a good story).

---

## Order of operations (concise)

1. Prerequisites: DB, migrations, API (and worker), demo tenant, policies.
2. **Clean:** Run `scripts/fresh_demo_clean.py` (or equivalent): raw tables + baselines + predicted impact + observations + (optional) analyses, impact results, data_periods, ingestions.
3. **Generate historical:** Run `scripts/generate_24mo_historical_demo_data.py` → 24 months, 1000 members, into source folder.
4. **Load historical:** Run Claims + Eligibility (and optionally Provider) pipelines with source pointing to that folder/files → DB has only the new 24-month data for demo tenant.
5. **Baselines:** Run baseline refresh for demo tenant.
6. **Predicted impact:** Run predicted impact for all policies; store in DB.
7. **Generate observation period:** Generate July 2025–present for same 1000 members; write to same (or designated) source folder.
8. **Load observation period:** Run same pipelines in APPEND mode (or equivalent).
9. **Observations per month:** For each month July 2025–present, run impact + create observation per policy (script or daily_demo_workflow with `generate_data=False`).
10. **Verify:** Policy Verdicts, Objectives Health, Dashboard, Observation Analysis; optional `run_demo_day.py --skip-seed` for mixed verdicts.

---

## Files and scripts to add or reuse

| Item | Action |
|------|--------|
| `scripts/fresh_demo_clean.py` | **Add:** Delete raw tables (by tenant) + baselines + predicted impact + observations + optional analyses/impact_results/analytics_runs/data_periods/ingestions. |
| `scripts/generate_24mo_historical_demo_data.py` | **Add:** Generate 24 months (July 2023–June 2025), 1000 members, claims + enrollment (+ providers); output to configurable source dir. |
| `scripts/generate_observation_period_demo_data.py` or mode in above | **Add (or extend):** Generate July 2025–present; same format; append or separate files. |
| Pipeline run with source folder | **Reuse** `run_all_pipelines_from_source.py`-style logic; fix or use file upload so generated files are used (source_uri or `-F file=@...`). |
| Baseline refresh | **Reuse** existing refresh API or `baseline_refresh.refresh_baseline`. |
| Predicted impact | **Reuse** `generate_all_predicted_impact_database.py` or equivalent. |
| Observations per month | **Reuse** `daily_demo_workflow` with `generate_data=False` in a loop, or **add** a small script that loops over months and calls create_observation_from_analysis. |

---

## Risks and mitigations

- **Pipeline expects different schema:** Match column names and types in generated CSVs to the pipeline’s field_mappings and target_dataset_type (canonical schema).  
- **Run order / FKs:** Clean in order: observations → baselines → policy_predicted_impacts → impact_analysis_results → analyses → analytics_runs → data_periods / ingestions; then raw tables.  
- **Worker vs sync:** If impact analysis is async, the “observations per month” step must wait for job completion (poll or use synchronous path for demo).  
- **Large 24-month file:** If one big CSV is too large, generate per-year or per-quarter and run pipeline multiple times (APPEND after first REPLACE).

---

## Summary

- **Clean:** Remove all source data (optional), clear PostgreSQL raw tables and all derived analytics for the demo tenant.
- **Historical:** Generate 24 months (July 2023–June 2025), 1000 members, pipeline-ready files; load via pipeline into `claims_lines` / `enrollment_records` (and optionally `provider_records`).
- **Baselines + predicted impact:** Refresh baselines; generate and store predicted impact for all policies.
- **Observation period:** Generate July 2025–present; load via pipeline (append); then create one observation per month per policy.
- **Refresh:** Reload Policy Verdicts, Objectives Health, and Dashboard in the UI; optionally run `run_demo_day.py --skip-seed` for a stronger demo narrative.

This gives you a single, repeatable path to a fresh demo with consistent 24-month history, clear observation timeline, and all dashboards aligned to the new data.
