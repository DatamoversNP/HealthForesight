# Correct Commands to Start API Server

## The Problem

You're getting `ModuleNotFoundError: No module named 'uepi_api'` because the PYTHONPATH doesn't include the `src` directory.

## The Solution

The module `uepi_api` is located at: `apps/api/src/uepi_api/`

So PYTHONPATH must include: `apps/api/src`

## ✅ Correct Command (Copy & Paste)

**From the project root directory** (where this file is):

```bash
# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH correctly (from project root)
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Change to src directory
cd apps/api/src

# Start server
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Alternative: One-Liner

From project root:

```bash
source .venv/bin/activate && export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH" && cd apps/api/src && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Or Use the Script

From project root:

```bash
./START_API_CORRECT.sh
```

## Key Points

1. **Start from project root** (not from `apps/api`)
2. **PYTHONPATH must include**: `apps/api/src` (where `uepi_api` module is)
3. **Run uvicorn from**: `apps/api/src` directory OR with correct PYTHONPATH
4. **Module location**: `apps/api/src/uepi_api/main.py`

## Why It Works

- `uepi_api` module is at: `apps/api/src/uepi_api/`
- Python looks for modules in directories listed in PYTHONPATH
- By adding `apps/api/src` to PYTHONPATH, Python can find `uepi_api`

## Verify Module Can Be Found

```bash
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
python3 -c "import uepi_api; print('✅ Module found!')"
```

If this works, you're ready to start the server!
