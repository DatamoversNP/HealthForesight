# API Server Not Starting - Missing Dependencies

## Problem

The API server can't start because Python dependencies (like `sqlalchemy`, `fastapi`) are not installed in your Python environment.

## Solution Options

### Option 1: Use a Virtual Environment (Recommended)

If you have a virtual environment set up, activate it before starting the API:

```bash
# Activate virtual environment (if you have one)
source venv/bin/activate  # or .venv/bin/activate

# Then start the API
cd apps/api
uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Install Dependencies

If you don't have a virtual environment, you can install dependencies globally (not recommended but works):

```bash
cd apps/api
pip3 install fastapi uvicorn sqlalchemy pydantic python-jose httpx boto3 polars pyarrow pandas
```

### Option 3: Check How It Was Running Before

The API was working before, so it must have been running from:
- A virtual environment
- A different Python installation
- Docker container

**Question for you:** How were you running the API before? 
- Was it in a terminal window?
- Was it using Docker?
- Was there a virtual environment activated?

## Quick Fix Script

I can create a script that:
1. Checks for a virtual environment
2. Creates one if needed
3. Installs dependencies
4. Starts the API

Would you like me to create this?
