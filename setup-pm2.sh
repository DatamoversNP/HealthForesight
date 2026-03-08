#!/bin/bash
# Setup PM2 (Process Manager) for keeping servers running
# PM2 is better than nohup - it provides process monitoring, auto-restart, and logging

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Setting up PM2 Process Manager"
echo "=========================================="
echo ""

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "📦 Installing PM2..."
    npm install -g pm2
    echo "✅ PM2 installed"
else
    echo "✅ PM2 already installed"
fi

echo ""

# Create PM2 ecosystem file with proper paths
cat > "$PROJECT_ROOT/ecosystem.config.js" << EOF
const path = require('path');
const projectRoot = path.resolve(__dirname);

module.exports = {
  apps: [
    {
      name: 'uepi-api',
      script: 'python3',
      args: '-m uvicorn uepi_api.main:app --reload --port 8000',
      cwd: path.join(projectRoot, 'apps/api'),
      interpreter: 'none',
      env: {
        PYTHONPATH: path.join(projectRoot, 'apps/api/src') + ':' + path.join(projectRoot, 'packages/common/src'),
      },
      error_file: path.join(projectRoot, 'logs/pm2-api-error.log'),
      out_file: path.join(projectRoot, 'logs/pm2-api-out.log'),
      log_file: path.join(projectRoot, 'logs/pm2-api-combined.log'),
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
    },
    {
      name: 'uepi-frontend',
      script: 'npm',
      args: 'run dev',
      cwd: path.join(projectRoot, 'apps/web'),
      env: {
        NODE_ENV: 'development',
      },
      error_file: path.join(projectRoot, 'logs/pm2-frontend-error.log'),
      out_file: path.join(projectRoot, 'logs/pm2-frontend-out.log'),
      log_file: path.join(projectRoot, 'logs/pm2-frontend-combined.log'),
      time: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
    },
  ],
}
EOF

echo "✅ Created ecosystem.config.js"
echo ""

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

echo "=========================================="
echo "PM2 Setup Complete!"
echo "=========================================="
echo ""
echo "To start servers with PM2:"
echo "  pm2 start ecosystem.config.js"
echo ""
echo "To stop servers:"
echo "  pm2 stop ecosystem.config.js"
echo ""
echo "To restart servers:"
echo "  pm2 restart ecosystem.config.js"
echo ""
echo "To view logs:"
echo "  pm2 logs"
echo ""
echo "To monitor:"
echo "  pm2 monit"
echo ""
echo "To save PM2 configuration (auto-start on reboot):"
echo "  pm2 save"
echo "  pm2 startup"
echo ""
echo "To check status:"
echo "  pm2 status"
echo ""

