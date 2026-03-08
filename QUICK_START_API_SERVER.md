# Quick Start API Server

The main application on port 3050 requires the API server to be running on port 8000.

## Start API Server

### Option 1: Using the start script (Recommended)
```bash
./start-api-server.sh
```

This will:
- Activate the virtual environment
- Set up Python paths
- Start the API server on port 8000

### Option 2: Start both servers (API + Web)
```bash
./start-both-servers.sh
```

This will start:
- API server on port 8000
- Web server on port 3050

### Option 3: Manual start (if scripts don't work)
```bash
# Activate virtual environment
source .venv/bin/activate

# Set Python path
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Start API server
cd apps/api
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Verify API Server is Running

Once started, verify it's working:
```bash
curl http://localhost:8000/health
```

You should see a response. If you get an error, check the logs.

## Access Points

- **Main Application**: http://localhost:3050 (requires API server)
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Documentation Portal**: http://localhost:3051 (standalone, no API needed)

## Troubleshooting

If the API server fails to start:
1. Check if port 8000 is already in use: `lsof -i :8000`
2. Check logs: `tail -f api-server.log`
3. Ensure virtual environment exists: `python3 -m venv .venv`
4. Install dependencies: `source .venv/bin/activate && pip install -r requirements.txt`
