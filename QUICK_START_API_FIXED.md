# Quick Start API Server - Fixed

## Issue

You're getting `ModuleNotFoundError: No module named 'uepi_api'` because PYTHONPATH needs to include the `src` directory.

## Solution

### Option 1: Use the Fixed Script (Recommended)

```bash
chmod +x start-api-fixed.sh
./start-api-fixed.sh
```

### Option 2: Manual Start with Correct PYTHONPATH

From the project root:

```bash
# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH correctly (from project root)
export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"

# Change to API directory
cd apps/api

# Start server
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Start from Project Root (Easiest)

```bash
# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH from project root
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Start server (can stay in project root)
cd apps/api
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Key Points

- **PYTHONPATH must include**: `apps/api/src` (where `uepi_api` module is)
- **Start from**: Project root or `apps/api` directory
- **Module location**: `apps/api/src/uepi_api/`

## Verify Module Found

```bash
export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"
python3 -c "import uepi_api; print('✅ Module found')"
```

## Complete Command (Copy & Paste)

From project root:

```bash
source .venv/bin/activate && export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH" && cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```
