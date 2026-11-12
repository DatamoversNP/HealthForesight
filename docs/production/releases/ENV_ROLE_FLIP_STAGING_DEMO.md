# Environment role flip — staging becomes demo; current demo → dev validation

**Date:** 2026-11-05  
**Status:** **STAGING ELEVATED for Dec4-nine path** — cutover of room URL still **owner-gated**. Current demo stays frozen until you explicitly switch.

---

## Target end state

| Role | Environment | URL |
|------|-------------|-----|
| **Primary demo — HealthForesight** (target) | Staging elevated | https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io |
| **Primary demo — Data Voyager** (same API) | Staging elevated | https://hfleanstg-web-datavoyager.whiteplant-64737337.eastus2.azurecontainerapps.io |
| **Shared staging API** | Staging elevated | https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io |
| **Dev validation** (eventually) | Today’s `healthforesight-rg` | https://healthforesight-web.azurewebsites.net |
| **Production** | Future HA/Premium | later cost package |

Both staging frontends share one backend (`hfleanstg-api`) and one Postgres (`hfleanstg`). Branding differs via `VITE_APP_NAME` only.

**Until you say cutover:** Dec 4 may still use current demo. Staging is ready for side-by-side rehearsal.

---

## What was done (elevation)

| Gate | Status |
|------|--------|
| Warm web/API `minReplicas=1` | **DONE** — web ~0.6–0.8s (was ~27s cold) |
| Dual frontends (HealthForesight + Data Voyager) → same API | **DONE** |
| CORS both staging webs → staging-api | **DONE** |
| Dec4 nine policies | **DONE** 9/9 |
| Infusion procedure_codes patched | **DONE** |
| Non-stub predicted impacts (nine) | **DONE** (regenerated Stage 3.5) |
| Catalog denser (~250) + stub predicted/obs for demos | **DONE** |
| One latest observation per policy (mixed verdicts) | **DONE** catalog-wide |
| Demo RG untouched | **DONE** still 9 resources / freeze intact |
| Critical retest | **PASS_WITH_CRITICAL_GAPS** — Celery/SB E2E still open |
| Exact 289 catalog parity | **OPTIONAL** (~250 seeded) |
| Celery/SB worker E2E | **NOT_TESTED** |
| Official room cutover | **NOT DONE** — awaiting your go |

Login staging: `admin@healthforesight.com` / `Swan@1234`

---

## Cutover (when you approve)

Reply **CUTOVER DEMO TO STAGING** to:

1. Point Dec4 runbook / freeze primary URL at staging web.  
2. Relabel `healthforesight-rg` as **dev validation** (keep apps; do not destroy).  
3. Keep demo alembic at 012; staging stays on 014+.

Until then both envs run side-by-side; demo remains the safe default for live customers.
