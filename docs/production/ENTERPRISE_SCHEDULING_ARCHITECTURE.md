# Enterprise Scheduling Architecture

**Decision:** Hybrid — Azure-managed trigger + HealthForesight-owned schedule data.

## Do / Don't

| Do | Don't |
|----|-------|
| One Container Apps scheduled Job (UTC cron) as dispatcher wake-up | Celery Beat as production authority |
| PostgreSQL schedule + occurrence ledger | Hundreds of per-policy Azure crons |
| Outbox → Service Bus → workers | Custom always-on Python cron daemon |
| Data-watermark gates | Run observations on incomplete claims |
| Same images for SaaS & customer-subscription | Fork product per deploy mode |

## Flow

```
ACA Scheduled Job (cron)
        │
        ▼
Dispatcher (claim due rows FOR UPDATE SKIP LOCKED)
        │
        ├─ watermark OK? ──no──► DEFERRED_DATA_NOT_READY
        │
        ▼ yes
AnalyticalJob + job_outbox (atomic)
        │
        ▼
Service Bus (or Celery adapter)
        │
        ▼
Workers / Databricks by workload class
        │
        ▼
Occurrence COMPLETED + evidence refs
```

## Occurrence identity

Unique `(schedule_id, occurrence_key, configuration_version)` — source of truth for exactly-once **logical** runs. Service Bus duplicate detection is auxiliary only.

## Workload classes

Observation · Ingestion · Incremental refresh · Baseline/prediction · Heavy simulation · Maintenance

## Feature flags

`ENABLE_ENTERPRISE_SCHEDULER` must be **false** on Dec4 demo.
