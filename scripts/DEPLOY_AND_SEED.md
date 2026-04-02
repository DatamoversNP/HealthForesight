# Deployment and user seed

## Complete deployment (recommended – same links, all components)

For **full deployment** (API + Frontend + CORS + migrations + user seed) on the same URLs as before, see:

- **[docs/COMPLETE_DEPLOYMENT.md](../docs/COMPLETE_DEPLOYMENT.md)** – Prerequisites, one-command deploy, and troubleshooting.
- **One command:**  
  `export DATABASE_URL="postgresql://..."; ./scripts/azure/deploy-complete-full.sh`

---

## Final deployment (alternative)

From the **repo root**, with **DATABASE_URL** set to your Azure PostgreSQL connection string (so migrations and seed run against the same DB as the API):

```bash
export DATABASE_URL="postgresql://user:password@your-server.postgres.database.azure.com:5432/yourdb?sslmode=require"
./scripts/azure/final-deploy.sh
```

This will:

1. Deploy the API to Azure App Service  
2. Deploy the frontend to Azure (Static Web App or App Service)  
3. Run `alembic upgrade head` (migrations)  
4. Run the user seed script (creates/updates users with password **Swan@1234**)

To skip migrations or seed:

```bash
SKIP_MIGRATIONS=1 ./scripts/azure/final-deploy.sh   # no migrations
SKIP_SEED=1 ./scripts/azure/final-deploy.sh        # no user seed
SKIP_MIGRATIONS=1 SKIP_SEED=1 ./scripts/azure/final-deploy.sh   # deploy only
```

If **DATABASE_URL** is not set, the script only deploys (steps 3 and 4 are skipped). You can run migrations and seed later (see below).

---

## Seeded users (password for all: **Swan@1234**)

| Email | Name | Roles |
|-------|------|--------|
| demo@example.com | Demo User | POLICY_ADMIN, UM_LEADER |
| admin@healthforesight.com | Admin User | POLICY_ADMIN |
| sarah.analyst@healthforesight.com | Sarah Analyst | ACTUARIAL |
| mike.leader@healthforesight.com | Mike UM Leader | UM_LEADER |
| jane.exec@healthforesight.com | Jane Executive | EXEC_VIEWER |
| david.compliance@healthforesight.com | David Compliance | COMPLIANCE |

After deployment, sign in via **POST /api/v1/auth/login** with `{"email": "<email>", "password": "Swan@1234"}` and use the returned `access_token` as `Authorization: Bearer <token>`.

---

## Run seed only (e.g. after first deploy without DATABASE_URL)

From **repo root**:

```bash
export DATABASE_URL="postgresql://..."
PYTHONPATH=apps/api/src:packages/common/src python3 scripts/seed_users.py
```

---

## Run migrations only

```bash
cd apps/api
export DATABASE_URL="postgresql://..."
alembic upgrade head
```
