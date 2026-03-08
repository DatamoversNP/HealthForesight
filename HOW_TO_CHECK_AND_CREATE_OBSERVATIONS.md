# How to Check Analysis Status and Create Observations

## Quick Answer: When Do I Know?

**Run this command anytime to check:**
```bash
cd apps/api
python3 scripts/check_and_create_observations.py
```

This script will:
1. ✅ Show you how many analyses are completed
2. ✅ Automatically create observations for completed analyses
3. ✅ Skip observations that already exist
4. ✅ Tell you if analyses are still pending

## What You'll See

### If Analyses Are Still Pending:
```
📈 Analysis Status:
   PENDING: 35
   COMPLETED: 0

⏳ No completed analyses yet.
   The analyses are being processed by the worker.
   Run this script again later to check status.
```

### If Analyses Are Completed:
```
📈 Analysis Status:
   PENDING: 10
   COMPLETED: 25

✅ Found 25 completed analyses!

🚀 Creating observations...
   ✅ Created: abc12345...
   ✅ Created: def67890...
   ...

🎉 Successfully created 25 observation(s)!
```

## Automated Monitoring (Optional)

If you want the script to keep checking automatically:

```bash
cd apps/api
python3 scripts/monitor_and_create_observations.py
```

This will:
- Check every 30 seconds
- Automatically create observations when analyses complete
- Run until you press Ctrl+C

## Manual Check via API

You can also check via API:

```bash
# Check analysis status
curl "http://localhost:8000/api/v1/analyses?analysis_type=IMPACT" \
  -H "Authorization: Bearer dev-token-123" | python3 -m json.tool

# Check job status (for daily jobs)
curl "http://localhost:8000/api/v1/jobs/daily-data-and-observations/status/{job_id}" \
  -H "Authorization: Bearer dev-token-123"
```

## Summary

**To know when analyses are ready and create observations:**
1. Run: `python3 apps/api/scripts/check_and_create_observations.py`
2. It will automatically create observations for any completed analyses
3. Run it again later if analyses are still pending

**No need to manually check or run anything else - just run that one script!**
