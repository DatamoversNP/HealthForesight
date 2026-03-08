# How to Use the API Restart Scripts

I've created simple scripts to automate restarting the API server. You don't need to be a command line expert!

## Option 1: Restart API (Interactive - Shows Output)

**File:** `restart-api.sh`

**How to use:**

### Method A: Double-click (Easiest!)
1. Open Finder
2. Navigate to this project folder
3. Find `restart-api.sh`
4. Right-click → Open With → Terminal
5. The API will start and show output in the terminal window

### Method B: From Terminal
1. Open Terminal
2. Type: `cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"`
3. Type: `./restart-api.sh`
4. Press Enter

**What it does:**
- Stops any running API server
- Starts the API server
- Shows all output in the terminal
- Press Ctrl+C to stop it

---

## Option 2: Restart API (Background - Runs in Background)

**File:** `restart-api-background.sh`

**How to use:**

1. Open Terminal
2. Type: `cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"`
3. Type: `./restart-api-background.sh`
4. Press Enter

**What it does:**
- Stops any running API server
- Starts the API server in the background
- Returns control to you (you can keep using the terminal)
- Logs are saved to `api-server.log`

**To stop it later:**
- Use: `./stop-api.sh`
- Or check the PID shown when you started it

---

## Option 3: Stop API Only

**File:** `stop-api.sh`

**How to use:**

1. Open Terminal
2. Type: `cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"`
3. Type: `./stop-api.sh`
4. Press Enter

**What it does:**
- Stops the running API server
- Doesn't start a new one

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start API (see output) | `./restart-api.sh` |
| Start API (background) | `./restart-api-background.sh` |
| Stop API | `./stop-api.sh` |
| View logs (if background) | `tail -f api-server.log` |

## Troubleshooting

### "Permission denied" error
Run this once: `chmod +x restart-api.sh restart-api-background.sh stop-api.sh`

### Script not found
Make sure you're in the project directory:
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
```

### API won't start
- Check if Python 3.11+ is installed: `python3 --version`
- Check if you're in the right directory
- Check the error messages in the terminal

### Port 8000 already in use
The scripts automatically stop any process on port 8000. If it still fails, run:
```bash
lsof -ti:8000 | xargs kill -9
```

## After Restarting

Once the API is restarted:
1. ✅ Open browser: http://localhost:8000/docs (should show FastAPI docs)
2. ✅ Go to: http://localhost:3050/policies
3. ✅ Click Psychology icon (🧠) on any policy
4. ✅ Predicted impact should now work!
