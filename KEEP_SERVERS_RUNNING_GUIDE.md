# Guide: Keeping Servers Running

This guide provides multiple methods to keep your servers running even when you step away from your system.

## 🎯 Quick Start (Recommended)

### Option 1: PM2 (Best for Production-like Setup)

PM2 is a process manager that keeps servers running, auto-restarts on crashes, and provides excellent monitoring.

```bash
# 1. Setup PM2 (one-time)
./setup-pm2.sh

# 2. Start servers
./START_WITH_PM2.sh

# 3. Save PM2 config (auto-start on reboot)
pm2 save
pm2 startup
```

**Benefits:**
- ✅ Auto-restart on crashes
- ✅ Process monitoring
- ✅ Log management
- ✅ Auto-start on system reboot
- ✅ Memory limit protection

### Option 2: Background Scripts (Simple)

```bash
# Start both servers in background
./START_SERVERS_BACKGROUND.sh

# Check status
./CHECK_SERVERS.sh

# Stop servers
./STOP_SERVERS.sh
```

**Benefits:**
- ✅ Simple, no extra dependencies
- ✅ Logs saved to `logs/` directory
- ✅ Easy to start/stop

## 📋 Detailed Methods

### Method 1: PM2 Process Manager (Recommended)

**Installation:**
```bash
npm install -g pm2
./setup-pm2.sh
```

**Usage:**
```bash
# Start servers
./START_WITH_PM2.sh
# or
pm2 start ecosystem.config.js

# View status
pm2 status

# View logs
pm2 logs

# Monitor (real-time)
pm2 monit

# Stop servers
pm2 stop ecosystem.config.js

# Restart servers
pm2 restart ecosystem.config.js

# Save configuration (auto-start on reboot)
pm2 save
pm2 startup  # Follow the instructions it prints
```

**PM2 Commands:**
- `pm2 list` - List all processes
- `pm2 logs [app-name]` - View logs for specific app
- `pm2 restart all` - Restart all apps
- `pm2 delete all` - Stop and delete all apps
- `pm2 info [app-name]` - Detailed info about an app

### Method 2: Background Scripts with nohup

**Usage:**
```bash
# Start servers
./START_SERVERS_BACKGROUND.sh

# Check if running
./CHECK_SERVERS.sh

# View logs
tail -f logs/api.log
tail -f logs/frontend.log

# Stop servers
./STOP_SERVERS.sh
```

**Manual nohup (if you prefer):**
```bash
# API Server
cd apps/api
export PYTHONPATH="../../apps/api/src:../../packages/common/src:$PYTHONPATH"
nohup python3 -m uvicorn uepi_api.main:app --reload --port 8000 > ../../logs/api.log 2>&1 &

# Frontend Server
cd apps/web
nohup npm run dev > ../../logs/frontend.log 2>&1 &
```

### Method 3: tmux (Terminal Multiplexer)

**Installation:**
```bash
# macOS
brew install tmux

# Or use built-in (if available)
```

**Usage:**
```bash
# Start tmux session
tmux new -s servers

# In tmux, start API server
cd apps/api
export PYTHONPATH="../../apps/api/src:../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --reload --port 8000

# Split window (Ctrl+B, then ")
# Start frontend in new pane
cd apps/web
npm run dev

# Detach from tmux (Ctrl+B, then d)
# Servers keep running!

# Reattach later
tmux attach -t servers

# List sessions
tmux ls

# Kill session
tmux kill-session -t servers
```

### Method 4: screen (Terminal Multiplexer)

**Usage:**
```bash
# Start screen session
screen -S servers

# Start API server
cd apps/api
export PYTHONPATH="../../apps/api/src:../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --reload --port 8000

# Split screen (Ctrl+A, then S)
# Switch to new window (Ctrl+A, then Tab)
# Start frontend
cd apps/web
npm run dev

# Detach (Ctrl+A, then d)
# Servers keep running!

# Reattach later
screen -r servers

# List sessions
screen -ls

# Kill session
screen -X -S servers quit
```

### Method 5: macOS Launch Agents (Auto-start on Boot)

Create a Launch Agent to auto-start servers on system boot:

```bash
# Create Launch Agent directory
mkdir -p ~/Library/LaunchAgents

# Create plist file (see example below)
```

**Example Launch Agent** (`~/Library/LaunchAgents/com.uepi.servers.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.uepi.servers</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/nilesh/Downloads/uepi-migration-20260123-151729/START_SERVERS_BACKGROUND.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/nilesh/Downloads/uepi-migration-20260123-151729/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/nilesh/Downloads/uepi-migration-20260123-151729/logs/launchd-error.log</string>
</dict>
</plist>
```

**Load the agent:**
```bash
launchctl load ~/Library/LaunchAgents/com.uepi.servers.plist
```

**Unload the agent:**
```bash
launchctl unload ~/Library/LaunchAgents/com.uepi.servers.plist
```

## 🔍 Monitoring & Troubleshooting

### Check if servers are running:

```bash
# Using our script
./CHECK_SERVERS.sh

# Manual check
lsof -ti:8000  # API Server
lsof -ti:3050  # Frontend Server

# Check processes
ps aux | grep uvicorn
ps aux | grep "npm run dev"
```

### View logs:

```bash
# Background script logs
tail -f logs/api.log
tail -f logs/frontend.log

# PM2 logs
pm2 logs
pm2 logs uepi-api
pm2 logs uepi-frontend
```

### Kill processes manually:

```bash
# Kill by port
lsof -ti:8000 | xargs kill -9
lsof -ti:3050 | xargs kill -9

# Kill by PID
kill <PID>
```

## 🎯 Recommended Setup

**For Development:**
- Use **PM2** - Best balance of features and simplicity
- Auto-restart on crashes
- Easy monitoring
- Clean log management

**For Quick Testing:**
- Use **Background Scripts** - Simple and fast
- No extra dependencies
- Easy to understand

**For Long-term/Production:**
- Use **PM2** with `pm2 save` and `pm2 startup`
- Servers auto-start on system reboot
- Process monitoring and alerts
- Memory limits and auto-restart

## 📝 Quick Reference

| Method | Auto-restart | Monitoring | Logs | Auto-start on boot |
|--------|--------------|------------|------|---------------------|
| PM2 | ✅ | ✅ | ✅ | ✅ (with setup) |
| Background Scripts | ❌ | ❌ | ✅ | ❌ |
| tmux/screen | ❌ | ❌ | ❌ | ❌ |
| Launch Agents | ✅ | ❌ | ✅ | ✅ |

## 🚀 Getting Started

1. **Choose a method** (PM2 recommended)
2. **Run setup** (if needed)
3. **Start servers**
4. **Verify** they're running
5. **Step away** - servers keep running!

## 💡 Tips

- Always check logs if something isn't working
- Use `./CHECK_SERVERS.sh` to verify status
- PM2 provides the best long-term solution
- Keep logs directory clean (rotate logs periodically)
- Set up monitoring alerts if needed

