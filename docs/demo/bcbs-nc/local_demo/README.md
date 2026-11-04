# Local Data Voyager demo stack (ports 7867+)

## Ports

| Port | Service |
|------|---------|
| **7867** | API (uvicorn, local process) |
| **7868** | Web — Data Voyager branding (Vite) |
| **7870** | Redis (`uepi-demo-redis` docker) |

**UI:** http://localhost:7868  
**API docs:** http://localhost:7867/docs  

Login: `admin@healthforesight.com` / (same demo password as production)

## What this stack is

- **Local UI + local API process**, talking to the **Azure Postgres** that already has the BCBS NC / MRI demo data (so MRI policy, observation `b227220e-…`, verdicts match the script).
- Redis is local on **7870**. File storage is local under `data/demo7867/` (Azure `STORAGE_PATH` is overridden — do not use `/home/site/...` on Mac).

This is **not** a fully offline local DB. Expect ~1–3s API calls after warm; first loads can be slower than a pure local DB, but better than cold Vercel + cold API for UI assets.

## Start / restart

```bash
./docs/demo/bcbs-nc/local_demo/start_demo7867.sh
```

Or keep long-lived shells (recommended so processes are not culled):

1. API on 7867 with `.env.demo7867` loaded + `STORAGE_PATH` → `data/demo7867`
2. Web: `cd apps/web && npm run dev -- --config vite.config.demo7867.ts --port 7868`
3. Optional worker: celery with `--pool=solo` and `REDIS_URL=redis://127.0.0.1:7870/0`

## Demo path (after warm)

1. Off-camera: walk once Executive → MRI policy → Baseline → Predict → Observe → What-If → Verdict → Executive; wait for each screen to populate.
2. **Do not hard-refresh.** Reuse the same browser session.
3. On-camera / live: walk the same path again, narration pace.

Warm Chromium profile (if used): `docs/demo/bcbs-nc/local_demo/chromium_warm`

## Fallback

If local API misbehaves, open warmed **https://data-voyager.vercel.app** and use the same double-walk pattern.

To point local UI at Azure API instead of :7867, set in `apps/web/vite.config.demo7867.ts`:

```ts
proxy: { '/api': { target: 'https://healthforesight-api.azurewebsites.net', changeOrigin: true, secure: true } }
```

## Secrets

`.env.demo7867` is local-only (gitignored via `.env*`). Do not commit it.

## Current recommended mode (as of setup)

**Local Data Voyager UI on :7868 → Azure API** (vite proxy).

Reason: local uvicorn + Azure Postgres works for short calls but can stall under multi-request warm; Azure App Service API is more reliable for a live walkthrough while still giving local DV branding and no Vercel cold UI.

To switch back to local API (`:7867`), set vite proxy target to `http://127.0.0.1:7867` and restart web.
