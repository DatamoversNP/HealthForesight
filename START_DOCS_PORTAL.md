# How to Start Documentation Portal on Port 3051

## Problem
The documentation portal is not loading because the server is not running on port 3051.

## Solution

### Step 1: Start the Documentation Server

Open a terminal and run:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
npm run dev:docs
```

**OR** use the convenience script:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./start-docs-server.sh
```

### Step 2: Wait for Server to Start

You should see output like:
```
  VITE v5.0.8  ready in xxx ms

  ➜  Local:   http://localhost:3051/
  ➜  Network: use --host to expose
```

### Step 3: Access Documentation

Open your browser and navigate to:
```
http://localhost:3051/documentation
```

**Important**: Make sure to include `/documentation` in the URL path!

## Alternative: Use Main App (Port 3050)

If your main web server is already running on port 3050, you can access the documentation there:

```
http://localhost:3050/documentation
```

Just click "Documentation" in the navigation menu.

## Troubleshooting

1. **Port 3051 already in use?**
   ```bash
   lsof -ti:3051
   # If a process is found, kill it:
   kill -9 $(lsof -ti:3051)
   ```

2. **Module not found errors?**
   ```bash
   cd apps/web
   npm install
   ```

3. **Config file not found?**
   - Make sure `vite.docs.config.ts` exists in `apps/web/`
   - If missing, it's configured to use port 3051

4. **Still not working?**
   - Check browser console for errors (F12)
   - Check terminal output for Vite errors
   - Verify the route exists in `apps/web/src/App.tsx`

## What You Should See

Once loaded, the documentation portal shows:
- Left sidebar with navigation (Product Overview, Architecture, Data Models, etc.)
- Main content area with tabs for each section
- Code examples, tables, and detailed documentation
- All documentation sections are interactive and expandable
