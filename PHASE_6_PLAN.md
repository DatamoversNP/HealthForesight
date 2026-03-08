# Phase 6: Substitution Detection & Provider Segmentation UI Integration

## Overview

Phase 6 completes the **Substitution Detection** and **Provider Segmentation** capabilities by adding comprehensive UI components and integration. While the backend analytics are complete, the frontend needs to be built to visualize and interact with these results.

## Current Status

### ✅ Completed (Backend - Phase 6 Backend was already done)
- Substitution detection engine (`SubstitutionDetector`)
- Provider segmentation engine (`ProviderSegmentation`)
- Worker tasks integration
- Result storage in analysis results

### ⏳ To Do (Frontend - This Phase 6)
- UI components for substitution results
- UI components for provider segmentation
- Integration with analysis workspace
- Visualization of top pathways
- Archetype drill-down views

## Phase 6 Goals

### 1. Substitution Detection UI
**Goal**: Display substitution analysis results with filtering and drill-down

**Components to Build**:
- `SubstitutionResultsTable.tsx` - Table showing detected substitutions
  - Columns: Code, Classification, Pre/Post metrics, Substitution Rate, Confidence, Statistical Rank
  - Filtering by: Code group, Classification, Confidence threshold
  - Sorting by: Statistical rank, confidence, magnitude
  - Drill-down to lag analysis and pathway details

- `TopSubstitutionPathways.tsx` - Visualization of top pathways
  - Network diagram or hierarchical view
  - Shows "from X → to Y" relationships
  - Aggregate metrics per pathway
  - Code group groupings

- `SubstitutionLagAnalysis.tsx` - Time-series view
  - Shows substitution patterns over 30/60/90 day windows
  - Claim count and allowed amount trends
  - Highlights delayed substitution patterns

### 2. Provider Segmentation UI
**Goal**: Display provider archetypes and enable exploration

**Components to Build**:
- `ProviderArchetypesOverview.tsx` - Summary cards
  - Count of providers per archetype (COMPLIERS, CIRCUMVENTERS, etc.)
  - Average metrics per archetype
  - Visual distribution (pie chart or bar chart)

- `ProviderArchetypesTable.tsx` - Detailed table
  - Archetype details with metrics
  - Top features per archetype
  - Stability scores
  - Provider count per archetype

- `ProviderArchetypeDetail.tsx` - Drill-down view
  - List of providers in an archetype
  - Provider-level metrics (allowed delta, claim count delta, POS shift)
  - Feature importance explanations
  - Export functionality

### 3. Integration Points

**Analysis Workspace Integration**:
- Add substitution and segmentation tabs to analysis results view
- Link from impact analysis to substitution/segmentation results
- Show substitution and segmentation in analysis summary

**Policy Impact View Integration**:
- Display substitution summary in policy impact dashboard
- Show provider response distribution (from segmentation)
- Link to detailed views

**API Integration**:
- Use existing `/analyses/{id}/results` endpoint with `result_type=SUBSTITUTION` or `PROVIDER_SEGMENTATION`
- Add helper methods to API client if needed

## Implementation Plan

### Step 1: API Client Enhancements (30 min)
- Add helper methods for substitution/segmentation results
- Ensure result type filtering works correctly

### Step 2: Substitution UI Components (2-3 hours)
- Build `SubstitutionResultsTable.tsx`
- Build `TopSubstitutionPathways.tsx`
- Build `SubstitutionLagAnalysis.tsx`
- Style with HealthForesight theme

### Step 3: Provider Segmentation UI Components (2-3 hours)
- Build `ProviderArchetypesOverview.tsx`
- Build `ProviderArchetypesTable.tsx`
- Build `ProviderArchetypeDetail.tsx`
- Style with HealthForesight theme

### Step 4: Integration (1-2 hours)
- Add tabs to analysis workspace
- Integrate with policy impact view
- Add navigation links

### Step 5: Testing & Polish (1 hour)
- Test with real analysis results
- Verify filtering and sorting
- Check responsive design
- Fix any edge cases

## Expected Deliverables

### UI Components
- ✅ 6 new React components (3 for substitution, 3 for segmentation)
- ✅ Integration in analysis workspace
- ✅ Integration in policy impact view

### User Experience
- Users can view substitution results with filtering
- Users can explore top substitution pathways
- Users can see provider archetype distribution
- Users can drill down to individual provider details
- Visualizations are clear and actionable

## Success Criteria

1. ✅ Substitution results are clearly displayed with all key metrics
2. ✅ Top pathways are visualized intuitively
3. ✅ Provider archetypes are easy to understand
4. ✅ Drill-down functionality works smoothly
5. ✅ Integration points are intuitive
6. ✅ Components follow HealthForesight design system

## Timeline Estimate

**Total Time**: 6-9 hours
- API client: 30 min
- Substitution UI: 2-3 hours
- Segmentation UI: 2-3 hours
- Integration: 1-2 hours
- Testing: 1 hour

## Files to Create

### New Components
- `apps/web/src/components/analytics/SubstitutionResultsTable.tsx`
- `apps/web/src/components/analytics/TopSubstitutionPathways.tsx`
- `apps/web/src/components/analytics/SubstitutionLagAnalysis.tsx`
- `apps/web/src/components/analytics/ProviderArchetypesOverview.tsx`
- `apps/web/src/components/analytics/ProviderArchetypesTable.tsx`
- `apps/web/src/components/analytics/ProviderArchetypeDetail.tsx`

### Modified Files
- `apps/web/src/lib/api.ts` - Add helper methods if needed
- `apps/web/src/pages/AnalysisWorkspacePage.tsx` - Add tabs for substitution/segmentation
- `apps/web/src/pages/PolicyImpactPage.tsx` - Add substitution/segmentation sections (if exists)

## Dependencies

### Required
- ✅ Backend substitution detection (completed)
- ✅ Backend provider segmentation (completed)
- ✅ Analysis results storage (completed)
- ✅ Material-UI components
- ✅ HealthForesight theme

### Optional Enhancements
- Chart library for pathway visualization (vis.js, cytoscape.js, or MUI Charts)
- Export functionality (CSV/Excel export)
- Advanced filtering UI

## Next Phase Preview

After Phase 6 completion:
- **Phase 7**: Enhanced What-If Scenarios
  - Integration with latest elasticity models
  - Multi-scenario comparison
  - Scenario sensitivity analysis
  - Improved simulation accuracy using learned models
