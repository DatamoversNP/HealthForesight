# Learning Router Syntax Error Fixed

## Issue

**Error**: `SyntaxError: parameter without a default follows parameter with a default`

**Location**: `apps/api/src/uepi_api/routers/learning.py` line 118

## Root Cause

Same issue as in `observations.py` - Python requires parameters without defaults to come before parameters with defaults.

The function had:
```python
async def update_prediction_accuracy(
    policy_id: UUID = Query(...),                # Has default ✗
    observation_ids: List[str] = Query(...),     # Has default ✗
    current_user: Annotated[CurrentUser, ...],   # No default but after defaults ✗
):
```

## Fix Applied

Reordered parameters to put `current_user` before the Query parameters:

```python
async def update_prediction_accuracy(
    current_user: Annotated[CurrentUser, ...],   # No default, now first ✓
    policy_id: UUID = Query(...),                # Has default ✓
    observation_ids: List[str] = Query(...),     # Has default ✓
):
```

## Verification

✅ Syntax error fixed
✅ Function signature is now valid Python
✅ FastAPI dependency injection still works

## Status

This was the second instance of the same parameter ordering issue. Both `observations.py` and `learning.py` are now fixed.

The API server should now start successfully without syntax errors.
