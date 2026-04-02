# Login returns 503

## HTML body: `Application Error` / `:(` (Azure page)

If the response **body is HTML** (not JSON `{"detail":...}`), **FastAPI is not answering**. Azure’s front end is returning **503** because the **API app process crashed, never started, or isn’t listening on `PORT`**.

**Fix on `healthforesight-api` (not CORS / not the web app):**

1. **Azure Portal** → App Service → **Log stream** (or **Diagnose and solve problems** → the link in the error page). Look for Python tracebacks or **container exit**.
2. **Configuration → General settings**
   - **Startup Command** must be **empty** for **Docker** deployments (a leftover `startup.sh` / Oryx command will crash the container).

3. **Port mismatch** — The container must listen on the port Azure forwards to. This repo sets **`WEBSITES_PORT=8080`** and `docker-entrypoint.sh` uses **`${WEBSITES_PORT:-${PORT:-8080}}`** so listen port matches. If you change one, change both.
4. **Lifespan / file logging** — If startup opens log files under a **read-only** path (common under `/app` on Linux containers), **lifespan can fail before Uvicorn binds** → HTML 503. Detection uses **`WEBSITE_SITE_NAME` / `WEBSITE_HOSTNAME`** (not `WEBSITE_INSTANCE_ID`, which is often **unset** in Web App for Containers). File logging is **off** on Azure unless **`UEPI_ENABLE_FILE_LOG=1`**. Logs go to **Log stream** (stdout).

5. **Application settings**
   - **`DATABASE_URL`** must start with `postgresql://` or `postgresql+psycopg2://`. A wrong scheme or empty value can cause **`ValueError` at import** → app never binds → HTML 503.
6. **Restart** the API app after changes.

Quick probe (should return **JSON**, not HTML):

```bash
curl -sS -D - "https://healthforesight-api.azurewebsites.net/api/v1/ping" | head -30
```

---

`/auth/login` hits **PostgreSQL**. `/api/v1/ping` does **not**. So you can see a healthy API but login still fails if the DB is unreachable.

## 1. Is the API reachable at all?

Open (via your **web** URL, same as the app):

1. `https://healthforesight-web.azurewebsites.net/api/v1/ping` → should be `{"ok":true,...}`  
   - **503 here** → API app or proxy is down; fix **healthforesight-api** / **API_BACKEND_URL** / restart.

2. `https://healthforesight-web.azurewebsites.net/api/v1/health/detailed` → always **200** JSON; read **`database`**:  
   - **`connected`** → DB OK; login 401 = wrong user/password or not seeded.  
   - **`timeout`** or **`error:`** → fix **DATABASE_URL** + PostgreSQL firewall (below).

## 2. Azure API app (`healthforesight-api`)

1. **Configuration → Application settings**
   - **`DATABASE_URL`** = full PostgreSQL URL, e.g.  
     `postgresql://USER:PASSWORD@HOST.postgres.database.azure.com:5432/DBNAME?sslmode=require`

2. **PostgreSQL firewall**
   - Azure Portal → your PostgreSQL server → **Networking**
   - Enable **“Allow public access from Azure services”** *or* add the API app’s **outbound IPs** (App Service → **Properties** → **Outbound IP addresses**).

3. **Users table**
   - Run migrations and seed (so a local user with `password_hash` exists).  
     Example: `scripts/azure/deploy-complete-full.sh` DB steps, or your team’s seed script.

4. **Restart** the API app after changing settings.

## 3. Test login directly (bypasses browser)

```bash
curl -sS -X POST "https://healthforesight-api.azurewebsites.net/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"YOUR_SEEDED_EMAIL","password":"YOUR_PASSWORD"}'
```

- **503** with **HTML** → see [HTML body](#html-body-application-error--azure-page) above (platform / crash / startup).
- **503** with a JSON `detail` about database → fix `DATABASE_URL` / firewall / migrations.
- **401** → wrong credentials or user not seeded.
- **200** + `access_token` → API is fine; if the site still fails, check the web proxy `API_BACKEND_URL`.

## 4. If response is 503 with no JSON body

Often **Azure** (app not running, scale-out, gateway). Check **Log stream** on **healthforesight-api** and restart the app.

**CLI (optional):**

```bash
az webapp log tail --name healthforesight-api --resource-group healthforesight-rg
```
