# How to Install Poetry and Start the API

## Issue
Poetry installation via the official script failed due to Python environment constraints.

## Solutions

### Option 1: Install Poetry via Homebrew (Recommended for macOS)
```bash
brew install poetry
cd apps/api
poetry install
poetry run uvicorn src.main:app --reload --port 8000
```

### Option 2: Install Poetry via pipx (if available)
```bash
pipx install poetry
cd apps/api
poetry install
poetry run uvicorn src.main:app --reload --port 8000
```

### Option 3: Manual Poetry Installation
1. Download poetry: https://python-poetry.org/docs/#installation
2. Or use pip: `pip install poetry` (if you have pip)
3. Then: `cd apps/api && poetry install && poetry run uvicorn src.main:app --reload`

## Current Status

✅ Configuration ready (USE_FILE_STORAGE=true)
✅ Services running (Redis & MinIO)
✅ Code ready
❌ Poetry not installed - needed to run API

## Once Poetry is installed:

1. **Install dependencies:**
   ```bash
   cd apps/api
   poetry install
   ```

2. **Start the API:**
   ```bash
   poetry run uvicorn src.main:app --reload --port 8000
   ```

3. **Access in browser:**
   - http://localhost:8000/docs (API Documentation)
   - http://localhost:8000/health (Health Check)
   - http://localhost:8000/api/v1/policies (Policies API)
