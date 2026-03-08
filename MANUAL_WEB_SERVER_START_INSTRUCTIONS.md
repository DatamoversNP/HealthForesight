# How to Manually Start the Web Server

## Step-by-Step Instructions

### Step 1: Open Terminal
- On Mac: Press `Cmd + Space`, type "Terminal", press Enter
- Or go to Applications → Utilities → Terminal

### Step 2: Navigate to the Web Directory
Copy and paste this command into Terminal:
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
```

Press **Enter**

### Step 3: Start the Web Server
Copy and paste this command:
```bash
npm run dev
```

Press **Enter**

### Step 4: Wait for Server to Start
You should see output like this:
```
  VITE v5.x.x  ready in 1234 ms

  ➜  Local:   http://localhost:3050/
  ➜  Network: use --host to expose
```

### Step 5: Open Your Browser
Once you see the "ready" message, open your browser and go to:
**http://localhost:3050**

## Visual Guide

Here's what it will look like in Terminal:

```
your-computer:~ your-name$ cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
your-computer:web your-name$ npm run dev

> uepi-web@0.1.0 dev
> vite

  VITE v5.x.x  ready in 1234 ms

  ➜  Local:   http://localhost:3050/
```

## Important Notes

1. **Keep Terminal Open**: Don't close the Terminal window while using the app
2. **Stop Server**: Press `Ctrl + C` in Terminal to stop the server
3. **Error Messages**: If you see errors, make sure you're in the correct directory

## Troubleshooting

### "Command not found: npm"
- You need to install Node.js: https://nodejs.org/
- Download and install the LTS version
- Restart Terminal after installing

### "Port 3050 is already in use"
- Stop any existing server: Press `Ctrl + C` in Terminal
- Or use a different port: `npm run dev -- --port 3000`

### "Cannot find module"
- Run: `npm install` first, then `npm run dev`

## Summary

**Three commands to run:**
1. `cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"`
2. `npm run dev`
3. Open http://localhost:3050 in browser

That's it! The web server will start and the application will load.
