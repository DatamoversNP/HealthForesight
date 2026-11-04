# Enterprise Execution Hardening Report

Generated: 2026-11-04T14:56:50.995845+00:00

**Enterprise HA claim: NO** · **Billion-row scalability claim: NO**

## 1. Deployment / worker topology
- API: `uvicorn :7867 (separate process)`
- Broker: `redis://127.0.0.1:7870 (docker uepi-demo-redis)`
- Workers restored: `2 × threads concurrency=2; queues policy_analytics,celery,interactive`
- DB host: `healthforesight-db.postgres.database.azure.com` claims_lines≈3505919
- Shared OLTP+analytics PG: **YES** (demo)

## 2. Concurrency benchmarks
- c=1: completed=8/8 jpm=53.14 job_p95=0.442s api_p95=0.918ms workers=1
- c=2: completed=2/8 jpm=118.74 job_p95=0.433s api_p95=0.957ms workers=2
- c=4: completed=8/8 jpm=247.41 job_p95=0.434s api_p95=1.26ms workers=2
- c=8: completed=8/8 jpm=329.16 job_p95=0.441s api_p95=1.213ms workers=2

## 3. Crash / cancellation
- Hard cancel PASS=True status=TIMEOUT
- Crash recovery PASS=True acks_late=True reject_on_lost=True

## 4. DB contention
- {"total": 29, "active": 1, "waiting": 28}
- Mitigation: SET application_name + statement_timeout on analytics connections; separate Celery queues; rate_limit 30/m on lifecycle jobs. Not a separate analytical warehouse yet.

## 5. API latency
- Baseline p95=0.925ms
- Final p95=4.903ms errors=0

## 6. Idempotency
- PASS=True statuses=['DUPLICATE_PREVENTED', 'PROVENANCE_COMPLETED', 'WAIT_ERROR', 'DUPLICATE_PREVENTED']

## 7. SPOFs
- Single Redis broker (uepi-demo-redis) — no Redis Sentinel/Cluster
- Single Azure PostgreSQL for API metadata AND claims analytics
- Local demo workers on one Mac host — no multi-AZ worker pool
- Celery result backend colocated on same Redis

## 8. Prioritized fixes
- [P0] Multi-worker topology (threads on Py3.14 demo; prefork on Linux prod); retire solo-only batch path — IMPLEMENTED
- [P0] Process isolation + pg_terminate_backend for analytical cancel — IMPLEMENTED
- [P0] task_acks_late + task_reject_on_worker_lost + celery_app circular-import fix — IMPLEMENTED
- [P0] Fix Celery prefork/billiard on Python 3.14 (or standardize workers on 3.11/3.12 Linux) — WORKAROUND_THREADS
- [P1] Read-replica / aggregate extract for claims scans — DOCUMENTED
- [P1] Broker HA (Redis Sentinel) + multi-host workers — NOT_STARTED
- [P1] Formal load test at 3.5M+ claims with connection pooling budgets — PARTIAL_BOUNDED

## 9. Target production topology
- **api**: Independent App Service / containers; no batch analytics in request path
- **workers**: ≥2 hosts, prefork concurrency sized to DB pool; queues: interactive + policy_analytics
- **broker**: Redis Sentinel or managed Redis HA
- **oltp**: PostgreSQL for policies/metadata/results indices
- **analytical**: Read replica or warehouse extracts for cohort/COUNT; columnar later if justified
- **cancellation**: Child process + statement_timeout + pg_terminate_backend (not revoke alone)

## 10. Acceptance criteria
- **PASS** `P0_concurrent_worker_execution` — Multiple jobs complete; ≥2 hostnames at concurrency≥4
- **PASS** `P0_hard_cancellation` — Timed-out jobs stop underlying DB/compute (process kill + pg_terminate)
- **PASS** `P0_worker_crash_recovery` — In-flight failures retry / dead-letter; reject_on_worker_lost enabled
- **PASS** `P0_durable_idempotency` — Concurrent duplicate submissions → one authoritative persisted result
- **PASS** `P0_api_isolation` — API p95 < 2s and zero errors during bounded load
- **PASS** `P1_queue_backpressure` — task_annotations rate_limit 30/m lifecycle, 120/m probe; prefetch=1
- **PASS** `P1_resource_isolation` — Queues policy_analytics vs interactive configured; API process separate
- **FAIL** `P1_storage_scalability` — FAIL as enterprise claim: analytics still on shared Azure PostgreSQL (healthforesight-db.postgres.database.azure.com). Short-term mitigations applied; warehouse path documented.
- **PASS** `P1_load_benchmarks` — Bounded concurrency benchmarks captured (not billion-row)
- **FAIL** `P1_ha_recovery` — FAIL: broker/DB failover not exercised in this bounded demo environment

## Status reconciliation (48 vs 22, 267 vs 241)
- Blocked pathways: 48
- Directional fails: 22
- Intersection: 22
- Directional PASS: 267 · DEMO_READY PASS: 241
- Gap explanation: DEMO_READY requires directional PASS plus a non-BLOCKED evidence pathway. The gap is primarily directionally accurate policies still classified BLOCKED for mechanism execution.

Full reconciliation: `POLICY_289_STATUS_RECONCILIATION.json`
