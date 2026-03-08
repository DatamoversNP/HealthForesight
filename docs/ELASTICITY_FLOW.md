# Elasticity Analysis – End-to-End Flow

This doc describes how elasticity analysis is traced and made fully functional.

## Flow (API → Worker → DB → API → Frontend)

1. **Frontend** – User clicks "Create Elasticity Analysis" on What-If page (Elasticity Curves tab).  
   `POST /analyses/elasticity` with `{ policy_id }`.

2. **API** – Creates an `Analysis` (type `ELASTICITY`), enqueues Celery task  
   `uepi_worker.tasks.elasticity_job(tenant_id, analysis_id, policy_id, service_categories=None)`.

3. **Worker** – `elasticity_job`:
   - Sets analysis status to `RUNNING`.
   - Uses `ElasticityModeler` (common) to compute elasticity (default categories e.g. `ALL` when no historical data).
   - Builds `result_dict` with `policy_id`, `service_categories`, `overall_elasticity`, `model_quality`, `warnings`, `created_at`.
   - **Saves to DB first**: inserts/updates `ElasticityAnalysisResult` with `result_data_json = result_dict`. This makes GET results work even when object storage is down.
   - Optionally uploads JSON to object storage and creates `AnalysisResultIndex` (backward compatibility). If S3/MinIO fails, job still completes and results are served from DB.
   - Sets analysis status to `COMPLETED`.

4. **API** – `GET /analyses/{id}/results?result_type=ELASTICITY`:
   - Loads from DB: `ElasticityAnalysisResult` for this analysis → `results["ELASTICITY"] = result_data_json`.
   - If no DB row, falls back to `AnalysisResultIndex` + object storage. URI is parsed as either `s3://bucket/key` or `bucket/key`.

5. **Frontend** – `loadElasticityData(policyId)` finds the elasticity analysis for the policy, calls `getAnalysisResults(id, 'ELASTICITY')`, then sets `elasticityData` from `results.results.ELASTICITY` (or `results.service_categories` / first key).  
   After "Create Elasticity Analysis", polling uses the same logic and shows curves when `payload.service_categories` is present.

## Changes Made

- **DB** – New table `elasticity_analysis_results` and model `ElasticityAnalysisResult` (like `WhatIfScenarioResult`). Migration: `004_add_elasticity_analysis_results.py`.
- **API** – `get_analysis_results` now:
  - Reads ELASTICITY from `ElasticityAnalysisResult` first.
  - Parses object-storage URI as `bucket/key` when not `s3://bucket/key`.
- **Worker** – `elasticity_job` writes to `ElasticityAnalysisResult` first, then optionally to S3; S3 failure no longer fails the job.
- **Frontend** – Create-flow polling uses `payload?.service_categories` and shows `analysis.error_message` when status is FAILED.

## Deploy Steps

1. **Run migration** (from `apps/api`):
   ```bash
   alembic upgrade head
   ```
   This creates `elasticity_analysis_results` if it does not exist.

2. **Restart API and Celery worker** so they load the new model and routes.

3. **Create Elasticity Analysis** from the What-If page (select policy → Elasticity Curves tab → "Create Elasticity Analysis"). Wait for completion; curves should appear. If the job fails, the UI shows the analysis `error_message`.

## Optional: Object Storage

Elasticity results are **not** required to be in object storage. If MinIO/S3 is unavailable, the worker still completes and stores results in the DB; the API serves them from `ElasticityAnalysisResult`.
