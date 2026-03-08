# Test and Verification Guide

## Steps to Test the Application

### 1. Start API Server
```bash
cd apps/api
python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test Endpoints (in another terminal)

```bash
# Health check
curl http://localhost:8000/health

# Auth endpoint (should respond immediately)
curl -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/auth/me

# Access roles (should respond immediately)
curl -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/access/users/00000000-0000-0000-0000-000000000001/roles

# Policies (should return policies without validation errors)
curl -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/policies

# Dashboard summary
curl -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/dashboard/summary

# Policy performance
curl -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/dashboard/policy-performance?limit=5
```

### 3. Verify Frontend

1. Open browser to `http://localhost:3050` (or your frontend URL)
2. Check browser console for errors
3. Verify:
   - Dashboard loads data
   - Policies page shows policies
   - Observations page loads
   - No timeout errors in console

## Expected Results

✅ All endpoints respond within 30 seconds
✅ No Pydantic validation errors in API logs
✅ Policies load with all policy_type values (including "DURATION / FREQUENCY LIMIT")
✅ Frontend displays data correctly
✅ No timeout errors

## Fixes Applied

1. Fixed indentation in `policies.py`
2. Fixed PolicyResponse validation (policy_type as string)
3. Made auth/access endpoints non-blocking
4. Removed database dependency from auth endpoints
