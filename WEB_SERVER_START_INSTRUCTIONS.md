# Web Server Startup Instructions

## Status
- ✅ **API Server**: Running on port 8000
- ⏳ **Web Server**: Starting on port 3050

## Quick Start

The web server is being started. If it's not running yet, use:

```bash
./START_WEB_SERVER.sh
```

Or manually:

```bash
cd apps/web
npm run dev
```

## Access URLs

Once both servers are running:
- **Web Application**: http://localhost:3050
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Verification

Check if web server is running:
```bash
lsof -ti:3050
```

If you see a process ID, the server is running.

## Troubleshooting

**If port 3050 is already in use:**
```bash
lsof -ti:3050 | xargs kill -9
./START_WEB_SERVER.sh
```

**If npm dependencies are missing:**
```bash
cd apps/web
npm install
npm run dev
```

**If you see connection errors:**
- Make sure API is running on port 8000
- Check that vite.config.ts has correct proxy settings
- Verify STORAGE_PATH is set for API

## Current Configuration

- **Web Port**: 3050 (configured in `vite.config.ts`)
- **API Port**: 8000
- **Proxy**: `/api/*` → `http://localhost:8000/api/*`

