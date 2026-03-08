# Web Server Port Update

## ✅ Port Changed to 3050

**Previous Port**: 5173 (default Vite port)  
**New Port**: 3050 (as requested)

## Changes Made

**File**: `apps/web/vite.config.ts`
- Changed `server.port` from `5173` to `3050`

## Access URLs

- **Web Application**: http://localhost:3050
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## To Start Web Server

```bash
cd apps/web
npm run dev
```

The server will now start on port 3050 instead of 5173.

## Note

If port 3050 is already in use, you can:
1. Stop the process using port 3050
2. Or change the port in `vite.config.ts` to another available port
