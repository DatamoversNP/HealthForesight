# System Setup Scripts

The system initialization has been broken down into logical, focused scripts that can be run independently or as a group.

## Script Overview

### 1. `01_setup_database.py` (REQUIRED)
- Resets database (drop and recreate)
- Creates all tables
- Verifies database connection
- **Must run first**

### 2. `02_setup_tenant_user.py` (REQUIRED)
- Creates demo tenant if it doesn't exist
- Creates demo user if it doesn't exist
- Verifies tenant and user are ready
- **Requires database to be set up first**

### 3. `03_seed_policies.py` (OPTIONAL)
- Loads policies from `seed_policies.py`
- Creates policies in database (skips if already exist)
- Reports creation status
- **Can be skipped if policies already exist**

### 4. `04_seed_pipelines.py` (OPTIONAL)
- Loads pipelines from JSON files in `data/pipelines/`
- Creates pipelines in database (skips if already exist)
- Reports creation status
- **Can be skipped if pipelines already exist or directory is empty**

### 5. `05_setup_source_directories.py` (OPTIONAL)
- Creates source data directory structure
- Creates historical and daily load directories
- Creates README with usage instructions
- **Can be run anytime**

### 6. `06_verify_system.py` (OPTIONAL)
- Verifies database connection
- Checks that policies exist
- Checks that pipelines exist
- Verifies source data directories exist
- Reports system status
- **Useful for troubleshooting**

## Usage

### Run All Steps (Recommended)
```bash
cd apps/api
python scripts/initialize_system.py
```

### Run Individual Steps
```bash
# Step 1: Database setup (REQUIRED)
python scripts/01_setup_database.py

# Step 2: Setup tenant/user (REQUIRED)
python scripts/02_setup_tenant_user.py

# Step 3: Seed policies (OPTIONAL)
python scripts/03_seed_policies.py

# Step 4: Seed pipelines (OPTIONAL)
python scripts/04_seed_pipelines.py

# Step 5: Setup source directories (OPTIONAL)
python scripts/05_setup_source_directories.py

# Step 6: Verify system (OPTIONAL)
python scripts/06_verify_system.py
```

## Error Handling

- **Critical steps** (01, 02): If these fail, the orchestrator stops
- **Optional steps** (03-06): These can fail without stopping the process
- Each script has its own error handling and logging
- Scripts can be re-run safely (they skip existing data)

## Troubleshooting

### Database Connection Issues
1. Check `DATABASE_URL` environment variable
2. Ensure PostgreSQL is running
3. Verify database credentials
4. Run `01_setup_database.py` to reset database

### Missing Tables
1. Run `01_setup_database.py` to recreate tables
2. Check for import errors in model files
3. Verify all models are imported in `database.py`

### Policy/Pipeline Creation Fails
1. Check that tenant/user exist (run `02_setup_tenant_user.py`)
2. Verify source files exist (`seed_policies.py`, `data/pipelines/*.json`)
3. Check database connection
4. Review error logs for specific issues

## Script Dependencies

```
01_setup_database.py
    └─> (no dependencies)

02_setup_tenant_user.py
    └─> Requires: 01_setup_database.py

03_seed_policies.py
    └─> Requires: 01_setup_database.py, 02_setup_tenant_user.py

04_seed_pipelines.py
    └─> Requires: 01_setup_database.py, 02_setup_tenant_user.py

05_setup_source_directories.py
    └─> (no dependencies)

06_verify_system.py
    └─> Requires: 01_setup_database.py, 02_setup_tenant_user.py
```

## Environment Variables

All scripts use these environment variables:
- `DATABASE_URL`: PostgreSQL connection string (required)
- `USE_FILE_STORAGE`: Set to `false` (database-only mode)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Benefits of This Approach

1. **Easier Debugging**: Each step is isolated and can be run independently
2. **Better Error Messages**: Focused scripts provide clearer error context
3. **Flexibility**: Run only the steps you need
4. **Reusability**: Scripts can be used in CI/CD pipelines
5. **Maintainability**: Each script has a single, clear responsibility

