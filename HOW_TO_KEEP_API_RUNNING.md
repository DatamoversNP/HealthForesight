# How to Keep API Running

## ⚠️ Important: Don't Stop the API!

When you see "Press Ctrl+C to stop" - **DON'T press Ctrl+C** if you want to use the application!

The API needs to keep running for the frontend to work.

## ✅ Solution: Two Options

### Option 1: Start API in Background (Recommended)

**Run this script:**
```bash
./start_api_background.sh
```

This will:
- ✅ Start API in the background
- ✅ Keep it running even if you close the terminal
- ✅ Show you the process ID
- ✅ Give you commands to stop it later

**To stop it later:**
```bash
lsof -ti:8000 | xargs kill -9
```

### Option 2: Use Separate Terminal Windows

**Terminal 1 - API Server (Keep this running!):**
```bash
./start_api_local.sh
# DON'T press Ctrl+C - leave this running!
```

**Terminal 2 - Web Server (if needed):**
```bash
./START_WEB_SERVER.sh
# DON'T press Ctrl+C - leave this running!
```

**Terminal 3 - Your commands:**
```bash
# Run diagnostics, check logs, etc.
./diagnose_api_network.sh
./view_logs.sh api
```

## 🔍 Check if API is Running

**Quick check:**
```bash
lsof -ti:8000
```

If you see a process ID, the API is running!

**Test API:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","service":"uepi-api"}`

## 📊 Monitor API

**View logs in real-time:**
```bash
./view_logs.sh api
```

**View startup log (if using background script):**
```bash
tail -f logs/api_startup.log
```

## 🛑 How to Stop API

**If running in background:**
```bash
lsof -ti:8000 | xargs kill -9
```

**If running in foreground:**
- Press `Ctrl+C` in the terminal where it's running

## 💡 Best Practice

**Use the background script:**
```bash
./start_api_background.sh
```

This way:
- ✅ API keeps running
- ✅ You can use your terminal for other commands
- ✅ Frontend will always have API available
- ✅ Easy to stop when needed

## ✅ After Starting API

1. **Wait 15 seconds** for startup
2. **Verify it's running:**
   ```bash
   ./diagnose_api_network.sh
   ```
3. **Open frontend:** http://localhost:3050
4. **Data should load!**

## 📋 Summary

**The API must stay running!**

- ❌ **Don't**: Press Ctrl+C when you see "Press Ctrl+C to stop"
- ✅ **Do**: Use `./start_api_background.sh` or keep terminal open
- ✅ **Do**: Use separate terminal windows for commands

**Remember:** The API is a server - it needs to keep running for the frontend to work!

