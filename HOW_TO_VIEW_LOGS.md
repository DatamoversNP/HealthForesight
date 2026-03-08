# How to View Logs

## Quick Start

### 1. Make sure API is running

The API must be running to generate logs:

```bash
./start_api_local.sh
```

### 2. View logs (simple method)

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

### 3. Search logs

**Search for specific policy:**
```bash
./search_logs.sh ST_BIOLOGIC_006
```

**Search for errors:**
```bash
./search_logs.sh error
```

## Manual Methods (without scripts)

### View logs without jq

**View all logs:**
```bash
tail -f logs/api.log
```

**View errors:**
```bash
tail -f logs/errors.log
```

**Search for specific term:**
```bash
grep "ST_BIOLOGIC_006" logs/api.log
```

### View logs with jq (if installed)

**Install jq (optional):**
```bash
brew install jq
```

**Then use:**
```bash
tail -f logs/api.log | jq .
```

## Log Files

- `logs/api.log` - All API logs
- `logs/errors.log` - Errors only
- `logs/actions.log` - User actions
- `logs/requests.log` - HTTP requests

## Troubleshooting

### "No such file or directory"
- The API hasn't been started yet
- Start the API: `./start_api_local.sh`
- Logs will be created automatically

### "jq: command not found"
- You don't need jq - the scripts work without it
- Or install jq: `brew install jq`

### No logs appearing
- Make sure the API is running
- Check that you're using the application (making API calls)
- Logs are only created when there's activity

## Tips

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

4. **Clear logs (if needed):**
   ```bash
   rm logs/*.log
   ```

