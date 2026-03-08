# Fix: Decision Router Conflict - 422 Error

## Issue
Getting `422 Unprocessable Content` error with message: `"Field required: action"`

## Root Cause
**Two decision routers were registered:**
1. **Old router** (`decisions.router`) - Requires `action` field, registered at line 137
2. **New router** (`decisions_workspace.router`) - Epic 3, doesn't require `action`, registered at line 218

FastAPI matches routes in order, so the **old router was intercepting the request first** and expecting an `action` field that we're not sending.

## Solution
**Commented out the old decisions router** so only the new Epic 3 router is used.

## Changes Made
- Commented out: `app.include_router(decisions.router, prefix="/api/v1", tags=["Decisions"])`
- Added note explaining why
- The new `decisions_workspace.router` (Epic 3) is now the only one handling `/api/v1/decisions` requests

## Testing
1. **Restart API server** (required for router changes)
   ```bash
   # Stop current server (CTRL+C)
   ./START_API_SERVER.sh
   ```

2. **Refresh browser**

3. **Try creating a decision again**
   - Should work now!
   - No more 422 error
   - No `action` field required

## Router Comparison

### Old Router (`decisions.py`)
- Requires: `action` field (APPROVE, DENY, DEFER, REVIEW)
- Model: `DecisionCreate` with `action: str`
- Status: Not fully implemented (returns 503)

### New Router (`decisions_workspace.py`) - Epic 3 ✅
- Does NOT require: `action` field
- Model: `DecisionCreate` with `title`, `recommendation`, `rationale`
- Status: Fully implemented with file storage

---

**Fix applied! Restart API server and try again.** 🚀


