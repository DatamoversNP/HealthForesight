# Fix API Start - Quick Solution

## The Problem

When you run from `apps/api` directory, the PYTHONPATH `apps/api/src` becomes relative to `apps/api`, so Python looks in `apps/api/apps/api/src` which doesn't exist.

## ✅ Solution: Use Absolute Paths

### From Project Root (Recommended)

```bash
# Make sure you're in project root (where this file is)
pwd
# Should show: .../Utilization Elastisity and Policy Impact Solution

# Activate venv
source .venv/bin/activate

# Set PYTHONPATH with ABSOLUTE paths using $(pwd)
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Change to src directory
cd apps/api/src

# Start server
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Or Use the Script (Easiest)

From project root:

```bash
./START_API_NOW.sh
```

## ✅ One-Liner (Copy & Paste)

From project root:

```bash
source .venv/bin/activate && export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH" && cd apps/api/src && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Why This Works

- **`$(pwd)`** gives absolute path to project root
- **`$(pwd)/apps/api/src`** = absolute path to where `uepi_api` module is
- **`cd apps/api/src`** = run uvicorn from the src directory

## Verify It Works

Before starting server, test:

```bash
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
python3 -c "import uepi_api; print('✅ Module found!')"
```

If you see "✅ Module found!", you're ready to start!

## After API Starts

In a new terminal, start the web server:

```bash
cd apps/web
npm run dev
```

Then open: http://localhost:3050
