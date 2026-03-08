# Fix 404 Error - Final Solution

The issue is that Vercel can't find `index.html`. The build creates `index-marketing.html` but Vercel needs `index.html`.

## Quick Fix: Manual Rename After Build

Since the plugin might have permission issues, here's the simplest fix:

### Option 1: Add Post-Build Script

Add this to `package.json`:

```json
"scripts": {
  "build:marketing": "vite build --config vite.marketing.config.ts",
  "postbuild:marketing": "cd dist-marketing && mv index-marketing.html index.html 2>/dev/null || true"
}
```

Then rebuild and redeploy:
```bash
npm run build:marketing
npx vercel --prod
```

### Option 2: Manual Fix Before Deploy

Before deploying, manually rename the file:

```bash
cd apps/web/dist-marketing
mv index-marketing.html index.html
cd ..
npx vercel --prod
```

### Option 3: Fix in Vercel Build Settings

1. Go to: https://vercel.com/health-foresight/healthforesight-marketing/settings
2. Go to "Build & Development Settings"
3. Change "Build Command" to:
   ```
   npm run build:marketing && cd dist-marketing && mv index-marketing.html index.html
   ```
4. Save and redeploy

## Recommended: Update package.json

I'll update your package.json to automatically rename the file after build.
