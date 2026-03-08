# Local Development Setup Guide

## Quick Start for Local PostgreSQL

### Step 1: Check Your Local PostgreSQL Setup

The default configuration expects:
- **User:** `postgres`
- **Password:** `postgres` (or no password for local trust)
- **Database:** `uepi_db`
- **Host:** `localhost`
- **Port:** `5432`

### Step 2: Create .env File

Create a `.env` file in the project root:

```bash
# For local PostgreSQL (most common)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uepi_db
```

### Step 3: Verify PostgreSQL is Running

```bash
# Check if PostgreSQL is running
ps aux | grep postgres

# Or check if port 5432 is listening
lsof -i :5432
```

### Step 4: Create Database (if needed)

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE uepi_db;

# Exit
\q
```

### Step 5: Restart API Server

The API will automatically load the `.env` file on startup.

## Common Local PostgreSQL Setups

### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Default connection (no password usually)
DATABASE_URL=postgresql://$(whoami)@localhost:5432/uepi_db
```

### Linux (apt)

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql

# Default connection
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uepi_db
```

### Docker Compose (Local)

If you're using `docker-compose.yml`:

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Use this in .env
DATABASE_URL=postgresql://uepi:uepi123@localhost:5432/uepi
```

## Troubleshooting

### "Connection Refused"
- PostgreSQL is not running
- Start it: `brew services start postgresql@15` (macOS) or `sudo systemctl start postgresql` (Linux)

### "Authentication Failed"
- Wrong username/password
- Check your PostgreSQL users: `psql -U postgres -c "\du"`
- Update `.env` with correct credentials

### "Database Does Not Exist"
- Create it: `createdb uepi_db` or `psql -U postgres -c "CREATE DATABASE uepi_db;"`

### "Permission Denied"
- PostgreSQL might be configured for peer authentication
- Try: `DATABASE_URL=postgresql://$(whoami)@localhost:5432/uepi_db` (no password)

## Configuration Priority

1. **Environment Variable** - `DATABASE_URL` (highest priority)
2. **`.env` File** - Created in project root
3. **Default Value** - In `config.py` (fallback)

## Next Steps

1. Create `.env` file with your local PostgreSQL credentials
2. Ensure PostgreSQL is running
3. Create database if it doesn't exist
4. Restart API server
5. Test connection - requests should no longer timeout
