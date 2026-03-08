#!/bin/bash
# Simple screenshot capture script using browser automation
# This script uses Playwright (more reliable than Puppeteer for screenshots)

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCREENSHOTS_DIR="$PROJECT_ROOT/public/screenshots/tours"
BASE_URL="http://localhost:3050"

echo "=========================================="
echo "Automated Screenshot Capture"
echo "=========================================="
echo ""

# Check if frontend is running
if ! curl -s "$BASE_URL" > /dev/null 2>&1; then
    echo "❌ Frontend server is not running at $BASE_URL"
    echo "   Please start it with: npm run dev"
    exit 1
fi

# Create screenshots directory
mkdir -p "$SCREENSHOTS_DIR"

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    echo "❌ npx not found. Please install Node.js"
    exit 1
fi

echo "📦 Installing Playwright (if needed)..."
cd "$PROJECT_ROOT"
npx playwright install chromium 2>/dev/null || echo "Playwright already installed"

echo ""
echo "🚀 Starting screenshot capture..."
echo "   Frontend URL: $BASE_URL"
echo "   Screenshots will be saved to: $SCREENSHOTS_DIR"
echo ""

# Run the capture script
node "$PROJECT_ROOT/scripts/capture-tour-screenshots-playwright.js"

echo ""
echo "✅ Screenshot capture complete!"
echo "   Review screenshots in: $SCREENSHOTS_DIR"

