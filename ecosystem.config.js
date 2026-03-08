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
