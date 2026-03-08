#!/bin/bash
# HealthForesight Website - Quick Reload Script
# Easy setup for Cursor or any development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 HealthForesight Website - Quick Setup"
echo "========================================"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install
  echo ""
fi

# Check if public folder and logo exist
if [ ! -f "public/healthforesight-logo.svg" ]; then
  echo "⚠️  Warning: Logo file not found in public/"
  echo "   Make sure public/healthforesight-logo.svg exists"
  echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Run: npm run dev"
echo "   2. Open: http://localhost:3052"
echo ""
echo "🎯 Or run everything at once:"
echo "   npm run dev"
echo ""
