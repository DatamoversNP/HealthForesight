# ⚠️ Configuration Mismatch Found

## The Issue

There's a **mismatch** between `docker-compose.yml` and the default config:

### docker-compose.yml (PostgreSQL container)
- **User:** `uepi`
- **Password:** `uepi123`
- **Database:** `uepi`

### config.py (Default value)
- **User:** `postgres`
- **Password:** `postgres`
- **Database:** `uepi_db`

## Why This Causes Timeouts

When the API tries to connect using the default config (`postgres:postgres@localhost:5432/uepi_db`), but PostgreSQL is running with different credentials (`uepi:uepi123@localhost:5432/uepi`), the connection fails or hangs.

## Solution

### Option 1: Use Environment Variable (Recommended)

Create a `.env` file in the project root:

```bash
# Match docker-compose.yml credentials
DATABASE_URL=postgresql://uepi:uepi123@localhost:5432/uepi
```

### Option 2: Update docker-compose.yml

Change docker-compose.yml to match the default config:

```yaml
environment:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: uepi_db
```

### Option 3: Update Default Config

Change `packages/common/src/uepi_common/config.py` to match docker-compose:

```python
url: str = "postgresql://uepi:uepi123@localhost:5432/uepi"
```

## Recommended Approach

**Use `.env` file** - This keeps credentials out of code and allows different configs for different environments:

1. Copy `.env.example` to `.env`
2. Update `DATABASE_URL` to match your PostgreSQL setup
3. Add `.env` to `.gitignore` (already done)
4. Never commit `.env` files

## How to Check Current Configuration

The configuration is loaded in this order (highest to lowest priority):

1. **Environment variables** (`DATABASE_URL`)
2. **`.env` file** (if exists)
3. **Default value** in `config.py`

To see what's actually being used, check the API logs on startup.

## Quick Fix

If using docker-compose, create `.env` file:

```bash
echo "DATABASE_URL=postgresql://uepi:uepi123@localhost:5432/uepi" > .env
```

Then restart the API server.
