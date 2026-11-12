# Lean staging apply + smoke report

**Date:** 2026-11-05  
**Env:** `infra/terraform/envs/enterprise-lean-staging`  
**Subscription:** `94a13dda-e607-413d-a0ef-d9501e71e506`  
**RG:** `rg-healthforesight-enterprise-staging`  
**Approval:** owner “approved” apply (Option B lean) + follow-on “yes go ahead” for isolated apps / outbox+schedule

---

## Verdict

| Gate | Result |
|------|--------|
| Terraform apply (lean SKUs) | **PASS** |
| Demo RG untouched (`healthforesight-rg` still 9 resources) | **PASS** |
| Staging alembic **014** on empty DB `hfleanstg` | **PASS** |
| Demo alembic remains **012** | **PASS** |
| KV secrets (PG, SB, Redis, DATABASE_URL) | **PASS** |
| Service Bus Standard send/receive | **PASS** |
| ADLS LRS containers + write/read | **PASS** |
| Budget alert $400 | **PASS** |
| Isolated Container Apps (API + web + 2 workers) | **PASS** |
| Outbox → SB Standard dispatch + receive | **PASS** |
| Schedule claim / cancel / recovery | **PASS** |
| API `/health` on staging FQDN | **PASS** |
| Product parity seed (9 policies + users + claims) | **PASS** (predicted/obs stubbed — see critical test) |
| Demo vs staging critical systems/integration/perf | **FAIL as Dec4 replacement** / sandbox PASS-with-gaps — `LEAN_STAGING_VS_DEMO_CRITICAL_TEST.md` |
| Premium / HA / Databricks / Front Door | **PASS** (absent by design) |
| Celery end-to-end task execution on staging queues | **NOT_TESTED** |

**Do not claim:** production HA, payer-scale performance, or Premium messaging readiness.

---

## Provisioned resources

| Resource | Name | Notes |
|----------|------|-------|
| PostgreSQL Flexible | `hfleanstg-pg` | `Standard_D2s_v3`, HA **Disabled** |
| Database | `hfleanstg` | Empty/synthetic; alembic **014** |
| Service Bus | `hfleanstg-bus` | **Standard**; `interactive`, `policy-analytics` |
| Storage (ADLS Gen2) | `hfleanstglake` | **LRS**; `raw` / `curated` / `results` |
| Key Vault | `hfleanstgkv` | staging-only secrets |
| Redis Cache | `hfleanstg-redis` | **Basic C0** (staging Celery broker; **not** demo Redis) |
| Log Analytics | `hfleanstg-law` | 30d retention |
| ACA Environment | `hfleanstg-cae` | eastus2 |
| Container Apps | `hfleanstg-api`, `hfleanstg-web`, `hfleanstg-worker-interactive`, `hfleanstg-worker-analytics` | web: `healthforesight-web:lean-stg-latest`; API/workers from ACR; secrets staging-only |
| Managed identity | `hfleanstg-mi` | Staging-only |
| VNet | `hfleanstg-vnet` | `10.50.0.0/16` |
| Budget | `hfleanstg-budget-400` | $400 / month soft alert |

---

## Isolation checks

| Check | Result |
|-------|--------|
| Demo RG resource count | **PASS** — still **9** |
| Demo App Service worker | **PASS** — still `Running` (untouched) |
| Staging workers broker | **PASS** — `hfleanstg-redis.redis.cache.windows.net` (not `nilesh-healthforesight-redis01`) |
| Staging DB vs demo DB | **PASS** — staging `014`; demo `012` |
| Shares demo credentials | **PASS** — KV secrets staging-generated |

---

## Apps + wiring

| App | Image | Wiring |
|-----|-------|--------|
| `hfleanstg-web` | `healthforesight-web:lean-stg-latest` | `VITE_API_URL` → staging API; external ingress |
| `hfleanstg-api` | `healthforesight-api:dec4-stab-5b587ed` | staging `DATABASE_URL` + CORS → staging web; Redis secret |
| `hfleanstg-worker-interactive` | `healthforesight-worker:latest` | staging DB + Redis only |
| `hfleanstg-worker-analytics` | `healthforesight-worker:latest` | same |

- Web: https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io/  
- API: https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/

Code: `outbox_relay.publish_service_bus_outbox_row` + `scripts/lean_staging_outbox_schedule_smoke.py` (SB path; Celery remains compat).

---

## Outbox + schedule smoke

Script: `scripts/lean_staging_outbox_schedule_smoke.py`  
Guards: refuses demo `DATABASE_URL` / non-`hfleanstg-bus` SB strings.

| Step | Result |
|------|--------|
| Insert `AnalyticalJob` + `job_outbox` (`destination=service_bus`) | PASS |
| `drain_pending_outbox` → publish | PASS (`published: 1`) |
| Job `QUEUED` / outbox `PUBLISHED` | PASS |
| Receive message on `policy-analytics` | PASS |
| Schedule claim (`ENABLE_ENTERPRISE_SCHEDULER=true`) | PASS |
| Cancel occurrence | PASS |
| Recovery claim (new occurrence id) | PASS |

---

## Alembic path (staging only)

1. Empty DB `hfleanstg`.  
2. Upgrade through bootstrap; stamp **012** (tables already from `create_all`).  
3. Upgrade **013 → 014**.  
Demo freeze: **no** alembic past 012 on demo.

---

## Cost posture

| Item | Value |
|------|-------|
| Budget alert | $400 / mo |
| Added vs original lean plan | Redis Basic C0 + 3 Container Apps |
| 14-day review | Destroy or re-approve expanded scope |

Teardown (Terraform-managed core):

```bash
cd infra/terraform/envs/enterprise-lean-staging
terraform destroy -var='enable_provision=true'
```

Also delete az-created apps/redis if not imported to state:

```bash
az containerapp delete -g rg-healthforesight-enterprise-staging -n hfleanstg-api -y
az containerapp delete -g rg-healthforesight-enterprise-staging -n hfleanstg-worker-interactive -y
az containerapp delete -g rg-healthforesight-enterprise-staging -n hfleanstg-worker-analytics -y
az redis delete -g rg-healthforesight-enterprise-staging -n hfleanstg-redis -y
```

---

## Remaining (optional)

1. Import az-created apps/redis into Terraform state (or keep CLI-managed until 14-day destroy).  
2. Rebuild/push staging image with `azure-servicebus` for in-cluster SB relay (smoke used local code + staging SB).  
3. Celery task E2E on staging Redis queues.  
4. Premium / ZR-HA / Databricks — **new** cost package + explicit approval.
