# Start PostgreSQL - Alternative Methods

## Option 1: Docker Compose (New Syntax)

If you have Docker but not `docker-compose`, try the newer syntax:

```bash
docker compose up -d postgres
```

(Note: `docker compose` without hyphen - this is the newer Docker Compose V2)

## Option 2: Docker Run Directly

If Docker Compose doesn't work, start PostgreSQL directly:

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

## Option 3: Install Docker Compose

If you need the `docker-compose` command:

### macOS (Homebrew):
```bash
brew install docker-compose
```

### Or use Docker Desktop:
Docker Desktop includes `docker compose` (V2) - just use `docker compose` instead of `docker-compose`

## Option 4: Local PostgreSQL Installation

If you have PostgreSQL installed locally:

```bash
# Create database
createdb uepi

# Set password for user
psql -U postgres -c "CREATE USER uepi WITH PASSWORD 'uepi123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE uepi TO uepi;"
```

Then update config to use local PostgreSQL (usually already configured for localhost:5432)

## Option 5: Check What You Have

Run these to see what's available:

```bash
# Check Docker
docker --version

# Check Docker Compose V2
docker compose version

# Check if PostgreSQL is already running
psql -U uepi -d uepi -h localhost -c "SELECT 1;" 2>&1
```

## Quick Test

Try this first:

```bash
docker compose up -d postgres
```

If that doesn't work, try:

```bash
docker-compose up -d postgres
```

If neither works, use Option 2 (docker run) or Option 4 (local PostgreSQL).
