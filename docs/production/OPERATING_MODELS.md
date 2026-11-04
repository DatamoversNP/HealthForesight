# Operating Modes (ADR-005)

**Accepted:** both **SaaS** (HealthForesight Azure subscription) and **customer subscription** deploy-in.

## Selection

```hcl
deployment_mode = "saas" | "customer_subscription"
```

Set per environment / customer install. Same container images and job contracts in both modes.

## Non-negotiable isolation rules (both modes)

1. No claims or large results in queue messages or workflow state — **refs only**.
2. Cache keys include `tenant_id` + dataset version + configuration digest.
3. Result publication is atomic; never cross-tenant artifact URIs.
4. Support access (HF) to customer-deployed stacks uses explicit MI + JIT, not standing admin passwords.
5. Demo / Dec 4 environment remains outside customer and SaaS production stamps.

## SaaS stamp profile

- One or more regional **stamps** (API + workers + SB + PG + lake).
- Tenants mapped via config: storage prefix, Databricks catalog/schema, optional dedicated compute pool.
- Front Door routes by hostname or path; WAF shared.
- HF operates backups, patching, capacity; customer gets contractual data residency region.

## Customer subscription profile

- Terraform/Bicep applied into payer subscription (customer SP or HF deploy MI invited).
- Resources named with payer prefix; single-tenant by default.
- Networking: customer VNet subnets for ACA + private endpoints; optional peering to HF management for support.
- Identity: customer Entra app registration; HF optional federated credential for release promotion.
- Data never lands in HF subscription unless contractually escrowed (default: **no**).

## Install automation inputs (minimum)

| Parameter | SaaS | Customer |
|-----------|------|----------|
| `deployment_mode` | `saas` | `customer_subscription` |
| `azure_subscription_id` | HF sub | Payer sub |
| `tenant_id` (Entra) | HF | Payer |
| `resource_group_name` | HF naming | Payer naming |
| `location` | Agreed region | Agreed region |
| `data_residency_region` | Required | Required |
| `entra_authority` | HF (+ federated IdPs) | Customer |
| `key_vault_name` | HF KV | Customer KV |
| `enable_provision` | Auth required | Auth required |

## What stays identical

- Application code and analytical adapters
- Durable job outbox semantics
- Workload classes (interactive / async / heavy)
- Evidence types and result publication contracts
- Release gates quality bar (mode-specific evidence attached)
