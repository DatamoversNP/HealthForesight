# Final Migration Instructions - Complete Project

## What We're Migrating

**ONE Complete Project:** Utilization Elastisity and Policy Impact Solution

This includes:
- ✅ **Main Application** (API + Frontend)
- ✅ **All Your Data** (22 pipelines, 10+ policies, analyses, observations, baselines)
- ✅ **100+ Scripts** we created
- ✅ **250+ Documentation Files**
- ✅ **Complete Project Structure**

## Step-by-Step Migration

### On Current Mac (Old System)

**Step 1: Create Migration Package**
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./CREATE_MIGRATION_PACKAGE.sh
```

This creates: `~/Downloads/uepi-migration-YYYYMMDD-HHMMSS.tar.gz`

**Step 2: Transfer Package**
Copy the `.tar.gz` file to your new Mac using:
- External drive/USB
- Cloud storage (Dropbox, Google Drive, iCloud)
- AirDrop
- Network transfer

### On New Mac (New System)

**Step 1: Extract Package**
```bash
cd ~/Downloads  # or wherever you saved it
tar -xzf uepi-migration-*.tar.gz
cd "Utilization Elastisity and Policy Impact Solution"
```

**Step 2: Run Automated Setup**
```bash
./SETUP_ON_NEW_SYSTEM.sh
```

This automatically:
- ✅ Checks Python installation
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Sets up frontend (if applicable)
- ✅ Makes all scripts executable
- ✅ Verifies data files

**Step 3: Start and Verify**
```bash
# Start API
./START_API_NOW.sh

# In another terminal, verify
./FIX_AND_VERIFY_PIPELINES.sh
```

## What's Included

### ✅ Everything:
- All source code
- All data files (pipelines, policies, analyses, observations, baselines)
- All 100+ scripts
- All 250+ documentation files
- Configuration files
- Complete project structure

### ❌ Excluded (Recreated):
- Virtual environment (`.venv/`)
- Node modules (`node_modules/`)
- Cache files (`__pycache__/`, `*.pyc`)
- Log files (`*.log`)

## Prerequisites on New Mac

Before running setup:
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Node.js (if frontend exists)
brew install node
```

## Verification Checklist

After migration, verify:
- [ ] API server starts: `./START_API_NOW.sh`
- [ ] Pipelines load: `./FIX_AND_VERIFY_PIPELINES.sh` shows 22 pipelines
- [ ] Policies load: Check http://localhost:3050/policies
- [ ] Frontend loads: Check http://localhost:3050
- [ ] All scripts executable: `ls -la *.sh`
- [ ] Data visible: Check dashboard, pipelines, policies pages

## Quick Commands

**Create package:**
```bash
./CREATE_MIGRATION_PACKAGE.sh
```

**Setup on new system:**
```bash
./SETUP_ON_NEW_SYSTEM.sh
```

**Verify:**
```bash
./FIX_AND_VERIFY_PIPELINES.sh
```

## Important Notes

1. **Storage Path:** Now uses absolute paths, so it works regardless of where you place the project
2. **Data Files:** All your data is included - pipelines, policies, analyses, everything!
3. **Scripts:** All 100+ scripts are included and will be made executable
4. **Documentation:** All 250+ documentation files are included for reference

## Summary

**One command to create package:**
```bash
./CREATE_MIGRATION_PACKAGE.sh
```

**One command to setup on new Mac:**
```bash
./SETUP_ON_NEW_SYSTEM.sh
```

**Everything will work seamlessly on the new system!**

All your work, all your data, all your scripts, everything is preserved and will work exactly as it does now.
