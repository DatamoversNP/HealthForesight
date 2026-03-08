# Restart API Server

## Quick Fix

The API server is not responding. Here's how to restart it:

### Step 1: Stop existing processes on port 8000

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
lsof -ti:8000 | xargs kill -9
```

### Step 2: Start the API server

**Option A: Using the start script (Recommended)**

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./start-api-server.sh
```

**Option B: Manual start**

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729

# Activate virtual environment
source .venv/bin/activate

# Set Python path
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Start API server
cd apps/api/src
python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify it's working

Wait 10-15 seconds, then check:

```bash
curl http://localhost:8000/health
```

You should see: `{"status":"healthy","service":"uepi-api"}`

### Step 4: Check the frontend

Once the API is running, refresh your browser at `http://localhost:3050`

## Troubleshooting

### If the server still doesn't start:

1. **Check for Python errors:**
   ```bash
   cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
   source .venv/bin/activate
   python3 -c "import uepi_api.main"
   ```

2. **Check if dependencies are installed:**
   ```bash
   source .venv/bin/activate
   pip list | grep uvicorn
   ```

3. **Check logs:**
   Look for error messages in the terminal where you started the server

### Common Issues

- **Port already in use**: Kill processes on port 8000 first
- **Module not found**: Make sure PYTHONPATH is set correctly
- **Virtual environment not activated**: Run `source .venv/bin/activate`
