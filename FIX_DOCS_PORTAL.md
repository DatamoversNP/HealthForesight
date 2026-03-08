# Fix: Documentation Portal Not Loading on Port 3051

## The Issue
The documentation portal requires the dev server to be running on port 3051.

## Quick Fix: Start the Server

Run this command:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
npm run dev:docs
```

**Then access:** `http://localhost:3051/documentation`

## Alternative: Use Main App (Easier)

If your main app is already running on port 3050, just access:
```
http://localhost:3050/documentation
```

The documentation is integrated into the main app, so you don't need a separate server unless you specifically want it on port 3051.

## What Was Fixed

1. ✅ Route structure updated - documentation is accessible
2. ✅ Layout fixes applied - drawer positioning corrected
3. ✅ Server config ready - `vite.docs.config.ts` configured for port 3051

## Next Steps

1. **Option A (Recommended)**: Access via main app on port 3050
   - If your main app is running, just go to `http://localhost:3050/documentation`

2. **Option B**: Start dedicated docs server on port 3051
   ```bash
   cd apps/web
   npm run dev:docs
   ```
   Then access: `http://localhost:3051/documentation`

The documentation portal is fully functional - you just need to start the server!
