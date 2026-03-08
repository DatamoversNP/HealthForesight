# Running Tests

## Project Structure

This is a monorepo with separate Poetry projects:
- `apps/api/` - API service (has its own `pyproject.toml`)
- `apps/worker/` - Worker service (has its own `pyproject.toml`)
- `packages/common/` - Shared package (has its own `pyproject.toml`)
- `apps/web/` - Frontend (uses npm)

The root `pyproject.toml` is only for tooling configuration (ruff, mypy, pytest), not for packaging.

## Running Tests

### Backend Tests (Python)

**Option 1: Install and test from individual projects**

```bash
# From project root
cd apps/api
poetry install
poetry run pytest

# Or for worker
cd ../worker
poetry install
poetry run pytest

# Or for common package
cd ../../packages/common
poetry install
poetry run pytest
```

**Option 2: Use pip directly (if Poetry is causing issues)**

```bash
# Install dependencies
cd apps/api
pip install -r requirements.txt  # If you have one, or install manually
pytest

# Or use Python directly
python3 -m pytest
```

### Frontend Tests (TypeScript/Vitest)

```bash
# From project root
cd apps/web

# Install dependencies (if not already done)
npm install

# Run tests
npm test

# Or run with coverage
npm test -- --coverage
```

### Quick Validation (No Dependencies Required)

```bash
# From project root
python3 scripts/test_scenario_accuracy.py
```

This validates code structure without requiring full environment setup.

## Troubleshooting

### Poetry Error: "No file/folder found for package uepi"

The root `pyproject.toml` now has `package-mode = false` to fix this. If you still see the error:

```bash
# Install from individual projects instead
cd apps/api && poetry install --no-root
```

### pytest not found

Install pytest in the project you're testing:

```bash
cd apps/api
poetry add --group dev pytest
# Or
pip install pytest
```

### npm test fails

Make sure you're in the `apps/web` directory and dependencies are installed:

```bash
cd apps/web
npm install
npm test
```
