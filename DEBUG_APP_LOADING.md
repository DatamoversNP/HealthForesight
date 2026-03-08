# Debug: Application Not Loading at http://localhost:3050

## Immediate Steps

### Step 1: Check Dev Server Status

In the terminal where you ran `npm run dev`, you should see output like:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3050/
```

**If you see errors**, copy and share them.

**If the server isn't running**, start it:
```bash
source ~/.nvm/nvm.sh
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

### Step 2: Check Browser Console

1. Open http://localhost:3050 in your browser
2. Press **F12** (or **Cmd+Option+I** on Mac) to open DevTools
3. Go to the **Console** tab
4. Look for **red error messages**

**Common errors to look for:**
- `Failed to load module`
- `Cannot find module`
- `ReferenceError: X is not defined`
- `SyntaxError`

**Share any red error messages you see.**

### Step 3: Check Network Tab

1. In DevTools, go to the **Network** tab
2. Refresh the page (F5 or Cmd+R)
3. Look for files with **red status codes** (404, 500, etc.)

**Share any failed requests you see.**

### Step 4: What Do You See?

- **Blank white screen?**
- **Error message?** (what does it say?)
- **Loading spinner that never stops?**
- **Nothing at all?** (page doesn't load)

## Quick Fixes to Try

### Fix 1: Clear Cache and Restart

```bash
# Stop the dev server (Ctrl+C in the terminal)

# Clear Vite cache
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
rm -rf node_modules/.vite

# Restart
source ~/.nvm/nvm.sh
npm run dev
```

### Fix 2: Hard Refresh Browser

- **Mac**: `Cmd + Shift + R`
- **Windows/Linux**: `Ctrl + Shift + R`

### Fix 3: Try Incognito/Private Mode

This rules out browser extensions interfering.

### Fix 4: Check Terminal Output

Look at the terminal where `npm run dev` is running. Are there any:
- **Build errors?**
- **TypeScript errors?**
- **Module not found errors?**

## What to Share

Please share:

1. **Terminal output** from `npm run dev` (any errors?)
2. **Browser console errors** (F12 → Console tab → red messages)
3. **What you see** in the browser (blank screen? error? loading?)
4. **Network tab errors** (F12 → Network tab → any red entries?)

This will help identify the exact issue.


