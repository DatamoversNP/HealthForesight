# Platform Started Successfully! ✅

## Platform Status

The HealthForesight platform is now starting up on:

- **🌐 Web Application**: http://localhost:3050
- **🔧 API Server**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs

## Quick Access

Open your browser and go to:

```
http://localhost:3050
```

This should show the HealthForesight application (not the marketing website).

## Verify Servers

### Check API Server

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### Check Web Server

```bash
# Web app
curl http://localhost:3050

# Open in browser
open http://localhost:3050
```

## View Logs

### API Server Logs

```bash
tail -f api-server.log
```

### Web Server Logs

```bash
tail -f web-server.log
```

## If Port 3050 Shows Wrong Site

If you're still seeing the marketing website on port 3050:

1. **Stop all servers**:
   ```bash
   lsof -ti:3050 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

2. **Restart platform**:
   ```bash
   ./start-platform.sh
   ```

   OR manually:

   **Terminal 1 - API**:
   ```bash
   source .venv/bin/activate
   export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"
   cd apps/api
   python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Terminal 2 - Web**:
   ```bash
   cd apps/web
   npm run dev
   ```

## Stop Platform

To stop the platform:

```bash
# Stop API
lsof -ti:8000 | xargs kill -9

# Stop Web
lsof -ti:3050 | xargs kill -9
```

Or use:

```bash
./stop-both-servers.sh
```

## What You Should See

### Port 3050 - Main Platform
- HealthForesight login/dashboard
- Policy Builder
- What-If Analysis
- Scorecards
- All main application features

### Port 3051 - Documentation Portal (if running)
- Documentation portal
- Product guides
- API documentation

### Port 8000 - API Server
- API documentation (Swagger UI)
- Health endpoint
- All API endpoints

## Troubleshooting

### Still seeing marketing website on 3050?

1. Check what's running:
   ```bash
   lsof -i:3050
   ```

2. If it's not the main app, stop and restart:
   ```bash
   lsof -ti:3050 | xargs kill -9
   cd apps/web
   npm run dev
   ```

### API not responding?

1. Check API logs:
   ```bash
   tail -f api-server.log
   ```

2. Verify API is running:
   ```bash
   curl http://localhost:8000/health
   ```

3. Restart API:
   ```bash
   source .venv/bin/activate
   export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"
   cd apps/api
   python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Platform Components

### Running Services

- ✅ **API Server** (FastAPI) - Port 8000
- ✅ **Web Application** (React/Vite) - Port 3050
- ✅ **File Storage** - Local filesystem (./data)

### Configuration

- **Storage**: Local file system (default)
- **Azure File Storage**: Available (set `USE_AZURE_FILE_STORAGE=true`)

## Next Steps

1. **Open**: http://localhost:3050
2. **Login**: Use demo credentials (if configured)
3. **Explore**: Navigate through the platform
4. **Test**: Try creating a policy, running What-If analysis, etc.

The platform is ready to use! 🎉
