# HealthForesight Website Separation Plan

## Overview

Separating the marketing website into a standalone `healthforesight-Website` folder outside the core application codebase for:
- ✅ Clean separation of concerns
- ✅ Independent deployment
- ✅ Easier maintenance
- ✅ Clearer project structure

## Folder Structure

```
healthforesight-Website/
├── src/
│   ├── pages/           # All marketing pages
│   ├── components/      # All marketing components
│   ├── theme/           # Theme configuration
│   ├── App.tsx          # Main app (routes)
│   └── main.tsx         # Entry point
├── index.html
├── package.json         # Standalone dependencies
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript config
├── vercel.json          # Deployment config
├── .gitignore
└── README.md
```

## Files to Copy/Move

### Pages (11 files)
- HomePage.tsx
- PlatformPage.tsx
- SolutionsPage.tsx
- HowItWorksPage.tsx
- WhoItsForPage.tsx
- InsightsPage.tsx
- WhitepaperElasticityPage.tsx
- BlogWhyPoliciesBackfirePage.tsx
- ExecutiveBriefCostOfUncertaintyPage.tsx
- CompanyPage.tsx
- RequestDemoPage.tsx

### Components (70+ files)
- All components from `src/components/marketing/`
- ErrorBoundary.tsx (from `src/components/`)

### Theme & Styles
- `src/theme/healthForesightTheme.ts`
- `src/index.css`
- `src/marketing-animations.css`

## Import Path Updates Needed

All imports in marketing files need to be updated from:
- `../../theme/` → `../theme/`
- `../../components/marketing/` → `../components/`
- `../../components/ErrorBoundary` → `../components/ErrorBoundary`
- `../pages/marketing/` → `../pages/`

## Dependencies

All dependencies are self-contained. Only marketing-related dependencies:
- React + React DOM
- React Router DOM
- Material-UI (MUI)
- GSAP (animations)
- TypeScript + Vite

## Next Steps

1. ✅ Created folder structure
2. ✅ Created config files (package.json, vite.config.ts, tsconfig.json)
3. ⏭️ Copy all marketing pages and components
4. ⏭️ Update all imports to relative paths
5. ⏭️ Test build locally
6. ⏭️ Verify all dependencies are included

## Deployment

After separation, deployment is simplified:
- Single `healthforesight-Website` folder
- Standalone `package.json` with all dependencies
- No dependency on core application
- Direct deployment from `healthforesight-Website/` directory

---

**Status**: Config files created. Ready to copy marketing files and update imports.
