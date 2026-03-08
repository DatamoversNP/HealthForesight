# Fix 404 Error on Vercel

Your site deployed successfully but shows a 404. This is a routing issue. Here's how to fix it:

## Quick Fix: Redeploy with Updated Config

I've updated your `vercel.json` to fix the routing. Now redeploy:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
npx vercel --prod
```

## What I Fixed

1. Added `routes` configuration (in addition to `rewrites`)
2. Added `cleanUrls: true` for better routing
3. Ensured all routes redirect to `index.html` for React Router

## Alternative: Fix via Vercel Dashboard

1. Go to: https://vercel.com/health-foresight/healthforesight-marketing/settings
2. Navigate to "Build & Development Settings"
3. Verify:
   - Build Command: `npm run build:marketing`
   - Output Directory: `dist-marketing`
4. Go to "Deployments" tab
5. Click "Redeploy" on the latest deployment

## Verify Build Output

Before redeploying, make sure the build works locally:

```bash
cd apps/web
npm run build:marketing
ls -la dist-marketing
```

You should see:
- `index.html`
- `assets/` folder
- Other files

If `dist-marketing` is empty or missing files, the build failed.

## Check Build Logs

1. Go to: https://vercel.com/health-foresight/healthforesight-marketing
2. Click on the latest deployment
3. Check "Build Logs" for errors

## Common Issues

### Issue 1: Build Failed
- Check build logs in Vercel dashboard
- Test build locally: `npm run build:marketing`
- Fix any TypeScript or build errors

### Issue 2: Wrong Output Directory
- Verify `dist-marketing` folder exists after build
- Check `vercel.json` has correct `outputDirectory`

### Issue 3: Missing index.html
- The build should create `dist-marketing/index.html`
- If missing, check `vite.marketing.config.ts` build settings

## After Redeploy

Once you redeploy, your site should work at:
- https://healthforesight-marketing.vercel.app
- https://healthforesight-marketing-qt67odfd4-health-foresight.vercel.app

All routes should work (/, /platform, /solutions, etc.)
