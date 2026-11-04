# Azure Enterprise Architecture (Reference)

**Status:** Target architecture — **not** fully implemented.  
**Decision date:** 2026-11-04  
**Related:** [CURRENT_STATE_INVENTORY.md](./CURRENT_STATE_INVENTORY.md), [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md)

## Guiding principle

A new customer requires **configuration, data mapping, capacity, validation** — not redesign.

## Target topology

```
Front Door Premium + WAF
        │
Container Apps (API + read APIs + job submit)
        │
   ┌────┴─────────────────────┐
   │                          │
Service Bus Premium     PostgreSQL Flexible HA
 (dispatch + DLQ)        (job state, config, result index)
   │
   ├─ Container Apps workers / Jobs  (bounded analytics)
   └─ Databricks Jobs                 (heavy scans/simulations)
            │
     ADLS Gen2 + Delta Lake
     (raw → curated → aggregates → results)
```

Redis: optional bounded cache when benchmarks show benefit.

## Workload classes

| Class | Runtime | Budget |
|-------|---------|--------|
| INTERACTIVE | Container Apps replicas | Queue wait + compute separate; p95 targets in PERFORMANCE report |
| ASYNC_COHORT | Container Apps Jobs / workers | Concurrent policy jobs; hard cancel |
| HEAVY_DISTRIBUTED | Databricks Jobs | Scheduled windows; cost per workload |

## Job control (single scheduler)

**Do not** run Celery + Service Bus + Temporal as overlapping schedulers.

**Default v1:**
1. PostgreSQL = authoritative job state (+ outbox)
2. Service Bus Premium = durable dispatch (target)
3. Celery = **compatibility adapter** until Service Bus workers cut over
4. Reconciliation controller = leases, cancel, orphan `pg_stat_activity`

Temporal: **conditional** — only if benchmarks require it ([ADR-003](./ARCHITECTURE_DECISIONS.md)).

## Storage rules (enforced in contracts)

- Never store enterprise claims as large JSON in PostgreSQL.
- Never put large datasets in Service Bus / workflow state.
- Pass **immutable refs** (URI, checksum, version).
- Atomic result publication; partial files ≠ completed evidence.

## Operating models (ADR-005 — both supported)

HealthForesight is built once and installed in either mode. Mode is selected at **environment provision / customer onboarding**, not by forking the product.

| Dimension | SaaS (HF subscription) | Customer subscription |
|-----------|------------------------|------------------------|
| Azure bill / RG ownership | HealthForesight | Payer |
| Tenancy | Logical multi-tenant (`tenant_id` + storage prefixes / catalogs) | Typically single-tenant stack per payer |
| Ingress | Shared Front Door + WAF; host/path or app routing per tenant | Customer Front Door or private ingress; optional HF-managed ops |
| Identity | HF Entra + optional customer IdP federation | Customer Entra primary; HF break-glass / support MI as agreed |
| Secrets | HF Key Vault; per-tenant secret isolation | Customer Key Vault; HF deploy MI with least privilege |
| Network | HF VNet; private endpoints; optional customer Private Link into SaaS | Deploy into customer VNet; Private Link to data plane; no cross-tenant data path |
| Data plane | Shared PG flexible + per-tenant row security / DB; ADLS paths `tenant={id}/…` | Dedicated PG + ADLS account (or dedicated containers) in customer sub |
| CI/CD | HF pipelines deploy shared stamps + tenant config | HF or customer pipeline applies same modules with customer SP/MI |
| Ops | HF SRE primary | Shared responsibility; customer owns subscription quotas/DR region choice |

See [OPERATING_MODELS.md](./OPERATING_MODELS.md) for install parameters and isolation rules.

## IaC entrypoint

`infra/terraform/envs/enterprise-staging` — modules under `infra/terraform/modules/enterprise/`.  
**`enable_provision` defaults to `false`.** No billable create without authorization.

## Preserve December 4

Demo App Service / demo7867 remains independent. Frozen MRI/MPPR/SOS KA fixtures unchanged by this program.
