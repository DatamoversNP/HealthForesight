# Local Development Guide

This guide helps you run the HealthForesight application **locally** without any Azure dependencies.

## Quick Start

### Option 1: Start Everything (Recommended)
```bash
./START_LOCAL_DEVELOPMENT.sh
```

This script will:
- ✅ Use local file storage (no database needed)
- ✅ Disable Azure features
- ✅ Start both API and Web servers
- ✅ Open the application in your browser

### Option 2: Start Servers Separately

**Start API Server:**
```bash
./START_API_NOW.sh
```

**Start Web Server (in another terminal):**
```bash
cd apps/web
npm run dev
```

## Configuration

The application is configured for local development by default:

- **Storage**: Local file storage in `./data` directory
- **Azure**: Disabled (`use_azure_file_storage: false`)
- **Environment**: Development mode
- **Database**: Not required (uses file storage)

## Access Points

Once started:
- **Frontend**: http://localhost:3050
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

### API Server Won't Start

1. **Check if port 8000 is in use:**
   ```bash
   lsof -ti:8000
   ```
   If something is running, stop it:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Check API logs:**
   ```bash
   tail -f api-server.log
   ```

3. **Verify Python environment:**
   ```bash
   source .venv/bin/activate
   python -c "import uepi_api; print('OK')"
   ```

### Web Server Won't Start

1. **Check if port 3050 is in use:**
   ```bash
   lsof -ti:3050
   ```

2. **Install dependencies:**
   ```bash
   cd apps/web
   npm install
   ```

3. **Check web logs:**
   ```bash
   tail -f web-server.log
   ```

### Storage Issues

The application uses local file storage in the `./data` directory. Make sure:
- The directory exists: `mkdir -p ./data`
- You have write permissions
- On macOS, it will use `./data` (not `/home/data`)

## Stopping the Application

**Stop all servers:**
```bash
pkill -f 'uvicorn uepi_api.main:app'
pkill -f 'vite'
```

Or stop individually:
- API: Press `CTRL+C` in the terminal running the API
- Web: Press `CTRL+C` in the terminal running the web server

## What's Different from Azure?

| Feature | Local Development | Azure Production |
|---------|------------------|------------------|
| Storage | Local files (`./data`) | Azure File Storage |
| Database | Not required | PostgreSQL (optional) |
| Redis | Not required | Azure Redis (optional) |
| Object Storage | Not required | Azure Blob Storage (optional) |
| Authentication | Mock/Demo mode | OIDC (Azure AD, etc.) |

## Development Tips

1. **Hot Reload**: Both servers support hot reload - changes are automatically reflected
2. **API Changes**: Edit files in `apps/api/src` - server will reload
3. **Frontend Changes**: Edit files in `apps/web/src` - Vite will reload
4. **Data Persistence**: All data is stored in `./data` directory locally

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Check out the frontend at http://localhost:3050
- Review the code structure in `apps/api/src` and `apps/web/src`
