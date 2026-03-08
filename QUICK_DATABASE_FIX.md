# Quick Database Fix - Database-Only Mode

## Problem
`docker-compose` command not found, but you need PostgreSQL running for database-only mode.

## Quick Solutions

### Option 1: Try Docker Compose V2 (Most Likely)

If you have Docker Desktop, try the newer syntax:

```bash
docker compose up -d postgres
```

(Note: `docker compose` without hyphen - this is Docker Compose V2)

### Option 2: Use the Helper Script

I've created a script that tries all methods:

```bash
./CHECK_AND_START_POSTGRES.sh
```

This will:
- Check if PostgreSQL is already running
- Try `docker compose` (V2)
- Try `docker-compose` (V1)
- Try `docker run` directly
- Show you what's available

### Option 3: Install Docker Compose

If you need the `docker-compose` command:

```bash
# macOS (Homebrew)
brew install docker-compose
```

### Option 4: Use Docker Run Directly

If Docker is installed but Compose isn't:

```bash
docker run -d \
  --name uepi-postgres \
  -e POSTGRES_USER=uepi \
  -e POSTGRES_PASSWORD=uepi123 \
  -e POSTGRES_DB=uepi \
  -p 5432:5432 \
  -v uepi-postgres-data:/var/lib/postgresql/data \
  postgres:15-alpine
```

### Option 5: Check if PostgreSQL Already Running

PostgreSQL might already be running locally:

```bash
# Test connection
psql -U uepi -d uepi -h localhost -c "SELECT 1;"
```

If this works, you're all set! No need to start anything.

## After PostgreSQL is Running

1. **Test connection:**
   ```bash
   python3 scripts/fix_database_connection.py
   ```

2. **Check if data exists:**
   The diagnostic will show which tables have data

3. **Restart API server:**
   The API should now connect to database successfully

## What You Need

- **Docker** (for containerized PostgreSQL)
- **OR** PostgreSQL installed locally
- **Password**: `uepi123` (already configured ✅)

Try Option 1 first (`docker compose up -d postgres`) - this is the most common case with Docker Desktop!
