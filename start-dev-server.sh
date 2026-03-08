#!/bin/bash
# Start the frontend dev server
# This script sources nvm and starts the Vite dev server

# Source nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Use default node version
nvm use default

# Navigate to web directory
cd "$(dirname "$0")/apps/web"

# Start dev server
echo "Starting Vite dev server..."
npm run dev


