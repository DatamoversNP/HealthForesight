# Database Removal Priority

## High Priority (Active Routers)
1. **analyses** - Has file storage fallback, but still uses database models
2. **scorecards** - Uses database, might not have file storage alternative
3. **auth** - Uses database for user/tenant lookup

## Medium Priority  
4. **cohorts** - Uses database
5. **decisions** - Uses database
6. **exports** - Uses database
7. **lineage** - Uses database
8. **notifications** - Uses database

## Strategy
Since the system is file-storage only, I should:
1. Remove database code from analyses router (already has file storage support)
2. Check if other routers can be simplified or if they're even needed
3. Remove database dependencies from auth (uses file storage for demo user)

Let me start with analyses router since it already has file storage code.
