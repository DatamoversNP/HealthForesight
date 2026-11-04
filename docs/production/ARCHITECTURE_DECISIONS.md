# Architecture Decision Records

## ADR-001 — Container Apps over AKS (first enterprise)

- **Status:** Accepted (2026-11-04)
- **Context:** Helm/AKS charts exist; first payer needs lower ops overhead.
- **Decision:** Azure Container Apps for API + workers/Jobs; AKS deferred.
- **Consequences:** Existing Helm is maintenance-only until AKS justified.

## ADR-002 — Service Bus + PostgreSQL job state (not Celery-as-HA)

- **Status:** Accepted as target; Celery remains compatibility path
- **Context:** Redis+Celery works for demo; not enterprise DLQ/HA story.
- **Decision:** PostgreSQL authoritative jobs + outbox; Service Bus Premium dispatch; Celery adapter until cutover.
- **Consequences:** One scheduler control plane; no Temporal unless ADR-003.

## ADR-003 — Temporal deferred

- **Status:** Deferred
- **Decision:** Do not add Temporal unless long-lived multi-step workflows exceed outbox+SB+reconciler.

## ADR-004 — Lakehouse for claims; PostgreSQL for transactions

- **Status:** Accepted as target
- **Decision:** ADLS Gen2 + Delta + Databricks SQL/Jobs for large analytics; PostgreSQL for metadata/job/result index.
- **Consequences:** Dual-run reconciliation required before switching reads (Wave 3).

## ADR-005 — Dual operating models (SaaS + customer subscription)

- **Status:** Accepted (2026-11-04)
- **Decision:** HealthForesight supports **both**:
  1. **SaaS** — hosted in HealthForesight’s Azure subscription (multi-tenant).
  2. **Customer-deployed** — installed into each payer’s Azure subscription.
- **Shared platform core:** Container Apps, Service Bus, PostgreSQL HA, ADLS/Delta, Databricks adapters, durable job contracts, same application images.
- **Mode-specific:** tenancy boundaries, Entra tenancy, Key Vault ownership, Private Link / VNet peering, CI/CD identity, data residency, ops runbooks.
- **Consequences:** IaC must be parameterized by `deployment_mode` (`saas` | `customer_subscription`); install automation must produce either footprint without forking business logic. Per-customer choice is a **configuration** decision at install time, not an architecture rewrite.
- **Unblocks:** Wave 2 identity/networking module design; does **not** authorize billable provision by itself.

## ADR-006 — Preserve Dec 4 demo environment

- **Status:** Accepted
- **Decision:** No policy customization in this program; frozen KA fixtures immutable; demo stack independent of enterprise-staging IaC.

## ADR-007 — Python worker pool on demo host

- **Status:** Accepted workaround
- **Context:** Celery prefork/billiard fails on Python 3.14 (`fast_trace_task` unpack).
- **Decision:** Threads pool + subprocess DB isolation for demo; production Linux workers prefer 3.11/3.12 + prefork.
