# Production Engineering Backlog

Wave-gated. Demo preservation is a hard constraint on every item.

## Phase A — Demo release protection (2026-11-04)

| ID | Item | Status |
|----|------|--------|
| PA-1 | Reconcile git vs live demo vs alembic | DONE — demo at **012**; 013/014 blocked |
| PA-2 | Freeze Dec4 fixtures + flags | DONE — `DEMO_DEC4_FREEZE.md` |
| PA-3 | Azure read-only discovery | DONE — `releases/azure_discovery_*.json` |
| PA-4 | Schedule registry code (flag off) | DONE — models + 014 + dispatcher stub |
| PA-5 | Staging apply 013/014 | BLOCKED — needs non-demo DB + approval |
| PA-6 | Terraform apply staging | BLOCKED — needs cost approval |

## Wave 0 — Discovery (in progress / delivered)

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| W0-1 | Current-state inventory | DONE | `CURRENT_STATE_INVENTORY.md` |
| W0-2 | ADRs | DONE | `ARCHITECTURE_DECISIONS.md` |
| W0-3 | Reference architecture | DONE | `AZURE_ENTERPRISE_ARCHITECTURE.md` |

## Wave 1 — Durable execution foundation

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| W1-1 | Execution contracts | DONE | `packages/common/.../execution/contracts.py` |
| W1-2 | Idempotency helper | DONE | `idempotency.py` + unit tests |
| W1-3 | Outbox + AnalyticalJob models | DONE | `services/execution/outbox.py`, alembic `013` |
| W1-4 | Celery outbox dispatcher | DONE | `celery_dispatcher.py`, `outbox_relay.py` |
| W1-5 | Apply migration on demo DB | PENDING | Requires explicit migrate authorization |
| W1-6 | Service Bus dispatcher adapter | NOT STARTED | After SB provision authorized |
| W1-7 | Reconciliation controller (leases/orphans) | NOT STARTED | Builds on isolated_analytics |
| W1-8 | Wire API job-submit endpoint to dispatcher | NOT STARTED | Feature-flagged |

## Wave 2 — Azure landing zone (IaC only until authorized)

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| W2-1 | Networking / SB / ACA / PG HA / ADLS modules | DONE (definitions) | `infra/terraform/modules/enterprise/*` |
| W2-2 | enterprise-staging env | DONE (`enable_provision=false`) | `envs/enterprise-staging` |
| W2-3 | Key Vault + MI + Front Door modules | NOT STARTED | |
| W2-4 | Databricks workspace module | NOT STARTED | |
| W2-5 | Authorized `terraform apply` staging | BLOCKED | Needs explicit billable auth (ADR-005 dual-mode **accepted**) |
| W2-6 | Mode-specific identity profiles (SaaS vs customer) | NOT STARTED | `deployment_mode` var present; Entra/KV modules pending |
| W2-7 | Customer-subscription install pack | NOT STARTED | Same images; payer sub tfvars + runbook |

## Wave 3 — Analytical data plane

| ID | Item | Status |
|----|------|--------|
| W3-1 | Delta table contracts + dual-run harness | NOT STARTED |
| W3-2 | Databricks execution adapter behind interface | NOT STARTED |
| W3-3 | Stop large JSON claims in PG (guardrails) | NOT STARTED |

## Wave 4 — Performance & HA

| ID | Item | Status |
|----|------|--------|
| W4-1 | Expand benchmark harness vs SLO table | PARTIAL (enterprise hardening report) |
| W4-2 | Staging fault injection | NOT STARTED |
| W4-3 | PG HA failover test | NOT STARTED |

## Wave 5 — First-customer install automation

| ID | Item | Status |
|----|------|--------|
| W5-1 | Parameterized install scripts | NOT STARTED |
| W5-2 | Smoke + rollback gates in CI | NOT STARTED |

## Explicitly out of scope

- Policy customization / expanding 289 catalog
- Inventing proprietary payer rules
- Billable Azure provision without authorization
- Claiming HIPAA compliance from Azure SKUs alone
