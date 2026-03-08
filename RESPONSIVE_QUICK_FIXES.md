# Quick Responsive Fixes Guide

## 🔧 Common Responsive Issues & Quick Fixes

### 1. Button Touch Targets (Critical)

**Problem:** Buttons too small on mobile (< 44px)

**Fix:**
```tsx
<Button
  sx={{
    minHeight: 44, // Add this
    py: { xs: 1.5, md: 1 },
    fontSize: { xs: '14px', md: '16px' },
  }}
>
```

### 2. SVG/Chart Scaling

**Problem:** Charts overflow or are too small on mobile

**Fix:**
```tsx
<Box
  sx={{
    width: '100%',
    maxWidth: { xs: '100%', md: '800px' },
    height: { xs: '250px', md: '400px' }, // Reduce height on mobile
  }}
>
  <svg 
    viewBox="0 0 800 400" 
    preserveAspectRatio="xMidYMid meet" // Add this
  >
```

### 3. Typography Line Length

**Problem:** Text too wide, hard to read on desktop

**Fix:**
```tsx
<Typography
  sx={{
    maxWidth: { xs: '100%', md: '65ch' }, // Add this
    fontSize: { xs: '16px', md: '17px' },
  }}
>
```

### 4. Grid Columns

**Problem:** Too many columns on mobile

**Fix:**
```tsx
// Use MUI Grid
<Grid container spacing={3}>
  <Grid item xs={12} md={6} lg={4}>
    {/* Card */}
  </Grid>
</Grid>

// OR use ResponsiveGrid
<ResponsiveGrid 
  columns={{ xs: 1, md: 2, lg: 3 }}
>
```

### 5. Horizontal Scroll Prevention

**Problem:** Content overflows causing horizontal scroll

**Fix:**
```tsx
// Add to root Box
<Box
  sx={{
    overflowX: 'hidden', // Prevent horizontal scroll
    width: '100%',
    maxWidth: '100vw',
  }}
>
```

### 6. Table Mobile Handling

**Problem:** Tables too wide on mobile

**Fix:**
```tsx
<Box sx={{ overflowX: 'auto', width: '100%' }}>
  <Table>
    {/* Table content */}
  </Table>
</Box>
```

### 7. Side Panel Mobile Collapse

**Problem:** Side panels cramped on mobile

**Fix:**
```tsx
<Box 
  sx={{ 
    display: { xs: 'none', lg: 'block' }, // Hide on mobile
  }}
>
  {/* Side panel */}
</Box>

// OR use accordion
<Accordion sx={{ display: { xs: 'block', lg: 'none' } }}>
  {/* Mobile accordion */}
</Accordion>
```

## 🎯 File-Specific Fixes Needed

### High Priority Files
1. All visual components in `components/marketing/` - Add responsive containers
2. `HomePage.tsx` - Verify all sections responsive
3. `PlatformPage.tsx` - Grid layout fixes
4. `SolutionsPage.tsx` - Grid layout fixes
5. `HowItWorksPage.tsx` - Visual component scaling

### Medium Priority Files
6. `WhoItsForPage.tsx` - Table responsive handling
7. All blog/whitepaper pages - Typography max-width

## ✅ Testing Commands

After fixes, test with:
```bash
# Build and preview
cd apps/web
npm run build:marketing
npm run preview
```

Then test in Chrome DevTools at:
- Mobile: 360px, 390px, 414px
- Tablet: 768px, 834px
- Desktop: 1366px, 1440px, 1920px
