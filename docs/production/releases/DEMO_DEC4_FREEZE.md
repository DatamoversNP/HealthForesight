# December 4 Demo Freeze

**Frozen at:** 2026-11-04T15:40:00Z (approx)  
**Priority:** Highest invariant — no schema activation of enterprise outbox/scheduler on this DB.

## Known-good Git baseline (last committed)

| Field | Value |
|-------|-------|
| Branch | `main` |
| Commit | `d74bd7262b3dda967f0b199604f2448321a64c12` |
| Message | Enable Dec-2025 baselines and 2026 observation seeding for the catalog demo |
| Remote | `origin/main` (working tree has **additional uncommitted** demo + enterprise work) |

## Live demo process baseline (local demo7867)

| Process | Evidence |
|---------|----------|
| API | uvicorn `:7867` — health `healthy` |
| Web | vite demo7867 `:7868` — HTTP 200 |
| Workers | 2× Celery threads (`harden0/1`) — enterprise probe tasks loaded; **not** Celery Beat |
| Broker | Redis `127.0.0.1:7870` |
| Database | Azure PG via `.env.demo7867` |

## Database freeze

| Item | Status |
|------|--------|
| `alembic_version` | **`012_policy_source_inventory`** |
| `analytical_jobs` / `job_outbox` | **ABSENT** (013 **not** applied) |
| `job_schedules` | **ABSENT** (014 **not** applied) |
| `claims_lines` | ~3,505,919 |

**FORBIDDEN without explicit owner approval:** `alembic upgrade` past 012 on this database.

## Dec4 fixture checksums (must remain unchanged)

| File | SHA256 |
|------|--------|
| `v1.2/mri/MRI_RELEASE_BLOCKERS.json` | `a0b72f76986db6350534c739c04f50f543d5158b` |
| `v1.2/DEC4_NINE_PROTECTION.json` | `943d8abd3cf819534b6ea0ddf1ebf595cf34e0c8` |

## Feature flags (demo must keep OFF)

```
ENABLE_ANALYTICAL_OUTBOX=false
ENABLE_ENTERPRISE_SCHEDULER=false
ENABLE_SERVICE_BUS_DISPATCH=false
ENABLE_DATABRICKS_ANALYTICS=false
```

## Rollback triggers

- MRI/MPPR/SOS numerical drift vs known-answer
- Workspace/API regression on primary demo paths
- Alembic accidentally advanced past 012
- Worker/API crash loop

## Rollback steps (local)

1. Stop applying any new migrations.
2. Restore API/web from last known-good process or re-checkout `d74bd72` only if required (prefer not if live is healthy).
3. Restore DB from Azure backup if schema was altered (must not happen under this freeze).
4. Re-verify fixture checksums and `/health`.

## Allowed changes under freeze

- Critical bugfixes with explicit approval
- Documentation under `docs/production/` that does not alter runtime
- Staging-only code paths behind flags defaulting to **false**

## Git lock (post check-in)

| Field | Value |
|-------|-------|
| Lock commit | `e323da9afb2759be45771a7bd2ceb8a18c1bdffe` |
| Tag | `demo-dec4-freeze-2026-11-04` |
| Pushed | `origin/main` |
| Demo DB alembic | Remains **012** (do not auto-upgrade to 013/014) |

