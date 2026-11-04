# Production Performance & Readiness Backlog

**Status:** Living backlog  
**Audience:** Engineering / architecture  
**Last updated:** 2026-10-31  

## Scope

### In scope (this backlog)
Interactive and always-on product paths that must stay fast for many concurrent users (e.g. BCBS NC–class):

- Thin API reads (lists, detail, dashboards, what-if **start/poll/result**)
- Database shape for interactive queries (indexes, partitions, rollups, pooling)
- App / API / worker **capacity** (not job algorithm redesign)
- Frontend payload hygiene and catalog-scale UX (filters already started)
- Caching, read scaling, observability, SLOs, resilience
- Security/perf hygiene that affects load (logging, timeouts, connection limits)

### Out of scope (already decided — backend jobs, not interactive API)
Track separately as **Batch / Worker** epics (do not reopen as “make API do this faster”):

| Workload | Cadence | Runtime |
|----------|---------|---------|
| Data ingestion / ETL bulk loads | Continuous / nightly | Pipeline → DB |
| Bulk baseline generation / refresh | Rare / on schedule | Workers |
| Bulk predicted-impact generation | Rare / on schedule | Workers |
| Nightly (or weekly/monthly) policy observations | Scheduled | Workers |

**Principle:** Interactive path only **reads prepared results**. Heavy compute is always enqueue → worker → store → UI reads.

---

## Target SLOs (production)

| Surface | Target (p95) | Notes |
|---------|--------------|--------|
| Auth + shell load (`/auth/me`, permissions) | &lt; 1–2s | Warm path |
| Policy / observation / baseline **lists** (summary) | &lt; 2–3s | Summary projections only |
| Single-policy detail / history | &lt; 2–5s | Scoped query |
| Dashboard / executive summary | &lt; 2–3s | **From rollups**, not live claim scans |
| What-if **submit** | &lt; 1s | Returns `job_id` / analysis id |
| What-if **result poll** while running | &lt; 500ms | Status only |
| What-if **open completed result** | &lt; 2–3s | Read stored results |
| Concurrent interactive users | Plan for tens–hundreds | Scale API independently of workers |

---

## Architecture guardrails (non-negotiable)

1. **No claim-line dumps through the API** for UI grids or dashboards.  
2. **No N+1 claim-count storms** on page load (lazy / cached / rollup only).  
3. **List endpoints default to `summary`** (scalars); full JSONB on detail/`id` fetch.  
4. **What-if / elasticity / any multi-minute compute** → Celery (or equivalent), never App Service request thread as the only path.  
5. **Dashboards** → precomputed rollup tables refreshed by night jobs (or incremental).  
6. **Scale API for readers; scale workers for jobs** — separate knobs.  
7. **Postgres first** (partitioned claims); warehouse only if claims ops force it.

---

## Epic backlog

Priorities: **P0** = production blocker / BCBS readiness · **P1** = high ROI soon after · **P2** = scale hardening · **P3** = polish / optional.

Effort: **S** (&lt;1w) · **M** (1–2w) · **L** (2–4w) · **XL** (multi-sprint).

---

### EPIC-A — Interactive API contracts (thin reads)

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-A1 | Standardize `summary=true` (or dedicated `/summary` list DTOs) on policies, observations, baselines, analyses | P0 | M | Default list responses omit heavy JSONB; detail routes return full; OpenAPI documented |
| PERF-A2 | Push all `latest_only` / “latest per policy” into SQL (`DISTINCT ON` / window), never “fetch 500 then filter in Python” | P0 | S | Verified in EXPLAIN; unit/integration coverage |
| PERF-A3 | Policy dropdown APIs: `include_metadata=false` (id/name/type/status only) | P0 | S | Catalog selects &lt; ~50–100KB for 250 policies |
| PERF-A4 | Eliminate remaining N+1 on UI boot (predicted-impact refresh status fan-out on Policy Catalog, etc.) | P0 | M | No per-policy sequential GETs on catalog load; batch or omit |
| PERF-A5 | Paginate all unbounded list endpoints (`skip`/`limit` or cursor); hard caps documented | P0 | M | No “return all baselines/analyses” without limit |
| PERF-A6 | What-if claim-counts: cache or materialize; never block first paint | P1 | S | Tip endpoint &lt; 2s or served from cache/rollup |

---

### EPIC-B — Dashboard & portfolio rollups

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-B1 | Design `dashboard_rollups` / `policy_performance_rollups` tables (tenant, as_of, metrics JSON scalars) | P0 | M | Schema + migration; written by worker job |
| PERF-B2 | Nightly (or post-observation) job refreshes rollups — **out of interactive API** but required for dashboards | P0 | M | Job idempotent; dashboard reads rollups only |
| PERF-B3 | Rewrite `GET /dashboard/summary` and `GET /dashboard/policy-performance` to read rollups | P0 | M | p95 &lt; 3s with production-like claim volume; no full claims DISTINCT on request |
| PERF-B4 | Persona dashboards (Executive / Policy Owner / etc.) use same rollup APIs | P1 | S | No duplicate live aggregation logic |
| PERF-B5 | Objectives / Verdicts portfolio views: optional rollup or summary observation index | P1 | M | Page load independent of raw claims |

---

### EPIC-C — On-demand compute (What-If / elasticity) — async only

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-C1 | Production default: `USE_CELERY_FOR_WHATIF_SIMULATION=true` (and elasticity) | P0 | S | Flags on in prod config; API BackgroundTasks only as local fallback |
| PERF-C2 | Guaranteed worker pool + Redis HA for queue; dead-letter / failed job visibility in UI | P0 | M | Failed what-if shows error; ops can see queue depth |
| PERF-C3 | What-if result payload slim on list; full charts on open-by-id | P1 | S | Scenario history list stays fast at 500 runs |
| PERF-C4 | Idempotency keys / debounce duplicate submits | P2 | S | Double-click doesn’t spawn duplicate heavy jobs |
| PERF-C5 | Progress events (Redis pub/sub or poll fields) for long what-ifs | P2 | M | UI % or stage without blocking |

---

### EPIC-D — Database (interactive path)

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-D1 | Keep/extend composite indexes: claims `(tenant_id, service_date)`; obs `(tenant_id, policy_id, period_end, computed_at)`; baselines `(tenant_id, policy_id, computed_at)` | P0 | S | Migrations CONCURRENTLY; EXPLAIN uses indexes |
| PERF-D2 | **Partition `claims_lines` by month** (`service_date`) | P0 | L | Partition pruning on date-window queries; runbook for attach/detach |
| PERF-D3 | Connection pooling (PgBouncer or Azure equivalent) + sane SQLAlchemy pool sizes per API instance | P0 | M | No connection storms at 2–N App Service instances |
| PERF-D4 | Statement timeouts: short for interactive routes; long only inside worker jobs | P0 | S | Interactive routes cannot hold 300s locks |
| PERF-D5 | Azure Postgres Flexible Server sizing playbook (SKU, IOPS, storage) for BCBS claim volumes | P0 | M | Documented target SKU + alert thresholds |
| PERF-D6 | Read replica for Voyager/dashboard **read** traffic (optional after rollups) | P1 | L | Replica lag monitored; writes stay primary |
| PERF-D7 | Autovacuum / bloat / index health monitoring | P1 | S | Alerts on dead tuples / wraparound risk |
| PERF-D8 | Evaluate warehouse (Fabric/Synapse/Snowflake) **only if** partitioned Postgres + rollups insufficient | P3 | XL | Decision record with cost/ops criteria |

---

### EPIC-E — Caching

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-E1 | Redis cache for tenant policy list summary (TTL + invalidate on policy write) | P1 | M | Cache hit rate measurable; stale &lt; TTL |
| PERF-E2 | Cache dashboard rollup responses briefly (30–120s) for stampede protection | P1 | S | Concurrent dashboard opens share one DB hit |
| PERF-E3 | HTTP cache headers where safe (public marketing only; authenticated APIs default no-store) | P2 | S | No leaking tenant data via shared caches |

---

### EPIC-F — Frontend production readiness

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-F1 | All catalog-scale grids use shared `ListFilterBar` / `PolicyAutocomplete` (extend MEDIUM pages: Decisions, Scorecards, Predicted Impacts polish, Ingestion, Exports) | P1 | M | No plain 200+ item Select left on core paths |
| PERF-F2 | Enforce summary list + detail-on-select everywhere (Obs cards, Baseline detail already started) | P0 | M | Network tab: first paint payloads bounded |
| PERF-F3 | Remove remaining secret/body logging; keep prod API logs minimal (done partially — audit) | P0 | S | No passwords/tokens in console or `uepi_logs` |
| PERF-F4 | Route-based code splitting for heavy analysis pages | P2 | M | Initial JS chunk reduced |
| PERF-F5 | Virtualize very long tables (react-window) if &gt; ~200 visible rows | P2 | M | Scroll stays smooth |
| PERF-F6 | AbortController / cancel in-flight list requests on navigation | P2 | S | No stale overwrite races |

---

### EPIC-G — Capacity & Azure topology

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-G1 | Separate scale rules: API App Service vs Worker vs Web | P0 | M | Docs + autoscale rules; workers never starve API CPU |
| PERF-G2 | Always On + health/warmup paths; multi-instance sticky-session policy documented | P0 | S | Cold-start mitigated |
| PERF-G3 | Redis (premium/HA) as Celery broker + cache | P0 | M | Failover tested |
| PERF-G4 | CDN for static web assets (optional) | P2 | S | Cache-busting via hashed bundles (already) |
| PERF-G5 | Region / DR RPO-RTO for Postgres (geo-backup / replica) | P1 | L | Runbook exists |

---

### EPIC-H — Observability & SLOs

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-H1 | Structured API timing metrics per route (p50/p95/p99) | P0 | M | Dashboard in App Insights / Grafana |
| PERF-H2 | Slow-query log + top offenders weekly review | P0 | S | Claims/obs queries tagged |
| PERF-H3 | Synthetic checks: login → dashboard → obs list → what-if history | P1 | M | Alert if SLO breached |
| PERF-H4 | Queue depth / worker lag alerts (for on-demand what-if) | P0 | S | Page if queue &gt; N for M minutes |
| PERF-H5 | Error budget / capacity review cadence | P2 | S | Monthly checklist |

---

### EPIC-I — Resilience & correctness under load

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-I1 | Rate limits on expensive interactive endpoints (per tenant/user) | P1 | M | Fair use; 429 with Retry-After |
| PERF-I2 | Bulkheads: interactive DB role vs worker DB role (different timeouts/pools) | P1 | L | Worker can’t exhaust interactive pool |
| PERF-I3 | Graceful degradation: dashboard returns last good rollup if refresh late | P1 | S | Stale banner, not 90s hang |
| PERF-I4 | Load test plan (k6/Locust): 50–200 concurrent readers + mixed what-if submits | P0 | M | Report vs SLOs before BCBS go-live |
| PERF-I5 | Chaos: kill one API instance / one worker during demo rehearsal | P2 | S | No data corruption; UI recovers |

---

### EPIC-J — Security / compliance that affects performance posture

| ID | Item | Pri | Effort | Acceptance criteria |
|----|------|-----|--------|---------------------|
| PERF-J1 | Secrets never in browser logs (audit complete) | P0 | S | Automated grep in CI |
| PERF-J2 | Tenant isolation verified on all summary/rollup queries (`tenant_id` forced) | P0 | M | Tests for cross-tenant leakage |
| PERF-J3 | PHI minimization in list APIs (no member-level in portfolio grids) | P0 | M | Contract review signed off |

---

## Suggested delivery waves

### Wave 1 — Stabilize interactive path (before large-tenant pilot)
PERF-A1–A5, PERF-B1–B3, PERF-C1–C2, PERF-D1–D5, PERF-F2–F3, PERF-G1–G3, PERF-H1–H2, PERF-H4, PERF-I4  

### Wave 2 — Scale & polish
PERF-A6, PERF-B4–B5, PERF-C3–C5, PERF-D6–D7, PERF-E1–E2, PERF-F1, PERF-F4–F6, PERF-I1–I3  

### Wave 3 — Enterprise hardening
PERF-D8 (if needed), PERF-G4–G5, PERF-H3–H5, PERF-I5, PERF-J\* residual  

---

## Explicit non-goals (do not put on interactive backlog)

- “Speed up bulk baseline / predicted impact / nightly observation **via API**”
- Loading millions of claim rows into the browser
- Using App Service scale-out as a substitute for rollups or partitions
- Premature multi-region active-active without rollup + queue maturity

---

## Tracking

- **Source of truth (repo):** this file — `docs/PRODUCTION_PERFORMANCE_BACKLOG.md`  
- **Issue tracker:** when GitHub/Linear is connected, create one issue per `PERF-*` ID; link epic labels `perf-interactive`, `perf-db`, `perf-whatif-async`, `perf-frontend`, `perf-obs`.  
- **Batch/worker jobs** (ETL, bulk baseline, bulk predicted, nightly obs): maintain a separate backlog file or epic `BATCH-*` so ownership stays clear.

---

## Done-when (program exit criteria)

1. Interactive SLOs met under load test with production-like claim volume.  
2. Dashboard never scans raw claims on request.  
3. What-if always async in production; workers healthy.  
4. Claims partitioned; indexes + pooling in place.  
5. Catalog-scale UX (filters + summary lists) on all HIGH/MEDIUM grids.  
6. Observability + runbooks signed off for on-call.
