# Quick Fix: PostgreSQL Password Authentication

## Problem
PostgreSQL requires a password, but you're connecting without one.

## Solution 1: Configure Trust Authentication (Easiest for Local Dev)

This allows passwordless connections from localhost:

```bash
# Run the configuration script
cd apps/api
./scripts/configure_postgres_auth.sh

# This will:
# 1. Edit pg_hba.conf to allow trust authentication
# 2. Restart PostgreSQL
# 3. Allow passwordless connections from localhost

# Then try again:
export DATABASE_URL="postgresql://postgres@localhost:5432/postgres"
export USE_FILE_STORAGE="false"
python3 scripts/create_db_direct.py
```

## Solution 2: Set a Password for postgres User

```bash
# Option A: Use the script
cd apps/api
python3 scripts/set_postgres_password.py

# Option B: Manual (if you can connect)
# Add PostgreSQL to PATH first:
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"

# Connect and set password
psql -U postgres -d postgres
ALTER USER postgres WITH PASSWORD 'yourpassword';
\q

# Then use password in connection
export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/postgres"
```

## Solution 3: Use Your macOS Username

Sometimes your macOS username works without password:

```bash
# Try with your username
export DATABASE_URL="postgresql://nilesh@localhost:5432/postgres"
export USE_FILE_STORAGE="false"
python3 scripts/create_db_direct.py
```

## Solution 4: Find PostgreSQL Config and Edit Manually

```bash
# Find config file location
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
psql -U postgres -d postgres -c "SHOW hba_file;"

# Edit the file and add these lines at the top:
# host    all             all             127.0.0.1/32            trust
# host    all             all             ::1/128                 trust

# Restart PostgreSQL
brew services restart postgresql@15
```

## Recommended: Solution 1 (Trust Authentication)

For local development, trust authentication is the simplest:

```bash
cd apps/api
./scripts/configure_postgres_auth.sh
```

Then you can connect without passwords for local development.

