#!/bin/bash
# Start script for marketing website
# This ensures index-marketing.html is used as the entry point

cd "$(dirname "$0")"

# For development, we'll temporarily copy index-marketing.html to index.html
# This allows Vite to find it, then we'll restore the original after
if [ -f "index.html" ] && [ ! -f "index.html.backup" ]; then
  cp index.html index.html.backup
fi

# Copy marketing HTML to index.html for Vite to use
cp index-marketing.html index.html

# Start the dev server
npm run dev:marketing -- --config vite.marketing.config.ts

# Restore original index.html when script exits
trap 'if [ -f "index.html.backup" ]; then mv index.html.backup index.html; fi' EXIT
