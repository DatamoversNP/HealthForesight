# Comprehensive Logging System

## Overview

A comprehensive logging system has been implemented to capture all actions, errors, and details throughout the application. This will help identify and debug issues quickly.

## Log Files Location

All log files are stored in the `logs/` directory at the project root:

```
logs/
├── api.log          # All API logs (JSON format)
├── errors.log       # Error logs only (JSON format)
├── actions.log      # User actions (JSON format)
└── requests.log     # HTTP requests/responses (JSON format)
```

## API Logging

### Request/Response Logging
- All HTTP requests are logged with:
  - Method, path, status code
  - Request/response bodies (truncated for large payloads)
  - Duration in milliseconds
  - User ID and tenant ID
  - Request ID for tracing

### Error Logging
- All exceptions are logged with:
  - Full stack traces
  - Request context (path, method, user)
  - Error type and message
  - Additional context data

### Action Logging
- Key user actions are logged:
  - Policy operations (create, update, delete)
  - Analysis operations
  - Data loading operations
  - User authentication

## Frontend Logging

### Console Logging
- All logs are output to browser console
- Categorized by type (API, ACTION, ERROR, etc.)

### Local Storage
- Logs are stored in browser localStorage
- Automatically saved every 5 seconds
- Maximum 1000 log entries
- Accessible via `logger.getLogs()`

### Log Categories
- **API**: All API calls (requests/responses)
- **ACTION**: User actions (button clicks, navigation)
- **ERROR**: Errors and exceptions
- **DEBUG**: Debug information

## Usage

### API (Python)

```python
from uepi_api.logging_config import get_logger, log_action, log_error_with_context

# Get logger
logger = get_logger(__name__)

# Log info
logger.info("Policy loaded", extra={"extra_data": {"policy_id": "ST_BIOLOGIC_006"}})

# Log action
log_action(
    logger=logger,
    action="policy_viewed",
    details={"policy_id": "ST_BIOLOGIC_006"},
    user_id="user-123",
    tenant_id="tenant-456"
)

# Log error
log_error_with_context(
    logger=logger,
    error=exception,
    context={"operation": "load_policy", "policy_id": "ST_BIOLOGIC_006"},
    user_id="user-123",
    tenant_id="tenant-456"
)
```

### Frontend (TypeScript)

```typescript
import logger from './lib/logger'

// Log info
logger.info('POLICY', 'Policy loaded', { policyId: 'ST_BIOLOGIC_006' })

// Log action
logger.logAction('policy_viewed', { policyId: 'ST_BIOLOGIC_006' })

// Log error
logger.error('POLICY', 'Failed to load policy', error, { policyId: 'ST_BIOLOGIC_006' })

// Log API call (automatically done by ApiClient)
// No manual logging needed - ApiClient handles it

// Get logs
const logs = logger.getLogs('error', 'POLICY', 100)

// Export logs
const exportData = logger.exportLogs()
```

## Viewing Logs

### API Logs

```bash
# View all API logs
tail -f logs/api.log | jq

# View errors only
tail -f logs/errors.log | jq

# View requests
tail -f logs/requests.log | jq

# Search for specific policy
grep "ST_BIOLOGIC_006" logs/api.log | jq
```

### Frontend Logs

1. **Browser Console**: All logs appear in browser console
2. **LocalStorage**: Logs are stored in `localStorage.getItem('uepi_logs')`
3. **Export**: Use `logger.exportLogs()` to get JSON string

## Log Format

### API Logs (JSON)

```json
{
  "timestamp": "2026-01-29T12:34:56.789Z",
  "level": "INFO",
  "logger": "uepi_api.routers.policies_file",
  "message": "Request: GET /api/v1/policies -> 200 (45.23ms)",
  "module": "policies_file",
  "function": "get_policies",
  "line": 123,
  "extra": {
    "request_id": "abc-123",
    "method": "GET",
    "path": "/api/v1/policies",
    "status_code": 200,
    "duration_ms": 45.23,
    "user_id": "user-123",
    "tenant_id": "tenant-456"
  }
}
```

### Frontend Logs (JSON)

```json
{
  "timestamp": "2026-01-29T12:34:56.789Z",
  "level": "info",
  "category": "API",
  "message": "GET /api/v1/policies -> 200 (45ms)",
  "data": {
    "method": "GET",
    "url": "/api/v1/policies",
    "status": 200,
    "duration": 45
  },
  "userAgent": "Mozilla/5.0...",
  "url": "http://localhost:3050/policies"
}
```

## Log Rotation

- Log files are rotated when they reach 10MB
- Maximum 5-10 backup files kept
- Oldest logs are automatically deleted

## Performance

- Logging is asynchronous and non-blocking
- Large request/response bodies are truncated to 1000 characters
- Health check endpoints are not logged to reduce noise

## Troubleshooting

### Logs not appearing
1. Check `logs/` directory exists and is writable
2. Check log level in settings (default: INFO)
3. Check browser console for frontend logs

### Too many logs
- Adjust log level in `config.py`: `log_level = "WARNING"`
- Filter logs by category/level when viewing

### Log files too large
- Logs auto-rotate at 10MB
- Old backups are automatically deleted
- Clear logs: `rm logs/*.log`

## Next Steps

1. **Monitor logs** during development to catch issues early
2. **Search logs** when errors occur to find root cause
3. **Export logs** when reporting bugs
4. **Review logs** periodically to identify patterns

