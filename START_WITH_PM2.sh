#!/bin/bash
# Start servers using PM2

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Starting Servers with PM2"
echo "=========================================="
echo ""

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 not installed. Run ./setup-pm2.sh first"
    exit 1
fi

# Check if ecosystem file exists
if [ ! -f "$PROJECT_ROOT/ecosystem.config.js" ]; then
    echo "❌ ecosystem.config.js not found. Run ./setup-pm2.sh first"
    exit 1
fi

# Set PYTHONPATH for API server
export PYTHONPATH="$PROJECT_ROOT/apps/api/src:$PROJECT_ROOT/packages/common/src:$PYTHONPATH"

# Start with PM2
cd "$PROJECT_ROOT"
pm2 start ecosystem.config.js

echo ""
echo "=========================================="
echo "✅ Servers started with PM2"
echo "=========================================="
echo ""
echo "View status:    pm2 status"
echo "View logs:      pm2 logs"
echo "Monitor:        pm2 monit"
echo "Stop:           pm2 stop ecosystem.config.js"
echo "Restart:        pm2 restart ecosystem.config.js"
echo ""
echo "To save PM2 config (auto-start on reboot):"
echo "  pm2 save"
echo "  pm2 startup"
echo ""

