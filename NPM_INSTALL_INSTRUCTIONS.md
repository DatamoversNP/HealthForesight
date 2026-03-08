# npm Not Found - Installation Instructions

## Problem
The web server can't start because `npm` is not found in your PATH.

## Solution: Install Node.js and npm

### Option 1: Download from Node.js Website (Recommended)

1. **Visit**: https://nodejs.org/
2. **Download**: The LTS (Long Term Support) version
3. **Install**: Run the installer
4. **Restart**: Close and reopen your terminal
5. **Verify**: Run `node --version` and `npm --version`

### Option 2: Install via Homebrew (macOS)

If you have Homebrew installed:

```bash
brew install node
```

Then restart your terminal.

### Option 3: Install via nvm (Node Version Manager)

If you prefer using nvm:

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal, then:
nvm install --lts
nvm use --lts
```

## After Installation

1. **Restart your terminal** (important!)
2. **Verify installation**:
   ```bash
   node --version
   npm --version
   ```
3. **Start the web server**:
   ```bash
   ./START_WEB_SERVER.sh
   ```

## Current Status

- ✅ **API Server**: Running on port 8000
- ❌ **Web Server**: Waiting for npm installation

Once npm is installed, the web server will start and you can access:
- **Web Application**: http://localhost:3050
- **API Server**: http://localhost:8000

