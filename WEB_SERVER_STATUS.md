# Web Server Status

## ✅ Configuration Complete

**Port**: 3050 (already configured in `vite.config.ts`)  
**Status**: Starting...

## Access URLs

- **Web Application**: http://localhost:3050
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Note About Port 5173

Port 5173 is showing "ETL Engine" - this is a different application. Our HealthForesight application is configured to run on port 3050.

## To Start Web Server

You can start the web server using:

**Option 1: Using the script**
```bash
./START_WEB_SERVER.sh
```

**Option 2: Manual start**
```bash
cd apps/web
npm run dev
```

The server will start on port 3050 (not 5173).

## If Port 3050 is Already in Use

If you see that port 3050 is in use, you can:

1. **Stop existing process**:
   ```bash
   lsof -ti:3050 | xargs kill -9
   ```

2. **Or use the script** (it will automatically stop existing processes):
   ```bash
   ./START_WEB_SERVER.sh
   ```

## Verification

Once started, you should see:
- Vite dev server running on port 3050
- Access the app at: http://localhost:3050
- The app should show "HealthForesight" (not "ETL Engine")
