# Quick Start Platform Guide

## Starting the Platform

### Option 1: Quick Start Script (Recommended)

```bash
./start-platform.sh
```

This will:
- Stop any existing servers
- Start API server on port 8000
- Start Web server on port 3050
- Show you the URLs

### Option 2: Manual Start

#### Terminal 1: API Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Set Python path
export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"

# Start API
cd apps/api
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Web Server

```bash
cd apps/web
npm run dev
```

## Access URLs

Once started:

- **Web Application**: http://localhost:3050
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## Checking Status

### Check if servers are running:

```bash
# Check ports
lsof -i:8000  # API server
lsof -i:3050  # Web server
```

### View logs:

```bash
# API logs
tail -f api-server.log

# Web logs
tail -f web-server.log
```

## Stopping Servers

### Quick Stop:

```bash
# Stop API
lsof -ti:8000 | xargs kill -9

# Stop Web
lsof -ti:3050 | xargs kill -9
```

### Or use stop script:

```bash
./stop-both-servers.sh
```

## Troubleshooting

### Port 3050 already in use:

```bash
# Find and stop process on port 3050
lsof -ti:3050 | xargs kill -9
```

### Port 8000 already in use:

```bash
# Find and stop process on port 8000
lsof -ti:8000 | xargs kill -9
```

### API server not starting:

1. Check Python dependencies: `source .venv/bin/activate && python -c "import uvicorn"`
2. Check logs: `tail -f api-server.log`
3. Check PYTHONPATH: `export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"`

### Web server not starting:

1. Check Node dependencies: `cd apps/web && npm install`
2. Check logs: `tail -f web-server.log`
3. Check if port 3050 is available

## Notes

- **API Server**: FastAPI on port 8000
- **Web Server**: Vite dev server on port 3050
- **File Storage**: Local filesystem (./data) by default
- **Azure File Storage**: Set `USE_AZURE_FILE_STORAGE=true` to use Azure

The platform is now ready to use!
