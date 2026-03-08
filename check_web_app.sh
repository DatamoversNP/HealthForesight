#!/bin/bash
# Diagnostic script for web app issues
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="${SCRIPT_DIR}/apps/web"

echo "🔍 Web App Diagnostics"
echo "======================"
echo ""

# Check if web directory exists
if [ ! -d "$WEB_DIR" ]; then
    echo "❌ Web directory not found: $WEB_DIR"
    exit 1
fi

cd "$WEB_DIR" || exit 1

# Check Node.js
echo "📋 Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✅ Node.js: $NODE_VERSION"
else
    echo "   ❌ Node.js not found. Please install Node.js"
    exit 1
fi

# Check npm
echo "📋 Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "   ✅ npm: $NPM_VERSION"
else
    echo "   ❌ npm not found. Please install npm"
    exit 1
fi

# Check node_modules
echo "📋 Checking dependencies..."
if [ -d "node_modules" ]; then
    echo "   ✅ node_modules exists"
else
    echo "   ⚠️  node_modules not found - need to run 'npm install'"
fi

# Check port 3050
echo "📋 Checking port 3050..."
if lsof -Pi :3050 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -ti :3050)
    echo "   ⚠️  Port 3050 is in use by PID: $PID"
    echo "   Run: kill -9 $PID to free the port"
else
    echo "   ✅ Port 3050 is available"
fi

# Check package.json
echo "📋 Checking package.json..."
if [ -f "package.json" ]; then
    echo "   ✅ package.json exists"
else
    echo "   ❌ package.json not found"
    exit 1
fi

# Check vite.config.ts
echo "📋 Checking vite.config.ts..."
if [ -f "vite.config.ts" ]; then
    echo "   ✅ vite.config.ts exists"
else
    echo "   ❌ vite.config.ts not found"
    exit 1
fi

echo ""
echo "✅ Diagnostics complete!"
echo ""
echo "To start the web app, run:"
echo "  ./start_web_app.sh"
echo ""
echo "Or manually:"
echo "  cd apps/web"
echo "  npm install  # if node_modules doesn't exist"
echo "  npm run dev"

