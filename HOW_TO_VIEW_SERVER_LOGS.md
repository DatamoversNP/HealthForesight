# How to View Server Logs

## Log File Locations

Server logs are saved in the project root directory:

- **API Server Log**: `api-server.log`
- **Web Server Log**: `web-server.log`

## View Logs Commands

### View Last 50 Lines of API Server Log
```bash
tail -50 api-server.log
```

### View Last 50 Lines of Web Server Log
```bash
tail -50 web-server.log
```

### Follow Logs in Real-Time (Live Monitoring)

**API Server (recommended for debugging):**
```bash
tail -f api-server.log
```

**Web Server:**
```bash
tail -f web-server.log
```

**Both Servers (in separate terminals):**
- Terminal 1: `tail -f api-server.log`
- Terminal 2: `tail -f web-server.log`

### Search Logs for Specific Errors

**Search for validation errors:**
```bash
grep -i "validation\|pydantic\|error" api-server.log | tail -20
```

**Search for recent errors:**
```bash
grep -i "error\|exception\|failed" api-server.log | tail -30
```

**Search for specific error type:**
```bash
grep -i "extra_forbidden" api-server.log | tail -10
```

### View All Recent Errors

```bash
tail -100 api-server.log | grep -i "error\|exception\|failed\|traceback" -A 5
```

## Notes

- If you started the server with `./start-api-server.sh` directly (not background), logs appear in the terminal output
- If you started with `./start-both-servers.sh`, logs are written to the log files
- The API server runs on port 8000
- The Web server runs on port 3050
- Press `Ctrl+C` to stop following logs (`tail -f`)

## Quick Debug Commands

**Check if servers are running:**
```bash
lsof -ti:8000 && echo "✅ API server running" || echo "❌ API server not running"
lsof -ti:3050 && echo "✅ Web server running" || echo "❌ Web server not running"
```

**View last 20 lines with timestamps:**
```bash
tail -20 api-server.log
```
