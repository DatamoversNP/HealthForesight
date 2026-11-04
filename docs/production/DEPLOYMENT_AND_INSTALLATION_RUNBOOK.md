# Deployment and Installation Runbook

## Environments

| Env | Purpose | Provision |
|-----|---------|-----------|
| demo7867 / Dec4 | Frozen demo | **Do not use enterprise IaC** |
| enterprise-dev | Engineering | IaC when authorized |
| enterprise-staging | Dual-run / fault injection | IaC when authorized |
| enterprise-prod | First customer | Explicit go-live gates |

## Current production-like path (legacy App Service)

Documented in `scripts/azure/DEPLOY_PRODUCTION_AZURE.md`:
1. Fill `production.azure.env` (never commit secrets)
2. `./scripts/azure/deploy-production-stack.sh`
3. API + worker App Services, Redis, PostgreSQL

## Target enterprise path (Container Apps)

ADR-005: choose **`deployment_mode`** = `saas` or `customer_subscription` (both supported). See [OPERATING_MODELS.md](./OPERATING_MODELS.md).

1. Set mode + subscription ownership in `terraform.tfvars` (from `terraform.tfvars.example`).
2. `cd infra/terraform/envs/enterprise-staging`
3. Review modules; keep `enable_provision=false` until written authorization.
4. `terraform plan` only by default.
5. After authorization: create RG in the **owner** subscription, set `enable_provision=true`, apply, wire Key Vault (HF or customer), deploy **same** images from ACR.
6. Run alembic migrations including `013_analytical_jobs_outbox`.
7. Smoke: `/health`, job submit → outbox → worker, cancel probe.
8. Rollback: redeploy previous image digest; do not drop outbox tables casually.

## Customer install checklist (Wave 5 target)

- [ ] Environment provision (scripted)
- [ ] Identity / Key Vault
- [ ] Migrations
- [ ] Storage init (raw/curated/results)
- [ ] Resumable bulk load
- [ ] Health + performance smoke
- [ ] DR restore drill evidence
- [ ] Sign-off against `PRODUCTION_RELEASE_GATES.md`

## Rollback

- Application: previous container digest.
- Schema: expand/contract migrations only; never destructive without backup proof.
- Demo: untouched by enterprise apply.
