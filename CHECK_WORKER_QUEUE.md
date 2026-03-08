# Checking Worker Queue Status

## Issue: Many Worker Processes

You have **20+ Celery worker processes** running, which is unusual. This might indicate:
- Worker was started multiple times
- Worker processes are spawning too many children

## The Real Problem

The 38 analyses are still **PENDING** even though the worker is running. This means:
- The analyses were created in the database
- But they were **NOT queued to Celery** (because worker wasn't running when they were created)
- The worker only processes tasks that are in the Celery queue

## Solution: Re-queue the Analyses

The analyses need to be manually queued to Celery. Since they were created before the worker was running, they're stuck in the database but not in the queue.

### Option 1: Create New Analyses (Easiest)

Create new impact analyses via the UI or API - they'll be queued immediately and processed:

```bash
# New analyses will be automatically queued and processed
```

### Option 2: Check if Worker is Actually Processing

The worker might be processing but there are no tasks in the queue. Check:

```bash
# Check Redis queue
redis-cli LLEN celery

# Check worker logs (if you can see them)
# The worker should show "ready" when it's waiting for tasks
```

### Option 3: Wait a Bit Longer

Sometimes it takes a moment for the worker to pick up tasks. Wait 1-2 minutes and check status again.

## Expected Behavior

When analyses are created:
1. Analysis record created in database (status: PENDING)
2. Task queued to Celery via `policy_impact_job.delay()`
3. Worker picks up task from queue
4. Worker processes analysis
5. Status updated: PENDING → RUNNING → COMPLETED
6. Monitor detects completion
7. Observation created automatically

## Current Status

- ✅ Worker: Running (many processes)
- ✅ Redis: Running
- ✅ Monitor: Running
- ❌ Analyses: 38 PENDING (not in queue)

**The analyses need to be queued to Celery to be processed.**

## Quick Test

Create a new analysis via the UI - it should be processed immediately since the worker is now running!
