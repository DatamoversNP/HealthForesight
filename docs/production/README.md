# Production Engineering Program

Start here for the Azure enterprise track. **December 4 demo is independent and protected.**

| Document | Purpose |
|----------|---------|
| [CURRENT_STATE_INVENTORY.md](./CURRENT_STATE_INVENTORY.md) | Wave 0 evidence-backed as-is |
| [AZURE_ENTERPRISE_ARCHITECTURE.md](./AZURE_ENTERPRISE_ARCHITECTURE.md) | Target reference architecture |
| [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) | ADRs (incl. ADR-005 dual deploy) |
| [OPERATING_MODELS.md](./OPERATING_MODELS.md) | SaaS + customer subscription profiles |
| [PRODUCTION_ENGINEERING_BACKLOG.md](./PRODUCTION_ENGINEERING_BACKLOG.md) | Wave backlog + status |
| [DEPLOYMENT_AND_INSTALLATION_RUNBOOK.md](./DEPLOYMENT_AND_INSTALLATION_RUNBOOK.md) | Install / rollback |
| [DATA_PLATFORM_MIGRATION_PLAN.md](./DATA_PLATFORM_MIGRATION_PLAN.md) | ADLS/Delta dual-run |
| [PERFORMANCE_AND_CAPACITY_REPORT.md](./PERFORMANCE_AND_CAPACITY_REPORT.md) | SLOs + measured |
| [RELIABILITY_AND_DR_REPORT.md](./RELIABILITY_AND_DR_REPORT.md) | HA/DR status |
| [SECURITY_READINESS_MATRIX.md](./SECURITY_READINESS_MATRIX.md) | Controls matrix |
| [PRODUCTION_RELEASE_GATES.md](./PRODUCTION_RELEASE_GATES.md) | Go-live MUST gates |

**Code:** `packages/common/src/uepi_common/execution/`, `apps/api/src/uepi_api/services/execution/`, alembic `013`–`014` (**staging only**).  
**IaC:** `infra/terraform/modules/enterprise/`, `envs/enterprise-staging` (`enable_provision=false`).  

**Phase A (demo protection):** [releases/PHASE_A_RELEASE_RECONCILIATION.md](./releases/PHASE_A_RELEASE_RECONCILIATION.md) · [releases/DEMO_DEC4_FREEZE.md](./releases/DEMO_DEC4_FREEZE.md) · [ENTERPRISE_SCHEDULING_ARCHITECTURE.md](./ENTERPRISE_SCHEDULING_ARCHITECTURE.md)
