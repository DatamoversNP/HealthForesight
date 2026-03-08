# Test API Connection

The script is getting "Connection refused" which means the API might not be accessible.

## Quick Test

Run this to verify API is accessible:

```bash
# Test 1: Health endpoint
curl http://localhost:8000/health

# Test 2: Policies endpoint (with auth)
curl -H 'Authorization: Bearer dev-token-123' http://localhost:8000/api/v1/policies

# Test 3: Policies endpoint (without auth - might work with demo user)
curl http://localhost:8000/api/v1/policies
```

## If Connection Refused

The API might be:
1. Not actually running (check the terminal where you started it)
2. Running on a different port
3. Blocked by firewall
4. Binding to wrong interface (should be 0.0.0.0:8000)

## Check API Status

In the terminal where API is running, you should see:
- `INFO: Uvicorn running on http://0.0.0.0:8000`
- `INFO: Application startup complete.`

If you see errors, the API might have crashed.

## Alternative: Use Direct Database Access

If API connection continues to fail, we can create observations directly from the claims data file without using the API. Let me know if you want that approach.
