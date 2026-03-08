# Quick Start - API Server

## One Command to Rule Them All! 🎯

Just run this **one command** and everything will be set up:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./setup-and-start-api.sh
```

## What It Does

This script automatically:
1. ✅ Checks if Python dependencies are installed
2. ✅ Installs them if missing (fastapi, uvicorn, etc.)
3. ✅ Stops any old API server
4. ✅ Copies policies file to the right location
5. ✅ Starts the API server
6. ✅ Verifies it's running

## After Running

Once the script completes:
- ✅ API will be running at: http://localhost:8000
- ✅ API docs at: http://localhost:8000/docs
- ✅ Go to your frontend: http://localhost:3050/policies
- ✅ Click the Psychology icon (🧠) on any policy to see predicted impact!

## Troubleshooting

### If it says "Python3 not found"
- Make sure Python 3 is installed
- Try: `python3 --version`

### If packages won't install
- Run manually: `python3 -m pip install --user fastapi uvicorn[standard] pydantic pydantic-settings python-jose httpx boto3`
- Then run the script again

### To stop the API
```bash
./stop-api.sh
```

### To view logs
```bash
tail -f api-server.log
```

## That's It!

One script, everything automated. No manual steps needed! 🚀
