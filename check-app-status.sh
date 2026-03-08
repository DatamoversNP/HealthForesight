#!/bin/bash
# Diagnostic script to check application status

echo "=== Application Status Check ==="
echo ""

# Check if dev server is running
echo "1. Checking if dev server is running on port 3050..."
if lsof -ti:3050 > /dev/null 2>&1; then
    echo "   ✅ Dev server is running on port 3050"
    PID=$(lsof -ti:3050 | head -1)
    echo "   Process ID: $PID"
else
    echo "   ❌ Dev server is NOT running on port 3050"
fi
echo ""

# Check Node.js
echo "2. Checking Node.js..."
if command -v node > /dev/null 2>&1; then
    echo "   ✅ Node.js: $(node --version)"
else
    echo "   ❌ Node.js not found"
    echo "   Try: source ~/.nvm/nvm.sh"
fi
echo ""

# Check npm
echo "3. Checking npm..."
if command -v npm > /dev/null 2>&1; then
    echo "   ✅ npm: $(npm --version)"
else
    echo "   ❌ npm not found"
    echo "   Try: source ~/.nvm/nvm.sh"
fi
echo ""

# Check if node_modules exists
echo "4. Checking dependencies..."
if [ -d "apps/web/node_modules" ]; then
    echo "   ✅ node_modules directory exists"
else
    echo "   ❌ node_modules directory missing"
    echo "   Run: cd apps/web && npm install"
fi
echo ""

# Check for common errors
echo "5. Checking for common issues..."
cd apps/web

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "   ❌ package.json not found"
else
    echo "   ✅ package.json exists"
fi

# Check for TypeScript errors
if [ -f "tsconfig.json" ]; then
    echo "   ✅ TypeScript config exists"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Make sure dev server is running:"
echo "   source ~/.nvm/nvm.sh && cd apps/web && npm run dev"
echo ""
echo "2. Check browser console for errors (F12 or Cmd+Option+I)"
echo ""
echo "3. Try accessing: http://localhost:3050"
echo ""
echo "4. If you see build errors, check the terminal where npm run dev is running"


