# How to Start the Platform

## Quick Start (Easiest)

### From Project Root

Navigate to the project directory first:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
```

Then run:

```bash
./START_PLATFORM_SIMPLE.sh
```

This will:
- ✅ Stop any existing servers
- ✅ Start API server on port 8000
- ✅ Start Web server on port 3050
- ✅ Show you the URLs

## Manual Start (Two Terminals)

### Terminal 1: API Server

```bash
# Navigate to project directory
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH with absolute paths
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Change to src directory
cd apps/api/src

# Start API server
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Web Server

```bash
# Navigate to project directory
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"

# Start web server
npm run dev
```

## Important: Navigate to Project Directory First

**The project is located at:**
```
/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution
```

**Always start from this directory!**

## Access URLs

Once started:

- **Main Platform**: http://localhost:3050
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Check Status

```bash
# Check if servers are running
lsof -i:8000  # API server
lsof -i:3050  # Web server
```

## Stop Platform

```bash
# Stop API
lsof -ti:8000 | xargs kill -9

# Stop Web
lsof -ti:3050 | xargs kill -9
```

## Troubleshooting

### "No such file or directory: apps/web"

You're not in the project directory! Navigate there first:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
```

### "Module not found: uepi_api"

Make sure you're using absolute paths in PYTHONPATH:

```bash
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
```

### Port 3050 showing wrong site

Stop all servers and restart:

```bash
lsof -ti:3050 | xargs kill -9
lsof -ti:8000 | xargs kill -9
./START_PLATFORM_SIMPLE.sh
```

## Summary

**Always navigate to project directory first:**

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
```

**Then run:**

```bash
./START_PLATFORM_SIMPLE.sh
```

This will start everything automatically! 🚀
