# Fix PostgreSQL Authentication: "no password supplied"

## Problem
PostgreSQL is running but requires a password, and you're trying to connect without one.

## Solutions

### Solution 1: Use postgres Superuser (Easiest)

The `postgres` superuser is created by default. Try connecting as `postgres`:

```bash
# Test connection
psql -U postgres -d postgres

# If that works, create database
psql -U postgres -d postgres -c "CREATE DATABASE uepi_db;"

# Then use postgres user in DATABASE_URL
export DATABASE_URL="postgresql://postgres@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"
cd apps/api
python3 scripts/create_db_simple.py
```

### Solution 2: Set Password for Your User

```bash
# Connect as postgres user
psql -U postgres -d postgres

# Set password for your user (replace 'nilesh' with your username)
ALTER USER nilesh WITH PASSWORD 'yourpassword';

# Or create user with password
CREATE USER nilesh WITH PASSWORD 'yourpassword' CREATEDB;

# Exit
\q

# Then use password in DATABASE_URL
export DATABASE_URL="postgresql://nilesh:yourpassword@localhost:5432/uepi_db"
```

### Solution 3: Configure Trust Authentication (No Password)

Edit PostgreSQL's `pg_hba.conf` file to allow passwordless local connections:

```bash
# Find pg_hba.conf location
psql -U postgres -d postgres -c "SHOW hba_file;"

# Edit the file (usually in /opt/homebrew/var/postgresql@15/ or similar)
# Add these lines at the top:
# host    all             all             127.0.0.1/32            trust
# host    all             all             ::1/128                 trust

# Restart PostgreSQL
brew services restart postgresql@15
```

### Solution 4: Use Empty Password

Some PostgreSQL installations allow empty password for local connections:

```bash
# Set empty password
psql -U postgres -d postgres -c "ALTER USER nilesh WITH PASSWORD '';"

# Then use empty password in connection string
export DATABASE_URL="postgresql://nilesh:@localhost:5432/uepi_db"
```

### Solution 5: Create Database First, Then Connect

```bash
# Create database using postgres user
psql -U postgres -d postgres -c "CREATE DATABASE uepi_db;"

# Grant permissions
psql -U postgres -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE uepi_db TO nilesh;"

# Then try connecting
export DATABASE_URL="postgresql://nilesh@localhost:5432/uepi_db"
```

## Quick Test

Test which user works:

```bash
# Test 1: postgres user
psql -U postgres -d postgres -c "SELECT 1;"

# Test 2: Your username
psql -U nilesh -d postgres -c "SELECT 1;"

# Test 3: Your username with database
psql -U nilesh -d uepi_db -c "SELECT 1;"
```

## Recommended: Use postgres User

The easiest solution is to use the `postgres` superuser:

```bash
# 1. Create database
psql -U postgres -d postgres -c "CREATE DATABASE uepi_db;"

# 2. Set DATABASE_URL
export DATABASE_URL="postgresql://postgres@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# 3. Create tables
cd apps/api
python3 scripts/create_db_simple.py
```

## Find PostgreSQL Config

```bash
# Find data directory
psql -U postgres -d postgres -c "SHOW data_directory;"

# Find config file
psql -U postgres -d postgres -c "SHOW config_file;"

# Find hba_file (authentication config)
psql -U postgres -d postgres -c "SHOW hba_file;"
```

