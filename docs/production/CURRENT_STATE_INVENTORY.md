# Current-State Architecture Inventory (Wave 0)

**Generated:** 2026-11-04  
**Rule:** Evidence from repository and live demo stack only — not aspirational docs.

## Services and processes (demo7867)

| Component | Evidence | Notes |
|-----------|----------|-------|
| API | `apps/api` FastAPI / uvicorn `:7867` | Also deployed historically as **Azure App Service** Linux container (`scripts/azure/deploy-api-docker.sh`) |
| Web | `apps/web` Vite `:7868` | Azure Static Web App / App Service paths in scripts |
| Worker | `apps/worker` Celery | Live: **2× threads concurrency=2**; prefork broken on Python 3.14/billiard |
| Broker | Redis `uepi-demo-redis` `:7870` | Also Azure Cache for Redis in prod scripts |
| OLTP + claims | Azure PostgreSQL Flexible (`healthforesight-db…`) | **Same DB** holds policies metadata **and** `claims_lines` (~3.51M rows) |
| Object storage | MinIO locally; Azure Blob optional | `OBJECT_STORAGE_*` in env examples |

## Runtime / process model

- Monolith-ish modular apps: `api`, `web`, `worker`, `packages/common`.
- Celery tasks in `uepi_worker.tasks` (ingest, impact, what-if, exports, **policy_analytics_***).
- Queues configured: `celery`, `policy_analytics`, `interactive` (`celery_app.py`).
- Isolation for analytics cancel: `uepi_worker.isolated_analytics` (subprocess + `pg_terminate_backend`).
- Durable outbox (new): `analytical_jobs` + `job_outbox` (migration `013`).

## Database topology

- SQLAlchemy engine with pool_size≈5, max_overflow≈10, `pool_pre_ping`, statement_timeout via `PG_STATEMENT_TIMEOUT_MS`.
- Claims analytics via `CanonicalDataRepository.count_claims_for_filters` / aggregates on `claims_lines`.
- **Bottleneck:** interactive API and batch analytics share one PostgreSQL.

## Deployment / release (actual)

| Path | Exists? | Notes |
|------|---------|-------|
| Docker Compose (pg/redis/minio) | Yes | Local deps only |
| Helm chart `infra/helm/uepi` | Yes | **AKS-oriented** (HPA api/worker) — **deferred** for first enterprise per ADR |
| Terraform `envs/azure` | Stub (`main.tf` empty / 1 byte) | Not a working landing zone |
| Terraform modules postgres/redis/object_storage | Partial | Legacy |
| App Service shell scripts | Many under `scripts/azure/` | Current production-like path |
| GitHub Actions `ci.yml` / `ci-cd.yml` | Yes | Need alignment to Container Apps target |
| Enterprise Terraform (Container Apps, Service Bus, ADLS, PG HA) | **Added** `infra/terraform/modules/enterprise/*` | `enable_provision=false` default |

## Analytics / data

- No ADLS/Delta/Databricks in runtime code paths today.
- Results often JSON in PostgreSQL (`BaselineAnalysisResult`, etc.) — **violates future enterprise storage rule** for large claims; small result indices OK.
- 289-policy program: preflight matrix + job evidence under `docs/demo/bcbs-nc/evidence/policy_289/`.

## Security / network (demo)

- Demo uses public localhost + Azure PG with SSL.
- Key Vault scripts exist (`fix-keyvault-permissions.sh`, `setup-secrets.sh`) — not yet Private Link / Front Door standard.
- Auth: JWT + email login paths; Entra setup script present (`setup-azure-ad.sh`) — not full enterprise federation.

## Failure behavior (measured)

- Solo Celery retired for batch; multi-worker threads + isolated cancel **PASS** (hardening report).
- Shared PG → **FAIL** storage scalability enterprise claim.
- Broker/DB HA failover **not** tested end-to-end.

## Explicit non-claims

- Not enterprise production-ready.
- Not billion-row ready.
- Helm/AKS not selected for first customer (deferred).
