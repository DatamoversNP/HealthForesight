# Why Timeouts Are Happening (It's NOT About Data Volume)

## The Real Problem

Timeouts are happening because **the database connection itself is failing or hanging**, not because of data volume. Even with small data, if PostgreSQL isn't running or the connection can't be established, every request will timeout.

## Root Causes

### 1. **PostgreSQL Not Running** (Most Likely)
The database server might not be running at all. When the API tries to connect, it hangs waiting for a response that never comes.

**Check:**
```bash
ps aux | grep postgres
# Should show postgres processes running
```

**Fix:**
```bash
# Start PostgreSQL (method depends on your setup)
# If using Docker:
docker-compose up -d postgres
# OR
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15

# If installed locally:
brew services start postgresql@15  # macOS
# OR
sudo systemctl start postgresql    # Linux
```

### 2. **Wrong Connection String**
The connection string in `packages/common/src/uepi_common/config.py` is:
```
postgresql://postgres:postgres@localhost:5432/uepi_db
```

**Check if this matches your actual setup:**
- **Host:** `localhost` (is PostgreSQL on localhost?)
- **Port:** `5432` (is PostgreSQL listening on this port?)
- **User:** `postgres` (does this user exist?)
- **Password:** `postgres` (is this the correct password?)
- **Database:** `uepi_db` (does this database exist?)

**Test connection manually:**
```bash
psql -h localhost -U postgres -d uepi_db
# Enter password when prompted
```

### 3. **Connection Attempt Hanging**
Even with timeouts configured, the initial connection attempt might hang if:
- PostgreSQL is running but not accepting connections
- Firewall is blocking port 5432
- PostgreSQL is configured to reject connections from localhost

**Check PostgreSQL logs:**
```bash
# Find PostgreSQL log location
# macOS (Homebrew):
tail -f /usr/local/var/log/postgres.log
# OR
tail -f /opt/homebrew/var/log/postgres.log

# Linux:
tail -f /var/log/postgresql/postgresql-*.log
```

### 4. **Connection Pool Exhausted**
If connections aren't being closed properly, the pool might be exhausted, causing new connections to wait indefinitely.

## Why It Times Out at Exactly 10 Seconds

The frontend timeout is 10 seconds. When the API tries to connect to the database:
1. Connection attempt starts
2. Database doesn't respond (not running or unreachable)
3. Connection hangs (waiting for response)
4. Frontend timeout (10 seconds) triggers
5. Request fails with "timeout of 10000ms exceeded"

**This has NOTHING to do with data volume** - it's a connection issue.

## Quick Diagnostic Steps

### Step 1: Check if PostgreSQL is Running
```bash
ps aux | grep postgres
```
If nothing shows up, PostgreSQL is not running.

### Step 2: Test Connection Manually
```bash
psql -h localhost -U postgres -d uepi_db
```
If this hangs or fails, the connection string is wrong or PostgreSQL isn't accessible.

### Step 3: Check if Port 5432 is Listening
```bash
lsof -i :5432
# OR
netstat -an | grep 5432
```
If nothing shows up, PostgreSQL isn't listening on port 5432.

### Step 4: Check API Server Logs
Look for database connection errors in the API server logs:
```
WARNING: Database connection failed/timed out in get_demo_current_user: ...
```

## Solution

### Option 1: Start PostgreSQL
If PostgreSQL isn't running, start it using your preferred method (Docker, Homebrew, systemd, etc.)

### Option 2: Update Connection String
If PostgreSQL is running but with different credentials, update `packages/common/src/uepi_common/config.py`:
```python
url: str = "postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE"
```

### Option 3: Use Environment Variable
Set `DATABASE_URL` environment variable to override the default:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
```

## Why Our Timeout Fixes Help

Even with the fixes:
- **Connection timeout (10s)**: If PostgreSQL isn't running, connection will fail after 10 seconds
- **Query timeout (30s)**: If connection works but query hangs, it will fail after 30 seconds
- **Frontend timeout (60s)**: Frontend waits long enough for connection + query to complete or fail

But if PostgreSQL isn't running at all, **the connection will still fail** - it just fails faster now (10 seconds instead of hanging indefinitely).

## Next Steps

1. **Check if PostgreSQL is running**
2. **If not, start it**
3. **Test connection manually with `psql`**
4. **Restart API server**
5. **Refresh frontend**

The timeouts will stop once PostgreSQL is running and accessible.
