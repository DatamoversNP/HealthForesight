# Node.js Installation Guide

## Problem
Homebrew installation failed with a formula error. However, you have **nvm** (Node Version Manager) installed, which is actually a better way to manage Node.js!

## Solution: Use nvm (Already Installed!)

You have nvm installed at `~/.nvm`. We just need to use it.

### Quick Start (Easiest Method)

**Run this script:**
```bash
./INSTALL_NODE_AND_START_WEB.sh
```

This script will:
1. ✅ Load nvm
2. ✅ Install Node.js LTS (if not already installed)
3. ✅ Install npm dependencies
4. ✅ Start the web server

### Manual Method

**Step 1: Load nvm and install Node.js**
```bash
# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js LTS
nvm install --lts
nvm use --lts
nvm alias default lts/*

# Verify
node --version
npm --version
```

**Step 2: Start the web server**
```bash
cd apps/web
npm install  # Only needed first time
npm run dev
```

### Alternative: Direct Download (If nvm doesn't work)

1. **Visit**: https://nodejs.org/
2. **Download**: LTS version for macOS
3. **Install**: Run the installer
4. **Restart terminal**
5. **Verify**: `node --version` and `npm --version`

### Make nvm Load Automatically

Add this to your `~/.zshrc`:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

Then reload:
```bash
source ~/.zshrc
```

## Recommended: Use the Script

The easiest way is to just run:
```bash
./INSTALL_NODE_AND_START_WEB.sh
```

This handles everything automatically!

## After Installation

Once Node.js is installed:
- ✅ Web server will start automatically
- ✅ Application will be available at http://localhost:3050
- ✅ API server should already be running on port 8000

## Troubleshooting

**"nvm: command not found"**
- Load nvm manually: `source ~/.nvm/nvm.sh`
- Or add to `~/.zshrc` (see above)

**"npm: command not found"**
- Make sure nvm is loaded: `source ~/.nvm/nvm.sh`
- Then: `nvm use --lts`

**Port 3050 already in use**
- Kill existing process: `lsof -ti:3050 | xargs kill -9`
- Or use a different port in `apps/web/vite.config.ts`

