# Finding pg_hba.conf File

If the automated scripts can't find `pg_hba.conf`, try these methods:

## Method 1: Query PostgreSQL Directly

```bash
# Add PostgreSQL to PATH
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"

# Get the exact location
psql -U postgres -d postgres -c "SHOW hba_file;"
```

This will show the exact path to `pg_hba.conf`.

## Method 2: Check Data Directory

```bash
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
psql -U postgres -d postgres -c "SHOW data_directory;"
```

Then check: `{data_directory}/pg_hba.conf`

## Method 3: Common Homebrew Locations

Check these locations manually:

```bash
# Intel Mac
ls -la /usr/local/var/postgresql@15/pg_hba.conf

# Apple Silicon Mac
ls -la /opt/homebrew/var/postgresql@15/pg_hba.conf

# Alternative location
ls -la ~/Library/Application\ Support/Postgres/var-15/pg_hba.conf
```

## Method 4: Search System

```bash
# Search for the file
find /usr/local/var -name "pg_hba.conf" 2>/dev/null
find /opt/homebrew/var -name "pg_hba.conf" 2>/dev/null
find ~/Library -name "pg_hba.conf" 2>/dev/null
```

## Once You Find It

1. **Backup the file:**
   ```bash
   cp /path/to/pg_hba.conf /path/to/pg_hba.conf.backup
   ```

2. **Edit the file** (add these lines at the TOP, before other rules):
   ```
   # Trust authentication for local development
   host    all             all             127.0.0.1/32            trust
   host    all             all             ::1/128                 trust
   ```

3. **Restart PostgreSQL:**
   ```bash
   brew services restart postgresql@15
   ```

4. **Test connection:**
   ```bash
   export DATABASE_URL="postgresql://postgres@localhost:5432/postgres"
   export USE_FILE_STORAGE="false"
   python3 apps/api/scripts/create_db_direct.py
   ```

## Alternative: Use Password Instead

If you can't find or edit `pg_hba.conf`, set a password:

```bash
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
psql -U postgres -d postgres
```

In psql:
```sql
ALTER USER postgres WITH PASSWORD 'yourpassword';
\q
```

Then use:
```bash
export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/postgres"
export USE_FILE_STORAGE="false"
python3 apps/api/scripts/create_db_direct.py
```

