# Final Start Instructions - All Fixes Applied

## All Import Errors Fixed

✅ Fixed `policy_versions.py` router imports
✅ Fixed `observation_enhancement.py` imports  
✅ Fixed `analyses_file.py` imports
✅ Fixed `integration_helpers.py` imports
✅ Made `ingestions` router import optional (boto3 permission issue)

## Start API Server

**Use this command:**

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api
export PYTHONPATH="$(cd ../.. && pwd)/apps/api/src:$(cd ../.. && pwd)/packages/common/src:${PYTHONPATH}"
python3 -m uvicorn uepi_api.main:app --reload --port 8000
```

**Or use the script:**

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_API_SERVER.sh
```

## Expected Output

You should see:
```
INFO:     Will watch for changes in these directories: ['/Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**No errors should appear!**

## Verify API is Running

```bash
# Test health endpoint
curl http://localhost:8000/docs

# Test auth endpoint
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer dev-token-123"
```

## Start Frontend (Terminal 2)

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

## Access Application

- **Application**: http://localhost:3050
- **API Docs**: http://localhost:8000/docs

## Complete Test Flow

Once both servers are running:

1. **Login** → Auto-login as demo user
2. **Switch Roles** → Test all 4 personas
3. **View Dashboards** → All should show real data
4. **Navigate to Policies** → See all policies
5. **Open Policy Workspace** → Test all Epic 2 features
6. **Test Cohort Builder** → Create and view cohorts
7. **Verify** → All data from files, no hardcoded values

## Troubleshooting

If you still see import errors:
1. Check PYTHONPATH is set correctly
2. Verify both `apps/api/src` and `packages/common/src` are in path
3. Check for any other missing dependencies

The server should now start successfully!


