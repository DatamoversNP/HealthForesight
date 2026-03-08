# Troubleshooting: Application Not Loading

## Quick Checks

### 1. Is the Dev Server Running?

Check the terminal where you ran `npm run dev`. You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3050/
➜  Network: use --host to expose
```

If you see errors, share them.

### 2. Check Browser Console

Open browser DevTools (F12 or Cmd+Option+I) and check:
- **Console tab**: Look for red error messages
- **Network tab**: Check if files are loading (status 200) or failing (status 404/500)

### 3. Common Issues & Fixes

#### Issue: Blank White Screen
**Possible causes:**
- JavaScript error preventing render
- Missing component export
- Import path error

**Fix:**
1. Open browser console (F12)
2. Look for red error messages
3. Share the error message

#### Issue: "Cannot GET /" or 404
**Possible causes:**
- Dev server not running
- Wrong port

**Fix:**
```bash
# Make sure server is running
source ~/.nvm/nvm.sh
cd apps/web
npm run dev
```

#### Issue: "Failed to fetch" or Network errors
**Possible causes:**
- API server not running
- CORS issues

**Fix:**
- Start API server: `cd apps/api && python3 -m uvicorn uepi_api.main:app --reload --port 8000`
- Or ignore API errors for now (frontend should still load)

#### Issue: Build Errors in Terminal
**Possible causes:**
- Syntax errors
- Missing imports
- TypeScript errors

**Fix:**
- Check the terminal output for specific error messages
- Share the error message

### 4. Clear Cache and Restart

```bash
# Stop the dev server (Ctrl+C)

# Clear Vite cache
cd apps/web
rm -rf node_modules/.vite

# Restart
npm run dev
```

### 5. Check Browser

1. **Hard Refresh**: 
   - Mac: `Cmd + Shift + R`
   - Windows/Linux: `Ctrl + Shift + R`

2. **Try Incognito/Private Mode**: Rules out browser extensions

3. **Try Different Browser**: Rules out browser-specific issues

## Diagnostic Commands

Run this to check status:
```bash
./check-app-status.sh
```

## What to Share for Help

If the app still doesn't load, please share:

1. **Terminal output** from `npm run dev`
2. **Browser console errors** (F12 → Console tab)
3. **Network tab** errors (F12 → Network tab, look for red entries)
4. **What you see** in the browser (blank screen? error message? loading spinner?)

## Quick Test

Try accessing these URLs directly:
- http://localhost:3050/ (should show login or dashboard)
- http://localhost:3050/login (should show login page)

If these don't work, the issue is with the dev server or build process.


