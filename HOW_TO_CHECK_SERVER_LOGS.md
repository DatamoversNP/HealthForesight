# How to Check Server Logs

## Quick Commands

### Check API Server Logs (Last 50 lines)
```bash
tail -50 api-server.log
```

### Watch API Server Logs in Real-Time
```bash
tail -f api-server.log
```

### Search for Errors in API Server Logs
```bash
grep -i "error\|exception\|traceback" api-server.log | tail -50
```

### Check Last Error with Context
```bash
tail -200 api-server.log | grep -B 10 -A 10 "Error\|Exception\|Traceback" | tail -50
```

### Check Web Server Logs
```bash
tail -50 web-server.log
```

## Log File Locations

- **API Server Logs**: `api-server.log` (in project root)
- **Web Server Logs**: `web-server.log` (in project root)

## Common Issues to Look For

1. **TypeError**: Look for "'float' object cannot be interpreted as an integer"
2. **ImportError**: Look for "ModuleNotFoundError" or "ImportError"
3. **IndentationError**: Look for "unexpected indent" or "IndentationError"
4. **SyntaxError**: Look for "SyntaxError" or "invalid syntax"
5. **CORS Errors**: Look for "CORS" or "Access-Control-Allow-Origin"

## Viewing Logs in Terminal

To check logs in real-time while testing:
1. Open a new terminal window
2. Navigate to the project directory
3. Run: `tail -f api-server.log`
4. Try your operation in the browser
5. Watch the logs update in real-time
