# Running Database Migrations

## Issue: Alembic Not Found

If you get `command not found: alembic`, you need to install Alembic first.

## Solution

### Step 1: Install Dependencies

```bash
# Install Alembic and psycopg2-binary
pip3 install alembic psycopg2-binary
```

Or install all dependencies:

```bash
cd apps/api
pip3 install -r requirements.txt
```

### Step 2: Set Environment Variables

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"
```

**Important:** Replace `user:password@localhost:5432/uepi_db` with your actual PostgreSQL credentials.

### Step 3: Run Migrations

**Option A: Using Alembic (Recommended)**

```bash
cd apps/api
alembic upgrade head
```

**Option B: If Alembic command not found, use Python module**

```bash
cd apps/api
python3 -m alembic upgrade head
```

**Option C: Using init_db() directly (No Alembic needed)**

```bash
cd apps/api
python3 -c "
import sys
import os
os.environ['USE_FILE_STORAGE'] = 'false'
sys.path.insert(0, 'src')
sys.path.insert(0, '../../packages/common/src')
from uepi_api.database import init_db
init_db()
print('✅ Database tables created!')
"
```

## Verify Database Creation

After running migrations, verify tables were created:

```bash
# Connect to PostgreSQL
psql -U user -d uepi_db

# List all tables
\dt

# Count tables (should be 55)
SELECT count(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
```

## Troubleshooting

### Error: "No module named 'alembic'"
- Install Alembic: `pip3 install alembic`

### Error: "No module named 'psycopg2'"
- Install psycopg2-binary: `pip3 install psycopg2-binary`

### Error: "Connection refused" or "could not connect"
- Check PostgreSQL is running: `pg_isready` or `psql -U postgres -c "SELECT 1"`
- Verify DATABASE_URL is correct
- Check firewall/network settings

### Error: "database 'uepi_db' does not exist"
- Create database first: `createdb -U user uepi_db`
- Or connect to PostgreSQL and run: `CREATE DATABASE uepi_db;`

### Error: "File storage is enabled"
- Make sure `USE_FILE_STORAGE="false"` is set
- Check it's exported: `echo $USE_FILE_STORAGE`

## Quick One-Liner

If you have all dependencies installed:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db" && \
export USE_FILE_STORAGE="false" && \
cd apps/api && \
alembic upgrade head
```

