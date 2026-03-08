# Fix: Evidence Tab Not Visible

## Issue
The Evidence tab (10th tab) was not visible in the Policy Workspace page.

## Root Cause
With 10 tabs total, the tabs were overflowing and the last tabs (Decisions and Evidence) were not visible on smaller screens or when tabs didn't fit.

## Solution
Made the Tabs component scrollable so all tabs are accessible:

```tsx
<Tabs 
  value={activeTab} 
  onChange={(e, v) => setActiveTab(v)}
  variant="scrollable"
  scrollButtons="auto"
  allowScrollButtonsMobile
>
```

## Changes Made
- Added `variant="scrollable"` to enable horizontal scrolling
- Added `scrollButtons="auto"` to show scroll buttons when needed
- Added `allowScrollButtonsMobile` to show scroll buttons on mobile devices

## Testing
1. Refresh the browser (or wait for hot reload)
2. Navigate to Policy Workspace
3. You should now see all 10 tabs:
   - Overview
   - Scope
   - Levers
   - Assumptions
   - Guardrails
   - Monitoring
   - Versions
   - Changelog
   - **Decisions** ← Should be visible
   - **Evidence** ← Should be visible now!

4. If tabs don't fit, you'll see left/right arrow buttons to scroll through tabs

## Next Steps
- Refresh your browser to see the fix
- The Evidence tab should now be visible and accessible


