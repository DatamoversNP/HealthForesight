# Plan: Remove All Database References - File Storage Only

## User Requirement
Remove ALL database references from the codebase. The system should be file-based ONLY, even for Azure deployment.

## Current State
- System has dual-mode: database OR file storage
- Policy endpoints try database first, fall back to file storage
- Many imports and dependencies on SQLAlchemy, database models, etc.

## Refactoring Plan

### Phase 1: Fix Immediate Issues ✅
- [x] Fix storage module import conflict
- [ ] Test API works with file storage

### Phase 2: Remove Database from Policies Router
- [ ] Remove all database/SQLAlchemy imports from `apps/api/src/uepi_api/routers/policies.py`
- [ ] Remove database fallback logic
- [ ] Make all policy endpoints use file storage exclusively
- [ ] Remove `get_db` dependency from policy endpoints
- [ ] Remove Policy, PolicyVersion model imports

### Phase 3: Simplify Configuration
- [ ] Remove `USE_FILE_STORAGE` flag (always file storage)
- [ ] Remove database configuration from settings
- [ ] Simplify database.py (or remove it entirely)

### Phase 4: Update Other Routers (if needed)
- [ ] Check other routers for database dependencies
- [ ] Update analysis, auth, etc. routers to use file storage only

### Phase 5: Clean Up Dependencies
- [ ] Remove SQLAlchemy from dependencies (if not needed)
- [ ] Remove database-related imports
- [ ] Clean up unused database models

## Files to Modify
1. `apps/api/src/uepi_api/routers/policies.py` - Remove all DB code
2. `apps/api/src/uepi_api/database.py` - Simplify or remove
3. `apps/api/src/uepi_api/config.py` - Remove database settings
4. Any other routers using database

## Notes
- Keep file storage implementation as-is
- Azure deployment will use Azure File Storage or Blob Storage (file-based)
- No PostgreSQL/SQL database needed
