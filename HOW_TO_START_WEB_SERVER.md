# How to Start Web Server

## Simple Method (Recommended)

Open a terminal and run this command:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./START_WEB_SERVER.sh
```

## Step-by-Step Manual Method

If the script doesn't work, follow these steps:

### Step 1: Open Terminal
Open Terminal on your Mac

### Step 2: Navigate to Project Directory
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
```

### Step 3: Go to Web Directory
```bash
cd apps/web
```

### Step 4: Install Dependencies (First Time Only)
```bash
npm install
```
*Note: This only needs to be run once. Skip if you've already done this.*

### Step 5: Start the Server
```bash
npm run dev
```

## What to Expect

Once the server starts, you should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3050/
  ➜  Network: use --host to expose
```

## Access Your Application

Open your browser and go to:
**http://localhost:3050**

## Troubleshooting

### If you see "command not found: npm"
You need to install Node.js first:
1. Go to https://nodejs.org/
2. Download and install Node.js (LTS version)
3. Restart your terminal and try again

### If port 3050 is already in use
Stop the existing process:
```bash
lsof -ti:3050 | xargs kill -9
```
Then try starting again.

### If you see dependency errors
Run this in the `apps/web` directory:
```bash
npm install
```

## Keep the Terminal Open

**Important**: Keep the terminal window open while using the application. The web server needs to keep running.

To stop the server, press `Ctrl+C` in the terminal.
