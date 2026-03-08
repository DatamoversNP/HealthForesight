# Fix Database Connection - Database-Only Mode

## Problem
All preconfigured data is not loading because:
1. Database connection is failing (password authentication error)
2. All routers are configured for database-only mode
3. Data was migrated to database but database is not accessible

## Solution: Fix Database Connection

### Step 1: Check Database Status

```bash
# Check if PostgreSQL container is running
docker-compose ps

# If not running, start it
docker-compose up -d postgres
```

### Step 2: Verify Database Configuration

Run the diagnostic script:

```bash
python3 scripts/fix_database_connection.py
```

This will:
- Check database connection
- Verify password matches docker-compose.yml
- List all tables
- Count records in each table
- Show which tables have data

### Step 3: Fix Password Mismatch (if needed)

The config should use password `uepi123` (from docker-compose.yml).

If the diagnostic shows password mismatch:
1. Check `packages/common/src/uepi_common/config.py` - should have `password="uepi123"`
2. Restart API server after fixing

### Step 4: Verify Data Exists

If database is connected but has no data:
1. Check if migrations were run
2. Check if data was imported
3. Run data loading scripts if needed

### Step 5: Restart API Server

After fixing database connection:

```bash
# In API terminal, restart (Ctrl+C then):
cd apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Expected Result

After fixing:
- ✅ Database connection successful
- ✅ All modules can access database
- ✅ Policies, observations, analyses, pipelines, etc. all load from database
- ✅ Frontend displays all preconfigured data

## Current Status

- **Database**: PostgreSQL (docker-compose)
- **Password**: Should be `uepi123`
- **Mode**: Database-only (no file fallback)
- **Issue**: Connection failing due to password/auth error

Run the diagnostic script first to see exact status!
