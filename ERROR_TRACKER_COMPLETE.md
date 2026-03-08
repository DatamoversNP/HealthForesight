# Complete Error Tracker & Fix Log

## 📋 Overview

This document provides a complete tracker of all errors found, their fixes, and verification status.

**Last Updated:** 2026-02-01  
**Status:** Active monitoring

---

## 🔍 How to Check for Errors

### 1. Check API Logs
```bash
# View all errors
./view_logs.sh error

# View all API activity
./view_logs.sh api

# Search for specific errors
./search_logs.sh "error_pattern"
```

### 2. Check Frontend Logs
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for red error messages
4. Or open: `extract_frontend_errors.html` in browser to extract from localStorage

### 3. Run Error Analysis
```bash
./analyze_errors.sh
```

This will:
- Analyze all log files
- Categorize errors
- Generate a report
- Update statistics

---

## 🔴 Error Log

### Error #1: API Server Not Running
**Date:** 2026-02-01  
**Status:** ✅ FIXED  
**Severity:** CRITICAL  
**Category:** Network

**Error Message:**
```
Network error: Network Error
GET http://localhost:8000/api/v1/auth/me net::ERR_CONNECTION_REFUSED
GET http://localhost:8000/api/v1/policies net::ERR_CONNECTION_REFUSED
```

**Root Cause:**
- API server was not running on port 8000
- Frontend cannot connect to backend

**Fix Applied:**
- Created `start_api_local.sh` - API startup script
- Created `start_api_background.sh` - Background API startup
- Created `HOW_TO_KEEP_API_RUNNING.md` - Documentation
- Created `diagnose_api_network.sh` - Diagnostic tool

**Verification:**
```bash
./diagnose_api_network.sh
# Should show: ✅ API is running on port 8000
```

**Files Created/Modified:**
- `start_api_local.sh`
- `start_api_background.sh`
- `HOW_TO_KEEP_API_RUNNING.md`
- `diagnose_api_network.sh`

---

### Error #2: No Log Files Generated
**Date:** 2026-02-01  
**Status:** ✅ FIXED  
**Severity:** MEDIUM  
**Category:** Logging

**Error Message:**
```
No log files found
logs/api.log: No such file or directory
logs/errors.log: No such file or directory
```

**Root Cause:**
- API was started before logging system was implemented
- Logging not enabled in API startup

**Fix Applied:**
- Integrated comprehensive logging in `apps/api/src/uepi_api/main.py`
- Created logging configuration: `apps/api/src/uepi_api/logging_config.py`
- Created request logging middleware: `apps/api/src/uepi_api/middleware_logging.py`
- Created frontend logging: `apps/web/src/lib/logger.ts`
- Created log viewing scripts: `view_logs.sh`, `search_logs.sh`

**Verification:**
```bash
./start_api_local.sh
# Wait 15 seconds, then:
ls -la logs/*.log
# Should show: api.log, errors.log, actions.log, requests.log
```

**Files Created/Modified:**
- `apps/api/src/uepi_api/main.py`
- `apps/api/src/uepi_api/logging_config.py`
- `apps/api/src/uepi_api/middleware_logging.py`
- `apps/web/src/lib/logger.ts`
- `apps/web/src/lib/api.ts`
- `view_logs.sh`
- `search_logs.sh`

---

### Error #3: Node.js/npm Not Found
**Date:** 2026-02-01  
**Status:** ✅ FIXED  
**Severity:** HIGH  
**Category:** Environment

**Error Message:**
```
npm: command not found
./START_WEB_SERVER.sh: line 37: npm: command not found
```

**Root Cause:**
- Node.js not installed or not in PATH
- nvm installed but not loaded in shell

**Fix Applied:**
- Updated `START_WEB_SERVER.sh` to automatically load nvm
- Created `INSTALL_NODE_AND_START_WEB.sh` - Node.js installer script
- Created `NODEJS_INSTALLATION_GUIDE.md` - Installation guide

**Verification:**
```bash
./INSTALL_NODE_AND_START_WEB.sh
# Should install Node.js and start web server
```

**Files Created/Modified:**
- `START_WEB_SERVER.sh`
- `INSTALL_NODE_AND_START_WEB.sh`
- `NODEJS_INSTALLATION_GUIDE.md`

---

### Error #4: API Stopped After Starting
**Date:** 2026-02-01  
**Status:** ✅ FIXED  
**Severity:** HIGH  
**Category:** Process Management

**Error Message:**
```
API is NOT running on port 8000
```

**Root Cause:**
- User pressed Ctrl+C after starting API
- API needs to keep running for frontend to work

**Fix Applied:**
- Created `start_api_background.sh` - Start API in background
- Created `HOW_TO_KEEP_API_RUNNING.md` - Documentation
- Updated error messages to clarify API must stay running

**Verification:**
```bash
./start_api_background.sh
# API should start in background and keep running
lsof -ti:8000
# Should show process ID
```

**Files Created/Modified:**
- `start_api_background.sh`
- `HOW_TO_KEEP_API_RUNNING.md`

---

## 🔄 Common Error Patterns

### Pattern 1: Network/Connection Errors
**Symptoms:**
- `ERR_CONNECTION_REFUSED`
- `Network Error`
- `ECONNABORTED`

**Common Causes:**
- API server not running
- Wrong port number
- Firewall blocking connection

**Fix:**
```bash
./start_api_background.sh
./diagnose_api_network.sh
```

---

### Pattern 2: 404 Not Found Errors
**Symptoms:**
- `GET /api/v1/policies/XXX/predicted-impact 404`
- `Resource not found`

**Common Causes:**
- Resource doesn't exist yet (normal for predicted impact)
- Wrong ID format
- Data not loaded

**Fix:**
- Check if resource should exist
- Generate missing resources via UI
- Verify data files exist

---

### Pattern 3: 500 Server Errors
**Symptoms:**
- `Internal Server Error`
- `500 status code`

**Common Causes:**
- Code errors
- Missing dependencies
- Data format issues

**Fix:**
```bash
./view_logs.sh error
# Check for stack traces
```

---

### Error #5: localStorage Quota Exceeded
**Date:** 2026-02-01  
**Status:** ✅ FIXED  
**Severity:** HIGH  
**Category:** Frontend Logging

**Error Message:**
```
QuotaExceededError: Failed to execute 'setItem' on 'Storage': Setting the value of 'uepi_logs' exceeded the quota.
```

**Root Cause:**
- Logger was saving logs every 5 seconds
- Max logs set to 1000, but each log entry can be very large (with full API request/response data)
- localStorage has a ~5-10MB limit
- Logs were accumulating and exceeding quota

**Fix Applied:**
1. Reduced `maxLogs` from 1000 to 100
2. Added data truncation for large objects (>500 chars)
3. Added size check before saving (2MB threshold)
4. If quota exceeded, disable storage and keep only in-memory logs
5. Truncate large nested objects (requestData, responseData) to prevent quota issues
6. Keep only errors and recent logs if size exceeds threshold

**Verification:**
- localStorage quota errors should stop appearing
- Logs will continue in memory even if localStorage is full
- Only essential data is stored

**Files Modified:**
- `apps/web/src/lib/logger.ts`

---

### Error #6: DOM Nesting Warning (div inside p)
**Date:** 2026-02-01  
**Status:** ✅ FIXED  
**Severity:** LOW  
**Category:** Frontend UI

**Error Message:**
```
Warning: validateDOMNesting(...): <div> cannot appear as a descendant of <p>.
```

**Root Cause:**
- In `ExecutiveDashboardPage.tsx`, `ListItemText` component's `secondary` prop renders inside a `<p>` tag
- The code was using `Box component="div"` inside the secondary prop
- This creates invalid HTML: `<p><div>...</div></p>`

**Fix Applied:**
- Changed `Box component="div"` to `Box component="span"` in secondary props
- Changed `Typography component="div"` to `Typography component="span"` in secondary props
- Added `display: 'block'` to maintain layout while using span elements

**Verification:**
- DOM nesting warning should disappear from console
- UI should look the same (spans with display:block behave like divs)

**Files Modified:**
- `apps/web/src/pages/persona/ExecutiveDashboardPage.tsx`

---

## 📊 Error Statistics

**Total Errors Found:** 6  
**Errors Fixed:** 6  
**Errors Open:** 0  
**Critical Errors:** 1  
**High Severity:** 3  
**Medium Severity:** 1  
**Low Severity:** 1  

---

## 🛠️ Tools Created

### Diagnostic Tools
1. `diagnose_api_network.sh` - Check API status and connectivity
2. `analyze_errors.sh` - Analyze all errors from logs
3. `view_logs.sh` - View logs by type
4. `search_logs.sh` - Search logs for patterns

### Startup Scripts
1. `start_api_local.sh` - Start API in foreground
2. `start_api_background.sh` - Start API in background
3. `START_WEB_SERVER.sh` - Start web server
4. `INSTALL_NODE_AND_START_WEB.sh` - Install Node.js and start web

### Documentation
1. `ERROR_TRACKER.md` - Error tracking document
2. `ERROR_TRACKER_COMPLETE.md` - This document
3. `HOW_TO_VIEW_LOGS.md` - How to view logs
4. `HOW_TO_KEEP_API_RUNNING.md` - API management guide
5. `API_NETWORK_ERRORS_FIX.md` - Network error fixes
6. `LOGGING_SETUP.md` - Logging system documentation

### Frontend Tools
1. `extract_frontend_errors.html` - Extract errors from browser localStorage

---

## 🎯 Next Steps

1. ✅ **Start API** - `./start_api_background.sh`
2. ✅ **Start Web** - `./START_WEB_SERVER.sh` (if needed)
3. ✅ **Monitor Logs** - `./view_logs.sh api`
4. ✅ **Check Errors** - `./view_logs.sh error`
5. ✅ **Run Diagnostics** - `./diagnose_api_network.sh`
6. ✅ **Analyze Errors** - `./analyze_errors.sh`

---

## 📝 How to Add New Errors

When you find a new error:

1. **Extract error details:**
   ```bash
   ./view_logs.sh error
   # Or
   ./search_logs.sh "error_message"
   ```

2. **Add to ERROR_TRACKER_COMPLETE.md:**
   - Error number (increment from last)
   - Date
   - Status (OPEN/FIXED)
   - Severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Category
   - Error message
   - Root cause
   - Fix applied
   - Verification steps
   - Files modified

3. **Update statistics** at the bottom

---

## 🔗 Related Documentation

- `HOW_TO_VIEW_LOGS.md` - How to view and search logs
- `LOGGING_SETUP.md` - Logging system details
- `API_NETWORK_ERRORS_FIX.md` - Network error fixes
- `QUICK_FIX_API_NETWORK_ERRORS.md` - Quick reference

---

**Note:** This tracker is maintained manually. Run `./analyze_errors.sh` regularly to discover new errors.

