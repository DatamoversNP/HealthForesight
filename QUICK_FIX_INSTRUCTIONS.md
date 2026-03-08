# Quick Fix: Install Dependencies and Run Data Generation

## The Problem
- `ModuleNotFoundError: No module named 'pandas'` - pandas is not installed
- Date parsing issue (showing "0111-10") - Fixed in the script

## Quick Fix

### Step 1: Install Dependencies
```bash
# Activate virtual environment
source .venv/bin/activate

# Install pandas and polars
pip install pandas polars
```

### Step 2: Run Data Generation
```bash
./GENERATE_DATA_FROM_LAST_DATE.sh
```

## Or Use the All-in-One Script
```bash
./INSTALL_DEPENDENCIES_AND_RUN.sh
```

This script will:
1. Activate virtual environment
2. Install pandas and polars
3. Run data generation

## What Was Fixed

1. **Date Parsing**: Fixed regex to correctly extract year/month from filenames
2. **Variable Names**: Fixed `file_date` vs `latest_file_date` confusion
3. **Sanity Checks**: Added validation for year (2000-2100) and month (1-12)
4. **Virtual Environment**: Script now activates venv automatically

## Manual Installation (if script fails)

```bash
# Check if virtual environment exists
ls -la .venv/bin/activate

# If it exists, activate it
source .venv/bin/activate

# Install dependencies
pip install pandas polars

# Verify installation
python3 -c "import pandas; print('✅ pandas installed')"
python3 -c "import polars; print('✅ polars installed')"

# Run generation
python3 scripts/synth/generate.py \
  --out data/demo \
  --members 50000 \
  --providers 5000 \
  --months 3 \
  --seed 42
```

## After Installation

Once dependencies are installed, you can:
1. Generate data: `./GENERATE_DATA_FROM_LAST_DATE.sh`
2. Run pipelines: `./RUN_ALL_PIPELINES.sh`
3. Check data quality dashboard

All scripts should work correctly now!
