#!/bin/bash
# Start the frontend dev server (Vite)
# Open http://localhost:3050 in your browser after it starts.

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/apps/web"

# Ensure npm is in PATH (e.g. when using nvm or fnm)
if ! command -v npm >/dev/null 2>&1; then
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
  [ -s "$HOME/.fnm/fnm" ] && eval "$("$HOME/.fnm/fnm" env)"
  [ -f "$HOME/.zshrc" ] && . "$HOME/.zshrc"
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js from https://nodejs.org or run from a terminal where 'npm' works."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies (npm install)..."
  npm install
fi

echo "Starting frontend at http://localhost:3050 ..."
echo "  (API should be running at http://localhost:8000)"
echo ""
npm run dev
