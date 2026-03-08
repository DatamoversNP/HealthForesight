# Marketing Website Setup - Troubleshooting

## The Problem

When you run `npm run dev:marketing`, you should see the **marketing website** (public-facing site with Platform, Solutions, etc.), NOT the main application.

## How It Works

The marketing site uses:
- **Entry Point**: `src/main-marketing.tsx` (loads `AppMarketing.tsx`)
- **HTML File**: `index-marketing.html` (points to `main-marketing.tsx`)
- **Port**: 3052
- **Routes**: All routes are at root level (`/`, `/platform`, `/solutions`, etc.)

The main app uses:
- **Entry Point**: `src/main.tsx` (loads `App.tsx`)
- **HTML File**: `index.html` (points to `main.tsx`)
- **Port**: 3050
- **Routes**: Protected routes with authentication

## Verification Steps

1. **Check which command you're running**:
   ```bash
   npm run dev:marketing  # Marketing site (port 3052)
   npm run dev            # Main app (port 3050)
   ```

2. **Check the browser console**:
   - Open DevTools → Console
   - Look for which entry point loaded
   - Marketing site should load `main-marketing.tsx`
   - Main app loads `main.tsx`

3. **Check the URL**:
   - Marketing site: `http://localhost:3052`
   - Main app: `http://localhost:3050`

4. **Check the page title**:
   - Marketing site: "HealthForesight - Decision Intelligence for Utilization Policy Impact"
   - Main app: "HealthForesight by DataMovers - Decision Intelligence for Healthcare"

## If You Still See the Main App

1. **Clear browser cache** and hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

2. **Check if the HTML file swap worked**:
   - The Vite plugin should automatically copy `index-marketing.html` to `index.html` when you run `dev:marketing`
   - Check `apps/web/index.html` - it should have:
     ```html
     <script type="module" src="/src/main-marketing.tsx"></script>
     ```
   - NOT:
     ```html
     <script type="module" src="/src/main.tsx"></script>
     ```

3. **Restart the dev server**:
   ```bash
   # Stop the server (Ctrl+C)
   npm run dev:marketing
   ```

4. **Check for port conflicts**:
   - Make sure nothing else is using port 3052
   - Try a different port if needed

## Manual Fix (If Needed)

If the automatic HTML swap isn't working, you can manually ensure the correct file:

```bash
cd apps/web
# Backup original if needed
cp index.html index.html.app-backup
# Use marketing HTML
cp index-marketing.html index.html
# Then run
npm run dev:marketing
```

## Expected Behavior

When you visit `http://localhost:3052`, you should see:
- ✅ Sticky navigation header with "HealthForesight" logo
- ✅ Navigation items: Platform, Solutions, How It Works, Who It's For, Insights, Company
- ✅ "Request Demo" button in header
- ✅ Home page with hero section, market reality, four pillars
- ✅ NO login page
- ✅ NO application dashboard
- ✅ NO sidebar navigation

If you see login pages, dashboards, or the application interface, you're looking at the main app, not the marketing site.
