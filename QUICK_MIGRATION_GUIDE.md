# Quick Migration Guide: Move to New Mac

## On Current System (Old Mac)

### Step 1: Create Migration Package
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./CREATE_MIGRATION_PACKAGE.sh
```

This creates: `~/Downloads/uepi-migration-YYYYMMDD-HHMMSS.tar.gz`

### Step 2: Transfer Package
Copy the `.tar.gz` file to your new Mac using:
- External drive/USB
- Cloud storage (Dropbox, Google Drive, etc.)
- Network transfer (scp, rsync)
- AirDrop

## On New System (New Mac)

### Step 1: Extract Package
```bash
cd ~/Downloads  # or wherever you saved it
tar -xzf uepi-migration-*.tar.gz
cd "Utilization Elastisity and Policy Impact Solution"
```

### Step 2: Run Setup Script
```bash
./SETUP_ON_NEW_SYSTEM.sh
```

This will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup frontend (if applicable)
- ✅ Make scripts executable
- ✅ Verify data files

### Step 3: Verify Everything Works
```bash
# Start API
./START_API_NOW.sh

# In another terminal, verify
./FIX_AND_VERIFY_PIPELINES.sh
```

## What Gets Migrated

✅ **All your data:**
- Pipelines (22 files)
- Policies (10+ files)
- Analyses, observations, baselines
- All ingested data

✅ **All code:**
- API code
- Frontend code
- Scripts
- Configuration

✅ **Project structure:**
- Complete directory structure
- All configuration files

## What Gets Recreated

❌ **Virtual environment** - Recreated on new system
❌ **Node modules** - Reinstalled on new system
❌ **Python cache** - Regenerated automatically

## Prerequisites on New Mac

Before running setup, install:

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Node.js (if frontend exists)
brew install node
```

## Verification Checklist

After setup, verify:
- [ ] API server starts: `./START_API_NOW.sh`
- [ ] Pipelines load: `./FIX_AND_VERIFY_PIPELINES.sh` shows 22 pipelines
- [ ] Policies load: Check http://localhost:3050/policies
- [ ] Frontend loads: Check http://localhost:3050 (if applicable)
- [ ] All data visible: Check dashboard, pipelines, policies pages

## Troubleshooting

### "Python not found"
```bash
brew install python@3.11
```

### "npm not found"
```bash
brew install node
```

### "Permission denied" on scripts
```bash
chmod +x *.sh
```

### Pipelines not loading
```bash
./FIX_AND_VERIFY_PIPELINES.sh
# If still 0, restart API server
```

## Summary

**On Old Mac:**
1. Run `./CREATE_MIGRATION_PACKAGE.sh`
2. Transfer `.tar.gz` file

**On New Mac:**
1. Extract `.tar.gz`
2. Run `./SETUP_ON_NEW_SYSTEM.sh`
3. Start API: `./START_API_NOW.sh`
4. Verify: `./FIX_AND_VERIFY_PIPELINES.sh`

That's it! Everything should work seamlessly on the new system.
