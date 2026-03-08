# Install and Start API - Simple Steps

## Step 1: Install Python Packages

Open Terminal and run this command (copy and paste):

```bash
python3 -m pip install --user fastapi "uvicorn[standard]" pydantic pydantic-settings python-jose httpx boto3 sqlalchemy polars pyarrow pandas
```

**Note:** The quotes around `"uvicorn[standard]"` are important!

This will take 2-3 minutes. Wait for it to finish.

## Step 2: Start the API

Once the installation is complete, run:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./setup-and-start-api.sh
```

Or if you prefer to start it manually:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/api"
export PYTHONPATH="$(pwd)/src:$(pwd)/../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 3: Verify It's Working

- Open browser: http://localhost:8000/docs
- Should see FastAPI documentation
- Then go to: http://localhost:3050/policies
- Click Psychology icon (🧠) on any policy

## That's It!

The packages only need to be installed **once**. After that, you can just use:
- `./restart-api.sh` to restart
- `./stop-api.sh` to stop

## Troubleshooting

### If pip install fails
- Make sure you have internet connection
- Try: `python3 -m pip install --upgrade pip` first

### If API won't start
- Check the error messages in the terminal
- Make sure you're in the right directory
