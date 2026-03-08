# How to Start the API Server

## Prerequisites
- Python 3.9+ installed
- Poetry installed (dependency manager)

## Install Poetry (if not installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

Or on macOS with Homebrew:
```bash
brew install poetry
```

## Start the API Server

1. **Navigate to API directory:**
   ```bash
   cd apps/api
   ```

2. **Install dependencies (first time only):**
   ```bash
   poetry install
   ```

3. **Start the server:**
   ```bash
   poetry run uvicorn src.main:app --reload --port 8000
   ```

4. **Access in browser:**
   - API Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health
   - Policies: http://localhost:8000/api/v1/policies

## Troubleshooting

- If poetry command not found: Add `~/.local/bin` to PATH or use full path
- If dependencies missing: Run `poetry install` first
- If port 8000 in use: Change port with `--port 8001`

## Current Status

✅ Configuration: .env file with USE_FILE_STORAGE=true
✅ Services: Redis & MinIO running
❌ API Server: Needs to be started (requires Poetry)
