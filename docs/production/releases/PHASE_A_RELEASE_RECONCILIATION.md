# Phase A — Release Reconciliation & Demo Protection Report

**Generated:** 2026-11-04  
**Scope:** Non-destructive discovery + classification. **No demo migration. No Azure apply.**

## 1. Exact deployed demo revision

| Layer | State | Notes |
|-------|-------|-------|
| Git HEAD (committed) | `d74bd7262b3dda967f0b199604f2448321a64c12` | Last known-good **committed** |
| Working tree | **Dirty** — large uncommitted demo + enterprise diffs | Repo ≠ clean release tag yet |
| API process | Live uvicorn 7867 | Healthy; not restarted for this report |
| Web process | Vite demo7867 7868 | HTTP 200 |
| Worker processes | 2× threads harden0/1 | Loaded newer worker modules from workspace |
| DB alembic | **012** | **013/014 NOT applied** |
| Outbox tables | Missing | Safe for demo |

**PASS:** Demo DB schema not advanced.  
**PASS:** API/web responsive.  
**NOT_TESTED:** Full 289 browser KA suite in this Phase A pass (baselines captured; full suite = next staging gate).

## 2. Change reconciliation matrix (summary)

| Change set | Classification | Deployed to demo? | Action |
|------------|----------------|-------------------|--------|
| Dec4 policy packages / evidence under `docs/demo/bcbs-nc/` | REQUIRED_FOR_DEMO (artifacts) | Files on disk; fixtures frozen | **Freeze** — do not rewrite KA |
| UI/API demo improvements (verdicts, workspace, what-if, etc.) | SAFE_BACKWARD_COMPATIBLE / REQUIRED_FOR_DEMO | Running via live processes from workspace | Leave running; no further schema |
| `uepi_common.execution` contracts | STAGING_ONLY / PRODUCTION_ARCHITECTURE_ONLY | Code present; unused by default | Keep flag-off |
| AnalyticalJob + outbox + alembic **013** | REQUIRES_MIGRATION + STAGING_ONLY | **Not applied** | **BLOCKED on demo** |
| Celery `policy_analytics_*` + `isolated_analytics` | STAGING_ONLY (hardening) | Workers have code loaded | Do not point demo product path at them |
| Celery app refactor (`celery_app.py`) | SAFE_BACKWARD_COMPATIBLE if workers already use it | Workers using it | Leave; avoid Beat as authority |
| Terraform enterprise modules | PRODUCTION_ARCHITECTURE_ONLY | Definitions only | Plan/approval before apply |
| Schedule registry + alembic **014** | STAGING_ONLY | **Not applied** | **BLOCKED on demo** |
| Dual-mode ADR-005 docs | PRODUCTION_ARCHITECTURE_ONLY | Docs only | N/A |
| `.env.demo7867` | Local secrets | Local only | Never commit |

### Classification legend used

- **REQUIRED_FOR_DEMO** — needed for Dec4 narrative  
- **SAFE_BACKWARD_COMPATIBLE** — no schema; additive  
- **STAGING_ONLY** — validate off demo first  
- **REQUIRES_MIGRATION** — needs alembic on non-demo DB first  
- **PRODUCTION_ARCHITECTURE_ONLY** — Azure/IaC  
- **BLOCKED** — must not touch demo

## 3. Regression / known-answer (this pass)

| Check | Result |
|-------|--------|
| API `/health` | **PASS** |
| Web `:7868` | **PASS** (200) |
| MRI/MPPR/SOS fixture checksums | **PASS** (unchanged hashes recorded in freeze doc) |
| alembic stays 012 | **PASS** |
| Full 9-policy numerical KA browser | **NOT_TESTED** this pass |
| Migration 013 on restored clone | **NOT_TESTED** (requires staging DB) |

## 4. Demo freeze & rollback evidence

See `DEMO_DEC4_FREEZE.md`.

## 5. Azure subscription discovery (read-only)

| Item | Result |
|------|--------|
| `az` authenticated | **PASS** — user `nileshlalchandpatil23@gmail.com` |
| Subscription | `Azure subscription 1` (`94a13dda-e607-413d-a0ef-d9501e71e506`) |
| Resource groups / PG / Redis / WebApps | Captured under `azure_discovery_*.json` |
| Terraform apply | **NOT_TESTED / BLOCKED** — awaiting explicit cost approval |
| Destructive actions | None performed |

## 6. Terraform plan / approval requirements

**Before any `terraform apply`:** owner must approve subscription, SKUs, estimated monthly cost, and `enable_provision=true`.  
Modules exist at `infra/terraform/envs/enterprise-staging` with `enable_provision=false`.

## 7. Scheduling architecture (decision + code started)

| Decision | Status |
|----------|--------|
| Authority | PostgreSQL schedule + occurrence ledger |
| Trigger | Azure Container Apps **scheduled Job** (not Celery Beat, not per-policy Azure crons) |
| Dispatch | Outbox → Service Bus (target); Celery adapter during migration |
| Data-aware | `required_data_watermark` → defer if not ready |
| Dual mode | Same artifacts; `deployment_mode` saas \| customer_subscription |

**Implemented (inactive on demo):**
- `uepi_common.execution.scheduling`
- `uepi_api.models.scheduling`
- `schedule_dispatcher.py` (`ENABLE_ENTERPRISE_SCHEDULER` default **false**)
- alembic **014** (depends on 013; **not applied**)

| Scheduler reliability tests | Result |
|----------------------------|--------|
| Contract unit tests | Runnable locally |
| Duplicate occurrence under concurrency | **NOT_TESTED** (needs staging DB) |
| Missed-run recovery | **NOT_TESTED** |
| DST | **NOT_TESTED** |

## 8. Remaining production-readiness gaps

- Shared PG analytics (~3.5M lines) vs 5–6M-life volume  
- Lakehouse / Databricks path not executed  
- Outbox not integrated into live API job submit  
- Service Bus not provisioned  
- HA / DR drills missing  
- Install automation incomplete  

## 9. Acceptance criteria snapshot

| Criterion | Status |
|-----------|--------|
| Demo protected / freeze documented | **PASS** |
| 013 not on demo | **PASS** |
| Azure discovery read-only | **PASS** |
| Staging provisioned | **NOT_TESTED** (needs approval) |
| Delta analytical path | **NOT_TESTED** |
| Scheduler HA tests | **NOT_TESTED** |
| Enterprise production ready | **FAIL** (correctly not claimed) |

## 10. Next safe implementation action

1. **Owner:** confirm demo freeze (no alembic past 012 on demo DB).  
2. **Cursor (after approval):** create **isolated staging** RG + PG clone; apply 013→014 there only; run outbox + scheduler tests.  
3. Present Terraform plan + cost estimate for staging; wait for apply authorization.  
4. Do **not** restart demo API solely to load enterprise flags.

**Immediate instruction compliance:** Phase A non-destructive work completed; provisioning gated.
