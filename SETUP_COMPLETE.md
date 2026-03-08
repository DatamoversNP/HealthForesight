# Database Migration Setup Complete ✅

## Backup Created
- **Backup Directory:** `backup_20260202_201442/`
- **Current file-based code:** Preserved and unchanged
- **Location:** All storage files backed up

## Implementation Strategy

### Folder Structure (No Git Branch Needed)
Since this isn't a git repo, we'll implement database support **alongside** file-based code:

```
apps/api/src/uepi_api/
├── storage_*.py          # Existing file-based (UNCHANGED)
├── models/              # Database models (ADD database models here)
│   ├── policy.py        # Add: PolicyAssumption, PolicyGuardrail, PolicyChangelog
│   ├── predicted_impact.py  # NEW: PolicyPredictedImpact
│   ├── baseline.py       # NEW: Baseline
│   ├── observation.py   # NEW: Observation
│   └── ... (30+ more models)
├── storage_db/          # NEW: Database storage implementations
│   ├── policy_db.py     # Database version of storage_policies.py
│   ├── assumption_db.py # Database version of storage_policy_assumptions.py
│   └── ... (39 database storage files)
└── storage/             # Existing (UNCHANGED)
```

### Dual-Mode Pattern
Each storage file will support both modes:

```python
# storage_policies.py (UPDATED - but file code unchanged)
def get_policy(policy_id, tenant_id):
    if USE_FILE_STORAGE:
        return _get_policy_from_file(policy_id, tenant_id)  # Existing code
    else:
        return _get_policy_from_db(policy_id, tenant_id)   # New database code
```

## Implementation Plan

### Phase 1: Database Models (Starting Now)
1. Create all 30+ database models in `models/`
2. Models will be added to existing model files or new files
3. All models inherit from `Base` (SQLAlchemy)

### Phase 2: Alembic Migrations
1. Create migrations for all tables
2. Test up/down migrations

### Phase 3: Database Storage Functions
1. Create database implementations in `storage_db/` or update existing files
2. Use dual-mode pattern to switch between file/database

### Phase 4: Data Migration
1. Scripts to move data from files to database
2. Validation scripts

## Next: Starting Implementation

I'll now start creating:
1. ✅ Database models (30+ tables)
2. ✅ Alembic migrations
3. ✅ Database storage functions
4. ✅ Data migration scripts

**Current file-based code remains 100% intact and functional.**

