# Why Analysis Keeps Running and How to Check for Errors

## What the status means

| Status     | Meaning |
|-----------|--------|
| **PENDING** | Analysis was created; the **Celery worker has not picked up the job** yet. It will stay PENDING until the worker runs and processes the queue. |
| **RUNNING** | The worker picked up the job and is running it. If it stays RUNNING for a long time, the worker may have crashed or the job may be very slow (e.g. loading a lot of data). |
| **COMPLETED** | The job finished; results are available. |
| **FAILED**   | The job failed. Check **error_message** on the analysis (if present) or the **worker logs** for the reason. |

## Why it “keeps running” (never completes)

1. **Worker not running**  
   Analyses are created with status PENDING. The API only enqueues the job (e.g. `whatif_scenario_job.delay(...)`). The **Celery worker** must be running to process the queue. If the worker is not running, analyses stay **PENDING** and never move to RUNNING or COMPLETED.

   **Fix:** Start the worker in a separate terminal:
   ```bash
   ./start_api_and_worker.sh worker
   ```
   (Redis must be running: `brew services start redis` or `redis-server`.)

2. **Worker died mid-job**  
   If the worker started the job (status became RUNNING) but then crashed or was killed, the status may stay **RUNNING** and never update to FAILED or COMPLETED.

   **Fix:** Restart the worker. For stuck analyses you can re-run a new analysis or (if you add an endpoint) mark the old one as FAILED.

3. **Job is slow or stuck**  
   The job might be loading a lot of data (e.g. from S3) or waiting on something. Check the **worker terminal** for progress or errors.

## How to check for errors

1. **Worker terminal**  
   When you run `./start_api_and_worker.sh worker`, errors and tracebacks are printed there. Look for `Task ... failed:` or Python tracebacks after a run.

2. **API: get analysis**  
   For a given analysis ID, call:
   ```bash
   curl -s http://localhost:8000/api/v1/analyses/<analysis_id>
   ```
   If the analysis has **status: "FAILED"** and an **error_message** field, that message describes the failure.

3. **Frontend**  
   On the What-If (or other analysis) page, if the run fails you should see an error alert. If the analysis is FAILED, the UI can show `analysis.error_message` when the API returns it.

## Quick checklist

- [ ] **API** is running: `./restart_api_now.sh` or `./start_api_and_worker.sh api`
- [ ] **Redis** is running: `redis-cli ping` → `PONG`
- [ ] **Celery worker** is running: `./start_api_and_worker.sh worker`
- [ ] Check **worker terminal** for tracebacks when an analysis fails or stays RUNNING

## Seeing the failure reason in the UI

The API returns **error_message** for analyses with status FAILED (the worker stores it when a job fails). The frontend shows that message when present. To enable this, add the `error_message` column (one-time): run `cd apps/api && alembic upgrade head`. Then the frontend can show “Scenario simulation failed: &lt;error_message&gt;” instead of a generic message. Ensure the worker is running so jobs are processed and failures are recorded.
