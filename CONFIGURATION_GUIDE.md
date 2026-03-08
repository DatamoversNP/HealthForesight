# Configuration Guide

## Database Connection String

The database connection string is **NOT hardcoded**. It uses environment variables with sensible defaults for local development.

### How It Works

1. **Environment Variables (Highest Priority)**
   - Set `DATABASE_URL` environment variable
   - Example: `export DATABASE_URL="postgresql://user:pass@host:port/db"`

2. **`.env` File (Second Priority)**
   - Create a `.env` file in the project root
   - Add: `DATABASE_URL=postgresql://user:pass@host:port/db`
   - The `.env` file is automatically loaded by `pydantic-settings`

3. **Default Value (Fallback)**
   - Only used if no environment variable or `.env` file is found
   - Default: `postgresql://postgres:postgres@localhost:5432/uepi_db`
   - **This is for local development only**

### Configuration Source

The configuration is defined in `packages/common/src/uepi_common/config.py`:

```python
class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATABASE_", extra="ignore")
    
    url: str = "postgresql://postgres:postgres@localhost:5432/uepi_db"  # Default only
```

The `env_prefix="DATABASE_"` means:
- `DATABASE_URL` → `url` field
- `DATABASE_POOL_SIZE` → `pool_size` field
- `DATABASE_MAX_OVERFLOW` → `max_overflow` field
- `DATABASE_ECHO` → `echo` field

### How to Configure

#### Option 1: Environment Variable (Recommended for Production)
```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

#### Option 2: `.env` File (Recommended for Development)
Create `.env` file in project root:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uepi_db
```

#### Option 3: Docker Compose
Set in `docker-compose.yml`:
```yaml
services:
  api:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/uepi_db
```

### Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment variables in production** - Set via deployment platform
3. **Use secrets management** - Azure Key Vault, AWS Secrets Manager, etc.
4. **Rotate credentials regularly** - Change database passwords periodically

### Current Configuration

To see what configuration is being used, check the API logs on startup. The database URL is logged (password is masked for security).

### Example: Different Environments

**Development (.env file):**
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uepi_db
```

**Staging (Environment Variable):**
```bash
export DATABASE_URL="postgresql://staging_user:staging_pass@staging-db.example.com:5432/uepi_staging"
```

**Production (Azure App Service):**
```bash
# Set in Azure Portal → Configuration → Application Settings
DATABASE_URL=postgresql://prod_user:${SECRET_PASSWORD}@prod-db.example.com:5432/uepi_prod
```

### Verification

To verify which configuration is being used:

1. **Check environment variables:**
   ```bash
   echo $DATABASE_URL
   ```

2. **Check API logs** - Database connection string is logged (password masked)

3. **Test connection:**
   ```bash
   python3 scripts/test_db_connection.py
   ```

### Troubleshooting

If connection fails:
1. Check if `DATABASE_URL` environment variable is set
2. Check if `.env` file exists and has correct values
3. Verify PostgreSQL is running and accessible
4. Test connection manually: `psql $DATABASE_URL`
