# Responsive Design Implementation Plan

## ✅ Completed

1. **Responsive Container System** - Created `ResponsiveContainer.tsx` with:
   - ResponsiveContainer component with breakpoint-based padding
   - ResponsiveGrid for automatic column adjustments
   - ResponsiveSection for consistent section spacing

2. **Mobile Navigation** - Updated `MarketingLayout.tsx`:
   - Hamburger menu for mobile (< 900px)
   - Drawer navigation with proper touch targets (48px minimum)
   - Responsive logo sizing
   - Footer converted to responsive grid layout

## 🚧 In Progress

### Next Priority Tasks

1. **HomePage Responsive Updates**
   - [ ] Hero typography scaling (already has some, verify all breakpoints)
   - [ ] Section spacing adjustments
   - [ ] Chart/visual component mobile optimization
   - [ ] Button sizing (ensure 44px min touch targets)

2. **Platform & Solutions Pages**
   - [ ] Grid layouts: 1 col mobile → 2 col tablet → 3 col desktop
   - [ ] Card components responsive padding/spacing
   - [ ] Visual components (SVG) scaling with viewBox
   - [ ] Typography line length limits

3. **How It Works & Who It's For**
   - [ ] Step/process visualizations mobile-friendly
   - [ ] Table components (horizontal scroll or card layout on mobile)
   - [ ] Accordion components properly sized

4. **Insights, Blog, Whitepaper Pages**
   - [ ] Side panel → accordion on mobile
   - [ ] Typography max-width (65-75ch for readability)
   - [ ] Table horizontal scroll implementation
   - [ ] Chart/infographic mobile simplification

5. **Chart/Visual Components**
   - [ ] All SVG components: ensure viewBox + responsive containers
   - [ ] Label readability on mobile (rotate, hide, or simplify)
   - [ ] Axis tick reduction on mobile
   - [ ] Font size scaling for mobile

## Implementation Approach

### Typography Standards
```tsx
// Headings
fontSize: { xs: '2rem', md: '2.5rem', lg: '3rem' }

// Body text
maxWidth: { xs: '100%', md: '65ch' } // ~65-75 characters
fontSize: { xs: '16px', md: '17px' }
lineHeight: { xs: 1.7, md: 1.8 }
```

### Grid Patterns
```tsx
// 3-column → 2-column → 1-column
<ResponsiveGrid 
  columns={{ xs: 1, md: 2, lg: 3 }}
  gap={{ xs: 2, md: 3, lg: 4 }}
>
```

### Touch Targets
```tsx
// All buttons/interactive elements
minHeight: 44,
minWidth: 44,
```

### Chart/Visual Scaling
```tsx
// SVG containers
<Box
  sx={{
    width: '100%',
    maxWidth: { xs: '100%', md: '800px' },
    height: { xs: '250px', md: '400px' },
  }}
>
  <svg viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet">
```

## Breakpoint Testing Checklist

### Mobile (360×640, 390×844, 414×896)
- [ ] No horizontal scrolling
- [ ] Navigation drawer works
- [ ] All text readable (min 14px)
- [ ] Buttons 44px+ height
- [ ] Charts/visuals readable or simplified
- [ ] Forms/inputs usable

### Tablet (768×1024, 834×1112)
- [ ] 2-column grids work well
- [ ] Typography not too wide
- [ ] Charts have adequate space
- [ ] Side panels start appearing where appropriate

### Desktop (1366×768, 1440×900, 1920×1080, 2560×1440)
- [ ] 3-4 column grids appropriate
- [ ] Max-width containers prevent text from spreading too wide
- [ ] Side panels sticky and functional
- [ ] All interactive elements work with mouse

## Key Files to Update

1. Pages:
   - `HomePage.tsx`
   - `PlatformPage.tsx`
   - `SolutionsPage.tsx`
   - `HowItWorksPage.tsx`
   - `WhoItsForPage.tsx`
   - `InsightsPage.tsx`
   - `BlogWhyPoliciesBackfirePage.tsx`
   - `WhitepaperElasticityPage.tsx`
   - `ExecutiveBriefCostOfUncertaintyPage.tsx`

2. Visual Components:
   - All components in `components/marketing/` with SVG/charts
   - Update to use viewBox and responsive containers
   - Add mobile-specific label handling

3. Layout Components:
   - ✅ `MarketingLayout.tsx` - DONE
   - ✅ `ResponsiveContainer.tsx` - DONE

## Quality Assurance

After implementation:
1. Test all breakpoints in Chrome DevTools
2. Check Lighthouse mobile scores
3. Verify no horizontal scrolling
4. Test touch interactions on mobile device
5. Verify all CTAs accessible on mobile
