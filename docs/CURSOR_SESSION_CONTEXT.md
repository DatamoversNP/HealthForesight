# Cursor / session handoff — HealthForesight (UEPI) migration repo

**Use this file when reopening Cursor** after shutdown, sleep, or a new chat. Paste or say: *“Read `docs/CURSOR_SESSION_CONTEXT.md` and continue.”*

Do **not** put real passwords or full `DATABASE_URL` strings in this file; use env vars and placeholders only.

---

## 1. What this repo is

- Monorepo: **API** (`apps/api`, FastAPI, Alembic, PostgreSQL), **web** (`apps/web`), **worker** (`apps/worker`), **common** (`packages/common`).
- **Demo tenant UUID:** `00000000-0000-0000-0000-000000000001`
- **Demo user UUID** (matches `demo@example.com` from seed): `00000000-0000-0000-0000-000000000001` (`DEFAULT_USER_ID` in `storage_auth.py`)

---

## 2. Azure PostgreSQL demo seed (main script)

- **Script:** `scripts/azure/setup-complete-azure-demo.sh` (run from **repo root**).
- **Requires:** `export DATABASE_URL='postgresql+psycopg2://USER:PASS@HOST:5432/DB?sslmode=require'` (URL-encode special chars in password, e.g. `@` → `%40`).
- **Steps [1/9]–[9/9]:** migrations → optional wipe → users → 32 policies → pipelines → `run_demo_day.py` (baseline + predicted, no obs) → `seed_complete_policy_workspace.py` → `run_demo_day.py --skip-seed` (observations) → **canonical row-count report**.
- **Skip flags:** `SKIP_WIPE`, `SKIP_MIGRATIONS`, `SKIP_USERS`, `SKIP_32_POLICIES`, `SKIP_PIPELINES`, `SKIP_POLICY_WORKSPACE`, `SKIP_DEMO_NARRATIVE`, `SKIP_CANONICAL_CHECK` (see script header).
- **Important:** This flow **does not** bulk-load `claims_lines` / `enrollment_records` / `provider_records`. Pipelines are **definitions**; canonical facts need ingestion or `scripts/run_complete_product_flow.py` (local) / product flows.

---

## 3. Fixes already implemented (policy workspace + storage)

These addressed failures during `seed_complete_policy_workspace.py`:

| Issue | Fix |
|--------|-----|
| `policy_changelog.changed_by` FK to `users` | `apps/api/scripts/seed_complete_policy_workspace.py` uses `DEFAULT_USER_ID` instead of random `uuid4()` for `changed_by` / `created_by`. |
| `decisions` insert `can't adapt type 'dict'` | `apps/api/src/uepi_api/storage_decisions.py` — `json.dumps` + `CAST(:decision_json AS jsonb)` on INSERT/UPDATE. |
| `risks.risk_id` NOT NULL, `impact` NOT NULL | `apps/api/src/uepi_api/storage_risks.py` — `risk_id`, `impact`, `_driver_probability` / `_driver_impact_label`. |

---

## 4. Checking if “source” / canonical data is loaded

- **Script:** `scripts/check_canonical_source_data.py` (also invoked as step **[9/9]** of the setup script).
- **Tables reported:** `claims_lines`, `enrollment_records`, `provider_records`, `ingestions`, `datasets` (totals + demo tenant filter).
- **SQL (demo tenant):** `SELECT COUNT(*) FROM claims_lines WHERE tenant_id = '00000000-0000-0000-0000-000000000001';` (and same for `enrollment_records`, `provider_records`).
- **Note:** There is **no** `members` table; member-ish coverage is **`enrollment_records`**.

---

## 5. Where raw / generated files live (conceptual)

| Context | Location |
|---------|-----------|
| Local source drops (daily job loader) | `data/source_data/<tenant-id>/` or `apps/data/source_data/<tenant-id>/`; optional `daily/YYYY-MM-DD/` |
| Local synthetic / product flow | `scripts/run_complete_product_flow.py` → under `apps/api/data/target_data_model/`, `data/synthetic/` |
| Azure Files (if enabled) | App settings: `USE_AZURE_FILE_STORAGE`, `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_FILE_SHARE_NAME` (default share name in code: `healthforesight-data`). Exact storage account name comes from provisioning / Portal. |
| Blob / S3-style | `OBJECT_STORAGE_*` (default bucket name in common config: `uepi-data`). |
| Loaded facts | PostgreSQL tables above — **not** the same as files on disk. |

**Synthetic date range in `run_complete_product_flow.py` (Step 1):** default **`months=36`**, `start_date = now - months*30 days`, `end_date = now` (relative to **run time**).

---

## 6. User goals still open (from prior threads)

- End-to-end: detect source files → load into Postgres via pipelines → policies → general + policy baselines → policy predicted impact → incremental data from “last source date + 1” through today → observations by week/month → objective health / policy verdict.
- **Not fully wired** into `setup-complete-azure-demo.sh` beyond seeds + demo narrative; needs explicit ingestion / generator steps and Azure file/blob layout decisions.

---

## 7. Quick reference paths

| Topic | Path |
|--------|------|
| Azure demo setup | `scripts/azure/setup-complete-azure-demo.sh` |
| Wipe public data | `scripts/wipe_public_application_data.py` |
| Seed users | `scripts/seed_users.py` |
| Policy workspace seed | `apps/api/scripts/seed_complete_policy_workspace.py` |
| Demo day / observations | `scripts/run_demo_day.py` |
| Canonical check | `scripts/check_canonical_source_data.py` |
| Daily load from folders | `apps/api/src/uepi_api/services/daily_pipeline_service.py` |
| Daily job API | `apps/api/src/uepi_api/routers/daily_jobs.py` |
| Canonical models | `apps/api/src/uepi_api/models/canonical_data.py` |
| API settings (Azure Files) | `apps/api/src/uepi_api/config.py` |

---

## 8. Database Viewer & Data Explorer (Azure / DB-only)

- **Database Viewer** (`apps/web/src/pages/DatabaseViewerPage.tsx`): requires `apiClient.get()` — implemented in `apps/web/src/lib/api.ts`. API: `apps/api/src/uepi_api/routers/database_viewer.py` uses `verify_token`, dialect-safe table quoting, `Decimal` JSON, paginated reads.
- **Data Explorer** (`apps/api/.../data_explorer.py`): historically listed **`/app/data/source_data`** (filesystem). With **`USE_FILE_STORAGE = false`**, it now lists **PostgreSQL tables** as virtual files (`__db__/<table>`) for paths `source_data` / `target_data_model`. UI hint in `DataExplorerPage.tsx`.
- **Data Quality** `GET /data-quality/report` may **404** until a report exists in DB or you run validation; `/data-quality/summary` can still return 200.

---

## 9. Redeploy (Azure)

From repo root:

```bash
./scripts/azure/redeploy-all.sh
# ./scripts/azure/redeploy-all.sh --api-only
# ./scripts/azure/redeploy-all.sh --web-only
```

Optional: `RESOURCE_GROUP`, `API_APP_NAME`, `WEB_APP_NAME`, `ACR_NAME`, `SKIP_VERIFY=1`.

---

## 10. How to resume in Cursor

1. Open this file: `docs/CURSOR_SESSION_CONTEXT.md`
2. New chat: say **“Read `docs/CURSOR_SESSION_CONTEXT.md` and continue.”** Then your next task.
3. Keep secrets in **environment variables** or Azure App Service configuration, not in committed files.

Last updated: 2026-03-30 — session handoff for continuity (no secrets stored here).
