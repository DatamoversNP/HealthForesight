# Lean staging — product parity approval (web + synthetic everything)

**Date:** 2026-11-05  
**Status:** **AUTHORIZED** by owner implement request (plan: Staging product parity)  
**Subscription:** `94a13dda-e607-413d-a0ef-d9501e71e506`  
**RG:** `rg-healthforesight-enterprise-staging`  
**Demo freeze:** `healthforesight-rg` untouched; demo alembic stays **012**

---

## Decision

Stand up **Env #2** with full product surface on lean staging:

| Include | Exclude (this wave) |
|---------|---------------------|
| Staging web ACA (`hfleanstg-web`) separate URL | Demo App Service / Redis / DB changes |
| Wire web → staging API only | Service Bus Premium / PG ZR-HA / Databricks / Front Door |
| Seed users + Dec4 **9 policy** packages | Demo Postgres restore / PHI dump |
| Demo-comparable synthetic claims/obs/baselines | 100× load / claim production HA |

Soft budget remains **$400/mo**. This wave adds ~**$10–40** for web ACA (plus existing lean stack).

---

## Target URLs (live)

| Surface | URL |
|---------|-----|
| Staging web | https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io |
| Staging API | https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io |
| Demo web | https://healthforesight-web.azurewebsites.net (unchanged) |

Critical comparison: `LEAN_STAGING_VS_DEMO_CRITICAL_TEST.md` — **FAIL as Dec4 replacement**, PASS-with-gaps as enterprise sandbox.

---

## Isolation gates

- No writes to `healthforesight-rg` apps/DB (demo RG still 9).
- Seed scripts refuse non-`hfleanstg` / demo DB hosts.
- ACR tags use `lean-stg-*` only (do not retag demo `dec4-*` pins).

---

## Login

`admin@healthforesight.com` / `Swan@1234` (also `demo@example.com`) on staging web/API only.

## Seed snapshot (staging DB)

- policies: **9** (Dec4 nine)
- users: **6**
- claims_lines: **2887**
- observations: **20** rows / **5** latest_only
- predicted impacts: **9** (stub)
- alembic: **014_job_schedules**
