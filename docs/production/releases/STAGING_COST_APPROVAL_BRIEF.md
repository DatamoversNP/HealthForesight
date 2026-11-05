# Enterprise staging — cost approval brief

**Status:** OPTION B DIRECTION APPROVED — lean **plan package ready**; **`terraform apply` still blocked**  
**Follow-up package:** `LEAN_STAGING_APPROVAL_PACKAGE.md` (subscription, plan, costs, teardown)  
**Demo constraint:** Dec4 freeze unchanged. No alembic past **012** on demo DB. No changes to `healthforesight-rg` demo apps for this work.  
**IaC (lean):** `infra/terraform/envs/enterprise-lean-staging`  
**IaC (full/expensive reference):** `infra/terraform/envs/enterprise-staging` (Premium + ZR HA — not for first apply)

## What we are asking to create

Isolated landing zone (new RG only):

| Resource | Module default | Notes |
|----------|----------------|-------|
| Resource group | `rg-healthforesight-enterprise-staging` | eastus2 |
| VNet + 3 subnets | networking | Container Apps / data / PE |
| PostgreSQL Flexible **GP_Standard_D4s_v3**, 128 GiB, **Zone-Redundant HA** | postgres_ha | Staging clone target for 013/014 |
| Service Bus **Premium** 1 MU + queues | service_bus | Target durable dispatch |
| Container Apps Environment (+ Log Analytics) | container_apps | Apps wired after KV/images |
| ADLS Gen2 (ZRS) `raw` / `curated` / `results` | adls | Lakehouse landing |

**Not in this apply:** Databricks, Front Door, Key Vault/MI modules (Wave 2 follow-ons). Demo App Service stack untouched.

## Cost estimate (list USD / month, eastus2-class, ±20%)

| Item | Ballpark $/mo | Driver |
|------|---------------|--------|
| PostgreSQL D4s_v3 + ZR HA + 128 GiB×2 | **~$520–600** | HA doubles compute+storage |
| Service Bus Premium 1 MU | **~$650–700** | Flat MU hour rate |
| Container Apps env + light API/workers | **~$50–200** | Usage-dependent |
| ADLS Gen2 ZRS (light staging) | **~$15–40** | Mostly storage |
| Log Analytics (30d) | **~$20–80** | Ingestion |
| **Full stack (as coded)** | **~$1,300–1,700** | SB Premium + PG HA dominate |

Sources: Azure public list-price ballparks (PG D4s_v3 ~$0.34/hr; ZR HA ≈ 2×; SB Premium ~$0.93/MU-hr). Confirm in [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) on the billable subscription before apply.

## Recommended approval options

### Option A — Full coded staging (architecture-faithful)
- Authorize `enable_provision=true` as modules are written.
- Best for SB Premium + PG HA drills.
- **Cost:** ~$1.3–1.7k/mo until destroyed.

### Option B — Lean staging first (recommended to unblock Wave 1 tests)
Phase B1 (cheaper, still isolated from demo):
1. New RG + **single-AZ** PG (Burstable or small GP, e.g. D2s) — restore/clone schema+demo data subset or empty with migrations.
2. Apply alembic **013 → 014** there only.
3. Service Bus **Standard** (or keep Celery/Redis outbox path) for dispatcher dual-run.
4. Defer Premium SB + ZR HA + full ACA to Phase B2.

**Cost B1 ballpark:** ~$150–400/mo depending on PG SKU.  
Unblocks: outbox concurrency, schedule occurrence tests, API job-submit flag, dual-run harness against non-demo DB.

### Option C — Defer all Azure create
Continue code-only (KV/MI modules, SB adapter behind interface, dual-run harness stubs). No billable resources.

## Hard non-negotiables (any option that provisions)

1. **New RG only** — never apply enterprise modules into `healthforesight-rg`.
2. Demo DB stays on alembic **012**.
3. Frozen MRI/MPPR/SOS KA fixtures immutable.
4. `enable_provision` flips only after written approval of option + subscription.
5. Destroy plan documented before long-lived spend (tag `purpose=enterprise-staging`, owner, review date).

## Approval checklist (reply with choices)

- [ ] Option **A** / **B** / **C**
- [ ] Subscription: `healthforesight` (SaaS) or other (`owner_subscription_label`)
- [ ] Region confirm: `eastus2` (or specify)
- [ ] Max monthly spend cap: $______
- [ ] Destroy-by date or “keep until ______”
- [ ] Explicit: **do not** touch demo App Service / demo Postgres

## After approval (Cursor sequence)

1. Create RG + tfvars (gitignored secrets).
2. `terraform plan` with `enable_provision=true` → owner spot-check.
3. `terraform apply` (authorized only).
4. PG: restore/clone or migrate empty → **013 → 014**.
5. Wire Key Vault secrets; deploy same ACR images to ACA (or keep App Service workers pointed at staging DB for B1).
6. Run outbox + scheduler reliability tests; update backlog PA-5/PA-6 → DONE.

## Explicitly not started until after apply

- W1-6 Service Bus dispatcher against real namespace  
- W2-5 marked DONE  
- W3 lakehouse dual-run on ADLS  
- W4 fault injection / PG failover  
