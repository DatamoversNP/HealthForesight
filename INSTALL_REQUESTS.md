# Fix: Install Missing `requests` Module

## Problem

The daily job script is failing with:
```
ModuleNotFoundError: No module named 'requests'
```

## Solution

The `requests` library needs to be installed. I've added it to `pyproject.toml`.

### Install it now:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
source .venv/bin/activate
pip install requests
```

Or if using Poetry:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/api"
poetry add requests
```

### Or install all dependencies:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/api"
poetry install
```

## What Changed

- ✅ Added `requests = "^2.31.0"` to `apps/api/pyproject.toml`

## After Installing

The daily job should work correctly. The error was because `scripts/daily_post_policy_job.py` imports `requests` but it wasn't installed in the virtual environment.
