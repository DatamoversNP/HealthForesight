# Check Frontend Status

## Quick Check

Run this to see if frontend is running:

```bash
# Check if web server is running on port 3050
lsof -i:3050

# Or check in browser
curl http://localhost:3050
```

## Start Frontend

If not running, start it:

```bash
cd apps/web
npm run dev
```

## Common Issues

1. **Port 3050 already in use**: Kill the process and restart
2. **API connection errors**: Frontend will still load but API calls will fail
3. **Build errors**: Check console for TypeScript/compilation errors

## Expected Behavior

- Frontend should load at http://localhost:3050
- Even if API is down, frontend should still show UI (with errors in console)
- If frontend doesn't load at all, check:
  - Is the dev server running?
  - Are there build errors?
  - Is port 3050 accessible?
