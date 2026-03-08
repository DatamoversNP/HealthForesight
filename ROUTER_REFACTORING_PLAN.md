# Router Refactoring Plan - File Storage Only

## Priority Order

### ✅ 1. Auth Router (EASY - Already has fallback)
- Already works without database
- Just needs to remove `get_db` dependency and database queries
- Use `get_demo_current_user` directly

### 🔄 2. Analyses Router (MEDIUM - Partial file storage support)
- `list_analyses` - Already uses file storage ✅
- `create_baseline_analysis` - Already uses file storage ✅
- `create_impact_analysis` - Needs conversion (uses Policy, PolicyVersion, Analysis models)
- `create_simulate_analysis` - Needs conversion
- `get_analysis` - Needs conversion
- `get_analysis_results` - Needs conversion (uses AnalysisResultIndex)
- Other endpoints - Need review

### ⏸️ 3. Other Routers (LOW PRIORITY - Return empty/errors)
- Scorecards - Return empty lists
- Cohorts - Return empty lists
- Decisions - Return empty lists
- Exports - Return empty lists
- Lineage - Return empty lists
- Notifications - Return empty lists

## Strategy

For routers that don't have file storage implementations:
1. Remove `db: Session = Depends(get_db)` parameter
2. Remove database queries
3. Return empty lists or raise HTTPException with 503 "Feature not available in file-storage mode"

Let's start with auth router first!
