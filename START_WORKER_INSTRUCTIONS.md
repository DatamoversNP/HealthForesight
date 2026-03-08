# How to Start the Worker Service

## Prerequisites

The worker service needs:
1. ✅ **Celery** - Already installed
2. ❌ **Redis** - Needs to be running

## Step 1: Start Redis

### Option A: Using Homebrew (macOS)
```bash
# Install Redis (if not installed)
brew install redis

# Start Redis
brew services start redis

# Or run Redis in foreground
redis-server
```

### Option B: Using Docker
```bash
docker run -d -p 6379:6379 redis:latest
```

### Option C: Check if Redis is already running
```bash
redis-cli ping
# Should return: PONG
```

## Step 2: Start the Worker

Once Redis is running, start the worker:

```bash
cd apps/worker
./start_worker.sh
```

Or manually:
```bash
cd apps/worker
export PYTHONPATH="$(pwd)/src:$(pwd)/../../packages/common/src:$(pwd)/../../apps/api/src"
celery -A uepi_worker.main.app worker --loglevel=info
```

## What Happens Next

1. Worker starts and connects to Redis
2. Worker begins processing the 38 pending analyses
3. Analyses change status: PENDING → RUNNING → COMPLETED
4. Observation monitor detects completion (checks every 30 seconds)
5. Observations are created automatically
6. You see results in the UI!

## Verify It's Working

### Check Worker Status
```bash
# In another terminal, check if worker is processing
cd apps/api/scripts
./check_status.sh
```

### Watch Monitor Log
```bash
tail -f /tmp/observation_monitor.log
```

You should see:
- Worker processing analyses
- Status changing from PENDING to COMPLETED
- Monitor creating observations automatically

## Troubleshooting

### Redis Connection Error
- Make sure Redis is running: `redis-cli ping`
- Check Redis URL in environment variables or config

### Import Errors
- Make sure PYTHONPATH includes worker src and common packages
- Check that all dependencies are installed

### Worker Not Processing Jobs
- Check Redis is accessible
- Verify Celery can connect to Redis
- Check worker logs for errors

## Summary

**Quick Start:**
```bash
# 1. Start Redis
brew services start redis  # or redis-server

# 2. Start Worker
cd apps/worker
./start_worker.sh

# 3. Monitor Progress
cd apps/api/scripts
./check_status.sh
```

Once the worker is running, everything else is automatic! 🎉
