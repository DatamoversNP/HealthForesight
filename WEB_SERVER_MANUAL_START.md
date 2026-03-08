# Web Server - Manual Start Required

## Issue
The web server cannot be started automatically due to sandbox/permission restrictions on port 3050.

## Solution: Start Manually

**You need to start the web server manually in a Terminal window.**

### Steps:

1. **Open Terminal** (new window)

2. **Run these commands:**
   ```bash
   cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
   npm run dev
   ```

3. **Wait 10-15 seconds** - You should see:
   ```
   VITE v5.x.x  ready in xxx ms
   ➜  Local:   http://localhost:3050/
   ```

4. **Open your browser** to: **http://localhost:3050**

## Alternative: Use Different Port

If port 3050 doesn't work, you can use a different port:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
npm run dev -- --port 3000
```

Then access: **http://localhost:3000**

## Current Status

- ✅ **API Server**: Running on port 8000
- ❌ **Web Server**: Needs manual start (sandbox restriction)

## Why Manual Start?

The automated script can't bind to port 3050 due to macOS/system permissions. Starting it manually in your own terminal session will work.

**Start the web server manually and the application will load!**
