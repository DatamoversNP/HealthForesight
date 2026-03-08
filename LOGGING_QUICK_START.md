# Logging Quick Start Guide

## ✅ Logging System is Ready

The comprehensive logging system has been implemented for both API and frontend. All actions, errors, and API calls are now being logged.

## 🚀 Enable Logging (One-Time Setup)

**Restart the API to enable logging:**

```bash
# Stop the current API (Ctrl+C if running)
# Then start it again:
./start_api_local.sh
```

## 📋 View Logs

### Using Helper Scripts (Recommended)

**View all API logs:**
```bash
./view_logs.sh api
```

**View errors only:**
```bash
./view_logs.sh error
```

**View user actions:**
```bash
./view_logs.sh action
```

**View HTTP requests:**
```bash
./view_logs.sh request
```

**Search for specific policy:**
```bash
./search_logs.sh ST_BIOLOGIC_006
```

### Manual Commands

**View logs:**
```bash
tail -f logs/api.log
```

**View errors:**
```bash
tail -f logs/errors.log
```

**Search:**
```bash
grep "error" logs/api.log
```

## 📁 Log Files Created

After restarting the API, these files will be created automatically:

- `logs/api.log` - All API logs (JSON format)
- `logs/errors.log` - Errors only (JSON format)
- `logs/actions.log` - User actions (JSON format)
- `logs/requests.log` - HTTP requests (JSON format)

## 🔍 What Gets Logged

### API Logging
- ✅ All HTTP requests (method, path, status, duration)
- ✅ Request/response bodies (for errors)
- ✅ User actions (policy views, workspace access, etc.)
- ✅ All errors with full stack traces
- ✅ Application startup/shutdown

### Frontend Logging
- ✅ All API calls (method, URL, status, duration)
- ✅ User actions (button clicks, navigation)
- ✅ Errors and warnings
- ✅ Stored in browser localStorage (`uepi_logs`)

## 💡 Tips

1. **Watch logs in real-time:**
   ```bash
   ./view_logs.sh api
   ```

2. **Search for specific errors:**
   ```bash
   ./search_logs.sh "HTTPException"
   ```

3. **View last 100 lines:**
   ```bash
   tail -n 100 logs/api.log
   ```

4. **View frontend logs:**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Or check localStorage: `localStorage.getItem('uepi_logs')`

## ⚠️ Troubleshooting

**"No such file or directory"**
- The API hasn't been restarted yet
- Restart: `./start_api_local.sh`
- Logs will be created automatically when the API starts

**"jq: command not found"**
- You don't need jq - the scripts work without it
- Or install: `brew install jq` (optional)

**No logs appearing**
- Make sure the API is running
- Use the application (make API calls)
- Logs are only created when there's activity

## 📖 More Information

See `HOW_TO_VIEW_LOGS.md` for detailed instructions.

