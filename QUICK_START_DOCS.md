# Quick Start: Documentation Portal

## Issue: Application not loading on port 3051

The documentation portal needs to be started separately on port 3051.

## Solution: Start the Documentation Server

### Option 1: Use the start script (Recommended)
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./start-docs-server.sh
```

### Option 2: Use npm script
```bash
cd apps/web
npm run dev:docs
```

### Option 3: Access via main app (Port 3050)
If the main web server is running on port 3050, you can access documentation at:
```
http://localhost:3050/documentation
```

## Troubleshooting

1. **Port 3051 already in use?**
   - Check if another process is using port 3051: `lsof -ti:3051`
   - Kill the process if needed: `kill -9 $(lsof -ti:3051)`

2. **Server not starting?**
   - Make sure you're in the `apps/web` directory
   - Check that `vite.docs.config.ts` exists
   - Try: `npm install` to ensure dependencies are installed

3. **404 Error?**
   - Make sure you're accessing: `http://localhost:3051/documentation` (note the `/documentation` path)
   - The route is `/documentation`, not just the root

4. **Route not found?**
   - The documentation route is configured in `apps/web/src/App.tsx`
   - Make sure the route is: `<Route path="documentation" element={<DocumentationPortalPage />} />`

## Expected Behavior

Once the server starts, you should see:
- Vite dev server output
- "Local: http://localhost:3051"
- Navigate to: http://localhost:3051/documentation

The documentation portal includes:
- Product Overview
- System Architecture  
- Data Models
- Source Data Specifications
- Technical Documentation
