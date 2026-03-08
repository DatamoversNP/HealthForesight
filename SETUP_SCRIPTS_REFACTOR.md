# Setup Scripts Refactor - Summary

## What Changed

The monolithic `initialize_system.py` script has been broken down into **6 focused, independent scripts** that can be run individually or together.

## New Structure

```
apps/api/scripts/
├── 01_setup_database.py          # Database reset and table creation
├── 02_setup_tenant_user.py       # Demo tenant and user setup
├── 03_seed_policies.py           # Policy seeding
├── 04_seed_pipelines.py          # Pipeline seeding
├── 05_setup_source_directories.py # Source data directory setup
├── 06_verify_system.py           # System verification
├── initialize_system.py          # Orchestrator (runs all steps)
└── README_SETUP.md               # Detailed documentation
```

## Benefits

1. **Easier Debugging**: Each step is isolated - you can see exactly which step fails
2. **Flexible Execution**: Run only the steps you need
3. **Better Error Messages**: Focused scripts provide clearer context
4. **Reusability**: Scripts can be used independently in CI/CD
5. **Maintainability**: Single responsibility per script

## Quick Start

### Run All Steps (Recommended)
```bash
cd apps/api
python scripts/initialize_system.py
```

### Run Individual Steps
```bash
# Only setup database
python scripts/01_setup_database.py

# Only seed policies
python scripts/03_seed_policies.py

# Only verify system
python scripts/06_verify_system.py
```

## Script Details

### Critical Steps (Must Succeed)
- **01_setup_database.py**: Creates database and tables
- **02_setup_tenant_user.py**: Creates demo tenant/user

### Optional Steps (Can Fail)
- **03_seed_policies.py**: Seeds policies (skips if exist)
- **04_seed_pipelines.py**: Seeds pipelines (skips if exist)
- **05_setup_source_directories.py**: Creates directories
- **06_verify_system.py**: Verifies everything is ready

## Error Handling

- Each script has comprehensive error handling
- Scripts can be safely re-run (they skip existing data)
- Critical steps stop the orchestrator if they fail
- Optional steps continue even if they fail

## Troubleshooting

If a step fails:

1. **Check the error message** - Each script provides detailed error output
2. **Run the step individually** - This isolates the problem
3. **Check dependencies** - Ensure previous steps completed
4. **Review logs** - Each script logs its progress

## Migration from Old Script

The old `initialize_system.py` is replaced with the orchestrator. The orchestrator:
- Runs all steps in order
- Stops on critical failures
- Continues on optional failures
- Provides a summary at the end

## Next Steps

1. Run `python scripts/initialize_system.py` to set up the system
2. If any step fails, run it individually to debug
3. Use `06_verify_system.py` to check system status anytime

