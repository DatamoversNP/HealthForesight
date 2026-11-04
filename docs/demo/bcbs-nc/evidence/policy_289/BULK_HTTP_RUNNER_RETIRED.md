# Bulk HTTP lifecycle runner — RETIRED

**Effective:** 2026-11-04

`execute_lifecycle_batch.py` is **no longer the primary bulk execution path**.

## Why
Synchronous Cursor → localhost HTTP → baseline/predict/observe does not provide:
- claim/mechanism preflight
- job isolation / killable DB work
- idempotent resume
- separation of empirical vs synthetic vs provenance vs blocked

## Replacement
1. `run_claims_mechanism_preflight.py` — feasibility matrix (Lane B gate)
2. `policy_analytics_job_runner.py` — isolated workers / Celery enqueue
3. Celery task `uepi_worker.tasks.policy_analytics_lifecycle_job` when broker available

Interactive single-policy API endpoints remain for UI workflows.
Frozen Dec4 MRI/MPPR/SOS verify path is unchanged.
