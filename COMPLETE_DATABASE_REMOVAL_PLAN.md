# Complete Database Removal Plan

## Strategy

Since the user wants to remove ALL database dependencies, we should:

1. **All Routers** - Remove `get_db`, `Session`, database model imports
   - Return empty lists or raise HTTPException with 503/404 for features not yet implemented
   
2. **Main.py** - Remove database conditionals, always use file storage routers
   
3. **Database Module** - Keep for now (might be imported elsewhere) but mark as deprecated
   
4. **Models** - Keep (might be used for validation) but remove from router imports

## Routers to Update

- cohorts.py
- decisions.py  
- exports.py
- lineage.py
- notifications.py
- analyses.py (partial - needs completion)

Let's do this systematically!
