# Routers - File Storage Only Refactoring

## ✅ COMPLETED

### 1. Auth Router ✅
- Removed `get_db` and `Session` dependencies
- Removed database queries (User, Tenant models)
- Uses CurrentUser directly (file storage mode)

### 2. Scorecards Router ✅  
- Removed `get_db` and `Session` dependencies
- All endpoints return empty lists (feature not yet implemented in file storage)
- Simplified to file-storage only

## 🔄 IN PROGRESS

### 3. Analyses Router (PARTIAL)
- `list_analyses` - Already uses file storage ✅
- `create_baseline_analysis` - Already uses file storage ✅
- Other endpoints still need conversion

## ⏸️ REMAINING ROUTERS (Low Priority)

These routers can be updated similarly - remove database dependencies and return empty lists/errors:

- Cohorts
- Decisions  
- Exports
- Lineage
- Notifications

## Notes

For routers without file storage implementations, the pattern is:
1. Remove `db: Session = Depends(get_db)` 
2. Remove database model imports
3. Return empty lists or raise HTTPException with appropriate message
4. Document that feature is not available in file-storage mode
