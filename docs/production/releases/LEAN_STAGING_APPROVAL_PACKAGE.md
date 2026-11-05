# Lean Azure Staging — Final Approval Package (Option B)

**Decision recorded:** Option B engineering direction **conditionally approved** for plan preparation.  
**This package:** planning complete. **`terraform apply` is NOT authorized** until you reply with explicit apply approval.  
**Date:** 2026-11-05  
**Authoring commit path:** `infra/terraform/envs/enterprise-lean-staging/`

---

## 1. Subscription & permissions (read-only verified)

| Field | Value |
|-------|--------|
| Subscription ID | `94a13dda-e607-413d-a0ef-d9501e71e506` |
| Subscription name | Azure subscription 1 |
| Tenant ID | `8c6c7629-ffe0-44fd-8610-7ab93d8b90e4` |
| Signed-in user | `nileshlalchandpatil23@gmail.com` |
| Role on subscription | **Owner** (sufficient to create RG, assign KV RBAC, set budget) |
| Region | `eastus2` (available) |

**Permissions needed to provision:** Owner or (Contributor + User Access Administrator) on the subscription or a management group that can create `rg-healthforesight-enterprise-staging`. Current identity already has Owner.

---

## 2. Demo isolation verification

| Check | Result |
|-------|--------|
| Target RG | `rg-healthforesight-enterprise-staging` (**new**) |
| Forbidden RG `healthforesight-rg` in plan addresses | **PASS** — zero matches |
| Plan modifies/deletes existing resources | **PASS** — `0 to change, 0 to destroy` |
| Demo App Services / PG / Redis referenced | **PASS** — none |
| Shares demo credentials / connection strings | **PASS** — new random PG password → staging Key Vault only |
| Demo Alembic 012 | Untouched (no DB connection in this plan) |
| Frozen MRI/MPPR/SOS fixtures | Untouched |
| VNet CIDR | `10.50.0.0/16` (not demo defaults) |

**Plan summary:** **23 to add, 0 to change, 0 to destroy.**  
Artifacts: `docs/production/releases/lean_staging_plan/`

---

## 3. Planned resources (lean configuration)

| # | Resource | SKU / notes |
|---|----------|-------------|
| 1 | Resource group `rg-healthforesight-enterprise-staging` | eastus2 |
| 2 | VNet + 3 subnets (ACA delegated, data, PE) | `10.50.0.0/16` |
| 3 | PostgreSQL Flexible Server `hfleanstg-pg` | **B_Standard_B2s**, 32 GiB, **single-AZ**, no ZR HA |
| 4 | PG firewall AllowAzureServices | lean public access; tighten later |
| 5 | Service Bus namespace `hfleanstg-bus` | **Standard** (not Premium) |
| 6 | Queues `policy-analytics`, `interactive` | duplicate detection on |
| 7 | Storage `hfleanstglake` ADLS Gen2 | **LRS**; containers `raw` / `curated` / `results` |
| 8 | Log Analytics + Container Apps **Environment** | retention **30d** (Azure minimum); **no app revisions yet** |
| 9 | User-assigned managed identity | staging-only |
| 10 | Key Vault (RBAC) + PG password/FQDN secrets | staging-only secrets |
| 11 | Consumption budget $400 / mo | alerts at 80% Actual + 100% Forecasted |

**Explicitly NOT in this plan:** Databricks, Front Door, Service Bus Premium, PG zone-redundant HA, Container App API/worker revisions, demo workers, PHI/claims copy.

---

## 4. Itemized monthly cost estimate (planning)

**Not a subscription quote.** Confirm in [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) on sub `94a13dda-…` before apply.

| Component | Low $/mo | High $/mo | Notes |
|-----------|----------|-----------|-------|
| PostgreSQL B2s compute | ~50 | ~70 | eastus2-class list |
| PG storage 32 GiB | ~4 | ~8 | ~$0.115/GiB |
| Service Bus Standard | ~10 | ~25 | base + ops if over 13M |
| ADLS LRS (light) | ~1 | ~5 | growth-dependent |
| Log Analytics | ~5 | ~25 | retention floor 30d; control ingestion |
| Key Vault ops | ~1 | ~5 | |
| VNet / MI / ACA env (no apps) | ~0 | ~10 | apps deferred |
| **Total** | **~$72** | **~$143** | well under **$400** ceiling |

JSON: `LEAN_STAGING_COST_ESTIMATE.json`

**Hidden / watch items:** ACA when apps are later authorized; SB ops overage; log ingestion spikes; public PG bandwidth; name uniqueness retries.

**Budget alert ≠ hard cap.** Soft alert at $400 + deployment limits (no Premium/HA in this env) + destroy procedure below.

---

## 5. Teardown / stop procedure

After tests or at day-14 review:

```bash
cd infra/terraform/envs/enterprise-lean-staging
# requires terraform.tfvars with enable_provision=true (local only)
terraform destroy -var='enable_provision=true'
```

Optional interim cost control (before destroy): stop PG compute via Azure Portal / CLI (`az postgres flexible-server stop`) — confirm SKU supports stop; SB Standard has no “stop” (delete namespace or accept base fee).

**14-day review:** destroy or re-approve expanded scope (Premium/HA/Databricks) with a new cost package.

---

## 6. After *separate* apply approval (NOT yet)

1. `terraform apply` this plan only.  
2. Verify RG isolation (no demo RG changes).  
3. Init **empty/synthetic** staging DB (no demo claims dump).  
4. Apply Alembic **013 → 014** on staging only.  
5. Deploy **isolated** staging workers (never demo App Service workers).  
6. Test outbox + SB Standard dispatch, schedules, cancel/recovery, ADLS layout.  
7. Report PASS/FAIL/NOT_TESTED per test; capture actual spend.  
8. Do **not** claim production HA or payer-scale performance.

---

## 7. Terraform validation status

| Gate | Result |
|------|--------|
| `terraform init` | PASS |
| `terraform validate` | PASS |
| `terraform plan` (enable_provision=true, local tfvars) | PASS — 23 add / 0 change / 0 destroy |
| Demo isolation scan | PASS |
| Cost vs $400 ceiling | PASS (planning ~$72–$143) |

**Apply:** **NOT_TESTED / BLOCKED** — awaiting your explicit “approve apply”.

---

## 8. Approval ask (copy-paste reply)

If the plan is acceptable:

> **APPROVE LEAN STAGING APPLY** — subscription `94a13dda-e607-413d-a0ef-d9501e71e506`, RG `rg-healthforesight-enterprise-staging`, plan 23-add/0-change/0-destroy, budget alert $400, 14-day review, synthetic data only, no demo RG touch.

If not:

> **REJECT / REVISE** — (note SKU or scope changes).

Until that message, Cursor will **not** run `terraform apply` or create billable resources.
