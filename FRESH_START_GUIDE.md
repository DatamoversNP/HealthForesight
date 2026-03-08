# Fresh Start Workflow Guide

## Overview
This guide explains the correct workflow for baselines, observations, and predictions:

1. **Baselines** = Historical data BEFORE policy activation
2. **Observations** = Data FROM policy activation date onwards
3. **Predictions** = Based on historical data
4. **All data** = Stored in same database tables (`claims_lines`)

## Step-by-Step Workflow

### Step 1: Cleanup
Remove all existing baselines and observations to start fresh.

**Option A: Via API (if DELETE endpoints exist)**
```bash
# Delete baselines and observations via API
```

**Option B: Via Database (direct)**
```bash
cd apps/api
PYTHONPATH=src python3 -c "
from uepi_api.database import SessionLocal
from uepi_api.models.baseline import Baseline
from uepi_api.models.observation import Observation
from uuid import UUID

db = SessionLocal()
tenant_id = UUID('00000000-0000-0000-0000-000000000001')

obs_count = db.query(Observation).filter(Observation.tenant_id == tenant_id).count()
baseline_count = db.query(Baseline).filter(Baseline.tenant_id == tenant_id).count()

print(f'Found: {obs_count} observations, {baseline_count} baselines')

db.query(Observation).filter(Observation.tenant_id == tenant_id).delete()
db.query(Baseline).filter(Baseline.tenant_id == tenant_id).delete()

db.commit()
print(f'✅ Deleted: {obs_count} observations, {baseline_count} baselines')

db.close()
"
```

### Step 2: Generate Historical Data
Generate data for the 12 months BEFORE policy activation dates.

**Run the workflow script:**
```bash
python3 scripts/fresh_start_workflow.py
```

This will:
- Generate general historical data (12 months before today)
- Generate policy-specific historical data (12 months before each policy's activation date)
- All data stored in `claims_lines` table

### Step 3: Create Baselines
Baselines are automatically created using historical data only (before activation).

**General Baseline:**
- Uses all historical data (12 months before today)
- No policy filters

**Policy-Specific Baseline:**
- Uses historical data matching policy scope (LOB, markets, codes)
- Date range: 12 months before policy activation, ending 1 day before activation
- Automatically filtered by policy activation date

### Step 4: Generate Post-Activation Data (for Observations)
After baselines are created, generate data from policy activation dates onwards.

```bash
# Generate data for observations (from activation date onwards)
python3 scripts/generate_historical_data.py  # Modify to generate post-activation data
```

### Step 5: Create Observations
Observations use data from policy activation date onwards.

```bash
# Create observations from post-activation analyses
python3 scripts/create_observations.py
```

## Key Points

### Data Storage
- **All data** (historical, post-activation, generated) goes to the same `claims_lines` table
- Data is distinguished by `service_date` and policy scope filters
- No separate tables for baseline vs observation data

### Date Ranges
- **Baseline window**: Ends 1 day before policy activation
- **Observation window**: Starts from policy activation date
- **Historical data**: Generated for baseline window
- **Post-activation data**: Generated for observation window

### Policy Activation Dates
- Retrieved from `policy.versions[latest].effective_start_date`
- Used to determine baseline vs observation date ranges
- Automatically enforced in baseline computation

## Scripts

1. **`scripts/fresh_start_workflow.py`**: Complete workflow (cleanup → historical data → baselines)
2. **`scripts/generate_historical_data.py`**: Generate historical data before activation
3. **`scripts/cleanup_baselines_observations.py`**: Clean up existing data
4. **`scripts/create_baselines_chunked.py`**: Create baselines in batches

## Verification

After running the workflow, verify:

1. **Baselines exist:**
   ```bash
   curl http://localhost:8000/api/v1/baselines
   ```

2. **Baseline date ranges end before activation:**
   - Check `window_end_date` < `policy.effective_start_date`

3. **Historical data exists:**
   ```bash
   # Check claims_lines table for data before activation dates
   ```

4. **Policy-specific baselines have matching data:**
   - Check baseline metrics show non-zero values
   - Verify LOB, markets, codes match policy scope
