# Quick Start Guide - Local Development

## Current Status
- ✅ Frontend: Running on http://localhost:3050
- ⚠️ API: Process running but not responding (may need to check for errors)

## To Start the Application

### Option 1: Start API Server (Recommended)
In a terminal, run:
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./START_API_NOW.sh
```

**What to look for:**
- You should see: `INFO: Uvicorn running on http://0.0.0.0:8000`
- If you see errors, share them and we can fix them

### Option 2: Start Both Servers
```bash
./start-both-servers.sh
```

## Troubleshooting

### API Not Responding?
1. Check the terminal where you ran `START_API_NOW.sh` for error messages
2. Common issues:
   - Missing dependencies: `pip install -r requirements.txt`
   - Port already in use: `lsof -ti:8000 | xargs kill`
   - Python path issues: Check PYTHONPATH is set correctly

### Check API Status
```bash
./CHECK_API_STATUS.sh
```

### Test API Directly
```bash
curl http://localhost:8000/health
```

## Access Points
- **Frontend**: http://localhost:3050
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Next Steps
Once the API is running, refresh your browser and the application should work!
