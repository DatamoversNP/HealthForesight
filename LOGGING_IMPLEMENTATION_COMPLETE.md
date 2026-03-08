# ✅ Comprehensive Logging System Implemented

## Summary

A complete logging system has been implemented to capture all actions, errors, and details throughout the application. This will help identify and debug issues quickly.

## What Was Added

### 1. API Logging Infrastructure

**Files Created:**
- `apps/api/src/uepi_api/logging_config.py` - Core logging configuration
- `apps/api/src/uepi_api/middleware_logging.py` - Request/response logging middleware

**Features:**
- ✅ JSON-formatted logs for structured data
- ✅ Human-readable console logs
- ✅ Automatic log rotation (10MB files, 5-10 backups)
- ✅ Separate log files:
  - `logs/api.log` - All API logs
  - `logs/errors.log` - Errors only
  - `logs/actions.log` - User actions
  - `logs/requests.log` - HTTP requests/responses

### 2. API Integration

**Files Modified:**
- `apps/api/src/uepi_api/main.py` - Added logging setup and error handlers

**Features:**
- ✅ Automatic request/response logging
- ✅ Comprehensive error logging with stack traces
- ✅ User action logging
- ✅ Request ID tracking for tracing

### 3. Frontend Logging

**Files Created:**
- `apps/web/src/lib/logger.ts` - Frontend logging utility

**Files Modified:**
- `apps/web/src/lib/api.ts` - Integrated logging into API client

**Features:**
- ✅ Console logging (categorized)
- ✅ LocalStorage persistence (1000 entries max)
- ✅ Automatic API call logging
- ✅ Error logging with stack traces
- ✅ User action logging

## Log Files Location

All logs are stored in: `logs/` directory

```
logs/
├── api.log          # All API logs (JSON)
├── errors.log       # Errors only (JSON)
├── actions.log      # User actions (JSON)
└── requests.log     # HTTP requests (JSON)
```

## What Gets Logged

### API Side

1. **All HTTP Requests:**
   - Method, path, status code
   - Request/response bodies (truncated)
   - Duration in milliseconds
   - User ID and tenant ID
   - Request ID for tracing

2. **All Errors:**
   - Full stack traces
   - Request context
   - User information
   - Error type and message

3. **User Actions:**
   - Policy operations (view, create, update, delete)
   - Analysis operations
   - Data loading operations
   - Authentication events

### Frontend Side

1. **All API Calls:**
   - Request method, URL, status
   - Duration
   - Request/response data
   - Errors

2. **User Actions:**
   - Button clicks
   - Navigation
   - Form submissions
   - Policy interactions

3. **Errors:**
   - JavaScript exceptions
   - API errors
   - Network errors

## Usage Examples

### API (Python)

```python
from uepi_api.logging_config import get_logger, log_action, log_error_with_context

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
    context={"operation": "load_policy"},
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

// Get logs
const errorLogs = logger.getLogs('error', 'POLICY', 100)

// Export logs
const exportData = logger.exportLogs()
```

## Viewing Logs

### API Logs

```bash
# View all logs
tail -f logs/api.log | jq

# View errors only
tail -f logs/errors.log | jq

# View requests
tail -f logs/requests.log | jq

# Search for specific policy
grep "ST_BIOLOGIC_006" logs/api.log | jq
```

### Frontend Logs

1. **Browser Console**: All logs appear in console
2. **LocalStorage**: `localStorage.getItem('uepi_logs')`
3. **Export**: `logger.exportLogs()` returns JSON string

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

## Next Steps

1. **Restart API** to enable logging:
   ```bash
   ./start_api_local.sh
   ```

2. **Use the application** - logs will be automatically captured

3. **Check logs** when issues occur:
   ```bash
   tail -f logs/errors.log | jq
   ```

4. **Search logs** to find specific issues:
   ```bash
   grep "policy_id" logs/api.log | jq
   ```

## Benefits

- ✅ **Complete visibility** into all operations
- ✅ **Easy debugging** with full context
- ✅ **Error tracking** with stack traces
- ✅ **Performance monitoring** with request durations
- ✅ **User action tracking** for analytics
- ✅ **Structured data** for easy searching

## Notes

- Logs are automatically rotated at 10MB
- Health check endpoints are not logged (to reduce noise)
- Large request/response bodies are truncated to 1000 characters
- Frontend logs are stored in localStorage (persist across sessions)

