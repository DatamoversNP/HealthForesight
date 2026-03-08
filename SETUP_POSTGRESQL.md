# PostgreSQL Setup Guide

## Error: Password Authentication Failed

You're using placeholder credentials (`user:password`). You need to use your actual PostgreSQL credentials.

## Find Your PostgreSQL Credentials

### Option 1: Check if PostgreSQL is installed

```bash
# Check if PostgreSQL is running
pg_isready

# Or check version
psql --version
```

### Option 2: Common Default Credentials

**macOS Homebrew PostgreSQL:**
```bash
# Usually uses your macOS username, no password
export DATABASE_URL="postgresql://$(whoami)@localhost:5432/uepi_db"
```

**Default PostgreSQL installation:**
```bash
# Common defaults:
# Username: postgres
# Password: (check your PostgreSQL setup)
export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/uepi_db"
```

**Docker PostgreSQL:**
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
```

### Option 3: Test Connection First

```bash
# Test with psql command line
psql -U postgres -d postgres

# Or with your username
psql -U $(whoami) -d postgres

# If that works, use the same credentials in DATABASE_URL
```

## Create Database

If the database `uepi_db` doesn't exist, create it:

```bash
# Using psql
psql -U postgres -c "CREATE DATABASE uepi_db;"

# Or connect and create
psql -U postgres
CREATE DATABASE uepi_db;
\q
```

## Test Connection Script

I've created a test script to verify your credentials:

```bash
export DATABASE_URL="postgresql://your_username:your_password@localhost:5432/uepi_db"
cd apps/api
python3 scripts/test_db_connection.py
```

## Once Connection Works

After the test script succeeds, create the tables:

```bash
export DATABASE_URL="postgresql://your_username:your_password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"
python3 scripts/create_db_simple.py
```

## Install PostgreSQL (if not installed)

**macOS:**
```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb uepi_db
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb uepi_db
```

**Docker:**
```bash
docker run --name postgres-uepi \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=uepi_db \
  -p 5432:5432 \
  -d postgres:15

# Then use:
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
```

## Quick Setup (macOS with Homebrew)

```bash
# 1. Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# 2. Create database
createdb uepi_db

# 3. Set DATABASE_URL (usually no password needed on macOS)
export DATABASE_URL="postgresql://$(whoami)@localhost:5432/uepi_db"

# 4. Test connection
cd apps/api
python3 scripts/test_db_connection.py

# 5. Create tables
export USE_FILE_STORAGE="false"
python3 scripts/create_db_simple.py
```

