# Complete Database-Only Refactor Guide

## Status
- ✅ `database.py` - Always uses PostgreSQL (removed USE_FILE_STORAGE)
- ✅ `storage_baselines.py` - Database only
- 🔄 Remaining 36 storage files need refactoring

## Refactoring Pattern

For each `storage_*.py` file:

1. **Remove file storage imports:**
   ```python
   # Remove these:
   import json
   from pathlib import Path
   from uepi_api.storage_file import init_storage, BASE_PATH
   from uepi_api.database import USE_FILE_STORAGE
   ```

2. **Remove file storage initialization:**
   ```python
   # Remove:
   init_storage()
   OBSERVATIONS_PATH = BASE_PATH / "observations"
   ```

3. **Remove file storage helper functions:**
   - `_ensure_*_storage()`
   - `_load_*_index()`
   - `_save_*_index()`
   - `_get_*_file_path()`
   - `_*_in_file()` functions

4. **Update public functions:**
   ```python
   # Change from:
   if not USE_FILE_STORAGE:
       return _create_in_db(...)
   else:
       return _create_in_file(...)
   
   # To:
   return _create_in_db(...)
   ```

5. **Rename database functions:**
   - `_create_*_in_db()` → `_create_*()`
   - `_get_*_from_db()` → `_get_*()`
   - `_list_*_from_db()` → `_list_*()`

6. **Update docstrings:**
   - "supports both file-based and database storage" → "database only"
   - "stored in database or file-based storage" → "stored in database"

## Remaining Work

### Storage Files (36 remaining)
See `REFACTOR_PROGRESS.md` for complete list.

### Routers to Update
- Remove imports of `*_file.py` routers
- Remove `USE_FILE_STORAGE` checks
- Ensure all routers use database sessions

### Configuration
- Remove `use_file_storage` from config
- Update environment variable documentation

### Migration Script
- Run `migrate_files_to_db.py` to import existing file data
- Script is idempotent (safe to run multiple times)

## Testing Checklist
- [ ] All storage_*.py files use database only
- [ ] No file I/O for persistence (except imports/exports)
- [ ] All routers work with database
- [ ] Migration script successfully imports file data
- [ ] Tests updated to use database
- [ ] Documentation updated

## Next Steps
1. Continue refactoring storage files (use pattern above)
2. Update routers to remove file storage paths
3. Run migration script
4. Update tests
5. Clean up dead code

