# Responsive Components Update Pattern

## 📋 Summary

- **29 visual components** need responsive containers
- **All Button components** need minHeight: 44
- **Long-form Typography** needs maxWidth: 65ch

## ✅ Pattern to Apply

### Visual Components (SVG/Charts)

**Find:**
```tsx
<Box
  sx={{
    width: '100%',
    height: '100%',
    p: 2,
  }}
>
  <Box component="svg" viewBox="..." sx={{ width: '100%', height: '100%', maxHeight: '...px' }}>
```

**Replace with:**
```tsx
<Box
  sx={{
    width: '100%',
    maxWidth: { xs: '100%', md: '800px' },
    height: { xs: '250px', md: '400px' },
    p: { xs: 2, md: 3 },
  }}
>
  <Box 
    component="svg" 
    viewBox="..." 
    preserveAspectRatio="xMidYMid meet"
    sx={{ width: '100%', height: '100%' }}
  >
```

### Button Components

**Find:**
```tsx
<Button
  sx={{
    px: 3,
    py: 1,
    fontSize: '16px',
  }}
>
```

**Replace with:**
```tsx
<Button
  sx={{
    minHeight: 44,
    px: { xs: 3, md: 4 },
    py: { xs: 1.5, md: 1 },
    fontSize: { xs: '14px', md: '16px' },
  }}
>
```

### Typography (Long-form content)

**Find:**
```tsx
<Typography
  variant="body1"
  sx={{
    fontSize: { xs: '16px', md: '17px' },
    lineHeight: 1.8,
  }}
>
```

**Replace with:**
```tsx
<Typography
  variant="body1"
  sx={{
    maxWidth: { xs: '100%', md: '65ch' },
    fontSize: { xs: '16px', md: '17px' },
    lineHeight: 1.8,
  }}
>
```

## 📁 Files to Update

### Visual Components (28 remaining)
All files in `apps/web/src/components/marketing/*Visual*.tsx` need the pattern above.

### Pages with Buttons
- HomePage.tsx (Partially done)
- PlatformPage.tsx
- SolutionsPage.tsx
- HowItWorksPage.tsx
- WhoItsForPage.tsx
- InsightsPage.tsx
- ExecutiveBriefCostOfUncertaintyPage.tsx
- WhitepaperElasticityPage.tsx
- BlogWhyPoliciesBackfirePage.tsx
- RequestDemoPage.tsx
- CompanyPage.tsx

### Pages with Long-form Typography
- ExecutiveBriefCostOfUncertaintyPage.tsx
- WhitepaperElasticityPage.tsx
- BlogWhyPoliciesBackfirePage.tsx
- PlatformPage.tsx (some sections)
- SolutionsPage.tsx (some sections)

## 🚀 Quick Update Commands

Use find/replace in your IDE with these patterns:

### Visual Components
1. Find: `width: '100%',\s+height: '100%'`
2. Replace: `width: '100%',\n        maxWidth: { xs: '100%', md: '800px' },\n        height: { xs: '250px', md: '400px' }`

### Buttons
1. Find: `sx=\{\{\s*px:`
2. Add: `minHeight: 44,` as first property

### Typography
1. Find: `fontSize: { xs: '16px', md: '17px' }`
2. Add before: `maxWidth: { xs: '100%', md: '65ch' },`
