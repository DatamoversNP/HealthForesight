# Start Frontend Web Application

## Quick Start

The frontend web application needs to be started separately from the API server.

### Start Command

Open a **NEW terminal window** and run:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

### What to Expect

You should see output like:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3050/
  ➜  Network: use --host to expose
```

### Access the Application

Once you see "ready", open your browser to:
**http://localhost:3050**

### Keep Terminal Open

**Important**: Keep the terminal window open while using the application. The web server needs to keep running.

To stop the server, press `Ctrl+C` in the terminal.

## Current Status

- ✅ **API Server**: Running on port 8000
- ❌ **Web Server**: Needs to be started on port 3050

## Troubleshooting

### Port 3050 already in use
```bash
# Kill existing process
lsof -ti:3050 | xargs kill -9
# Then start again
npm run dev
```

### npm not found
Install Node.js from https://nodejs.org/ (LTS version)

### Dependencies missing
```bash
cd apps/web
npm install
npm run dev
```

### Build errors
Check the terminal output for TypeScript or compilation errors
