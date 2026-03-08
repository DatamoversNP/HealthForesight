# Fix Database-Only Mode - All Modules

## Problem
All preconfigured data is not loading because database connection is failing.

## Solution: Fix Database Connection

### Quick Fix

Run this script to start database and verify connection:

```bash
./START_DATABASE_AND_FIX.sh
```

This will:
1. ✅ Check if PostgreSQL is running
2. ✅ Start PostgreSQL if not running
3. ✅ Test database connection
4. ✅ Show which tables have data
5. ✅ Report any issues

### Manual Steps

#### Step 1: Start PostgreSQL

```bash
docker-compose up -d postgres
```

Wait 10-15 seconds for it to start.

#### Step 2: Verify Connection

```bash
python3 scripts/fix_database_connection.py
```

This diagnostic will show:
- ✅ Database connection status
- ✅ All tables in database
- ✅ Record counts for each table
- ✅ Which tables have data vs empty

#### Step 3: Check Data Exists

If database is connected but empty:
- You may need to run migrations
- You may need to import/seed data
- Check if data was migrated from files

#### Step 4: Restart API Server

After database is working, restart API:

```bash
# In API terminal (Ctrl+C to stop, then):
cd apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Current Configuration

- **Database**: PostgreSQL (docker-compose)
- **Password**: `uepi123` (matches config ✅)
- **Mode**: Database-only (all routers use database)
- **Issue**: Connection failing → no data loads

## Expected Result

After fixing:
- ✅ Database connection successful
- ✅ All modules (policies, observations, analyses, pipelines, baselines) load from database
- ✅ Frontend displays all preconfigured data
- ✅ No file storage fallback needed

## Troubleshooting

### "Connection refused"
- PostgreSQL container not running → Run `docker-compose up -d postgres`

### "Password authentication failed"
- Password mismatch → Config already has `uepi123` ✅
- Check if PostgreSQL container was recreated with different password

### "Database has no data"
- Tables exist but empty → Need to import/seed data
- Check if migrations were run
- Check if data migration scripts were executed

### "Table does not exist"
- Migrations not run → Run `alembic upgrade head`
- Or create tables manually

Run the diagnostic script first to see exact status!
