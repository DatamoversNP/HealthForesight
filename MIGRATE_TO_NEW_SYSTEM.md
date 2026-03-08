# Migration Guide: Move to New Development System

## Overview
This guide will help you move the entire project to a new Mac system and have it work seamlessly.

## Step 1: Prepare Current System

### 1.1 Create Migration Package
On your **current laptop**, run this to create a complete backup:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"

# Create migration package
tar -czf ../uepi-migration-$(date +%Y%m%d).tar.gz \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='*.log' \
  .
```

This creates a compressed archive with all project files (excluding virtual environment and caches).

### 1.2 Export Requirements
```bash
# Export Python dependencies
source .venv/bin/activate
pip freeze > requirements.txt

# Export Node dependencies (if frontend exists)
cd apps/web 2>/dev/null && npm list --depth=0 > ../../npm-dependencies.txt 2>/dev/null || echo "No frontend"
cd ../..
```

## Step 2: Transfer to New System

### 2.1 Copy Files
Transfer the following to your new Mac:

**Option A: Using the tar.gz file**
```bash
# On new Mac, extract to desired location
cd ~/Downloads  # or wherever you want
tar -xzf uepi-migration-YYYYMMDD.tar.gz
cd "Utilization Elastisity and Policy Impact Solution"
```

**Option B: Using rsync/scp**
```bash
# From new Mac, copy from old Mac
rsync -avz --exclude='.venv' --exclude='node_modules' \
  user@old-mac:/path/to/project/ \
  ~/Downloads/Utilization\ Elastisity\ and\ Policy\ Impact\ Solution/
```

**Option C: Using external drive/USB**
- Copy the entire project folder (excluding `.venv` and `node_modules`)
- Paste to new Mac

## Step 3: Setup on New System

### 3.1 Install Prerequisites

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+ (recommended 3.11 or 3.12)
brew install python@3.11

# Install Node.js (if frontend exists)
brew install node

# Verify installations
python3 --version  # Should be 3.11+
node --version
npm --version
```

### 3.2 Setup Virtual Environment

```bash
cd "~/Downloads/Utilization Elastisity and Policy Impact Solution"

# Create new virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3.3 Install Python Dependencies

```bash
# If requirements.txt exists
pip install -r requirements.txt

# Otherwise, install common dependencies
pip install fastapi uvicorn pydantic pydantic-settings pandas polars sqlalchemy
```

### 3.4 Install Frontend Dependencies (if applicable)

```bash
cd apps/web 2>/dev/null && npm install && cd ../..
```

## Step 4: Verify Configuration

### 4.1 Check Storage Path
The storage path is now automatically calculated, but verify:

```bash
python3 << 'PYTHON_SCRIPT'
from pathlib import Path
# Check if storage_file.py calculates path correctly
storage_file = Path("apps/api/src/uepi_api/storage_file.py")
if storage_file.exists():
    project_root = storage_file.parent.parent.parent.parent.parent
    print(f"✅ Project root: {project_root.absolute()}")
    print(f"✅ Data path: {project_root / 'data'}")
else:
    print("❌ storage_file.py not found")
PYTHON_SCRIPT
```

### 4.2 Verify Data Files
```bash
# Check that data files exist
ls -la data/pipelines/ | head -5
ls -la data/policies/ 2>/dev/null | head -5
```

## Step 5: Test Everything

### 5.1 Start API Server
```bash
./START_API_NOW.sh
```

Wait for: `INFO:     Uvicorn running on http://0.0.0.0:8000`

### 5.2 Verify Pipelines
```bash
./FIX_AND_VERIFY_PIPELINES.sh
```

Should show: `✅ API returns 22 pipelines`

### 5.3 Test API Endpoints
```bash
# Test basic endpoints
curl http://localhost:8000/api/v1/me
curl http://localhost:8000/api/v1/pipelines -H "Authorization: Bearer demo-token"
curl http://localhost:8000/api/v1/policies -H "Authorization: Bearer demo-token"
```

### 5.4 Start Frontend (if applicable)
```bash
cd apps/web
npm run dev
# Should start on http://localhost:3050 or http://localhost:5173
```

## Step 6: Quick Verification Checklist

- [ ] API server starts without errors
- [ ] Pipelines load (22 found)
- [ ] Policies load (10 found)
- [ ] Frontend loads (if applicable)
- [ ] Data files are accessible
- [ ] All scripts are executable

## Files to Copy

### Essential Files (MUST COPY):
- ✅ All `*.py` files
- ✅ All `*.sh` scripts
- ✅ `data/` directory (all your data!)
- ✅ `apps/` directory
- ✅ `packages/` directory
- ✅ `scripts/` directory
- ✅ `requirements.txt` (if exists)
- ✅ `package.json` files (if frontend exists)

### Can Skip (will be regenerated):
- ❌ `.venv/` (virtual environment - recreate on new system)
- ❌ `node_modules/` (npm packages - reinstall on new system)
- ❌ `__pycache__/` (Python cache)
- ❌ `*.pyc` (compiled Python files)
- ❌ `.git/` (if you want fresh git history)

## Important Notes

### Storage Path
The storage path is now **automatically calculated** from the project root, so it will work on any system regardless of:
- Where you place the project
- What the working directory is
- System-specific paths

### Data Files
**CRITICAL:** Make sure to copy the entire `data/` directory! This contains:
- All your pipelines (22 files)
- All your policies
- All your analyses, observations, baselines
- All your ingested data

### Ports
Default ports:
- API: `8000`
- Frontend: `3050` or `5173`

If these are in use on the new system, you may need to change them.

## Troubleshooting

### Issue: "Module not found"
**Solution:** Reinstall dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Permission denied" on scripts
**Solution:** Make scripts executable
```bash
chmod +x *.sh
chmod +x scripts/**/*.sh
```

### Issue: Pipelines not loading
**Solution:** Run verification script
```bash
./FIX_AND_VERIFY_PIPELINES.sh
```

### Issue: Port already in use
**Solution:** Change port in `START_API_NOW.sh` or kill existing process
```bash
lsof -ti:8000 | xargs kill -9
```

## Quick Migration Script

I'll create a script to automate the migration process.
