# Syntax Error Fixed in observations.py

## Issue

**Error**: `SyntaxError: parameter without a default follows parameter with a default`

**Location**: `apps/api/src/uepi_api/routers/observations.py` line 88

## Root Cause

In Python, you cannot have a function parameter without a default value after a parameter with a default value.

The function had:
```python
async def create_observation_from_analysis_route(
    analysis_id: UUID,                           # No default ✓
    policy_id: UUID = Query(...),                # Has default ✗
    data_period_id: Optional[str] = Query(None), # Has default ✗
    current_user: Annotated[CurrentUser, ...],   # No default but after defaults ✗
):
```

Even though `current_user` uses FastAPI's `Depends()`, Python's syntax checker still requires parameters without defaults to come before parameters with defaults.

## Fix Applied

Reordered parameters to put `current_user` before the Query parameters:

```python
async def create_observation_from_analysis_route(
    analysis_id: UUID,                           # No default ✓
    current_user: Annotated[CurrentUser, ...],   # No default, now before defaults ✓
    policy_id: UUID = Query(...),                # Has default ✓
    data_period_id: Optional[str] = Query(None), # Has default ✓
):
```

## Verification

✅ Syntax error fixed
✅ Function signature is now valid Python
✅ FastAPI dependency injection still works (Depends can be anywhere)

## Status

The API server should now start successfully without syntax errors.
