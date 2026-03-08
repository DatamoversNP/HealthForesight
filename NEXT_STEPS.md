# Next Steps - Start Frontend & Test Application

## ✅ API Server is Running!

Your API server is running on **http://localhost:8000**

## Step 1: Start Frontend Server

Open a **new terminal window** and run:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

This will start the frontend on **http://localhost:3050** (or the next available port).

## Step 2: Access the Application

Once both servers are running:

- **Frontend Application**: http://localhost:3050
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/v1/auth/me

## Step 3: Test the Application

### 1. **Login**
   - The app should auto-login as a demo user
   - You'll see the role switcher in the top navigation

### 2. **Switch Roles** (Test All Personas)
   - Click the role switcher dropdown
   - Try all 4 personas:
     - **Executive** → Executive Dashboard
     - **Policy Owner** → Policy Owner Dashboard
     - **Analyst** → Analyst Dashboard (with Cohort Builder)
     - **Ops/Clinical** → Ops/Clinical Dashboard

### 3. **View Dashboards**
   - Each persona should show their specific dashboard
   - Dashboards should load real data from your files
   - No hardcoded/mock data

### 4. **Navigate to Policies**
   - Click "Policies" in the sidebar
   - View all your configured policies
   - Click "Open Workspace" on any policy to see:
     - Policy Versions
     - Assumptions
     - Guardrails
     - Changelog

### 5. **Test Cohort Builder** (Analyst Role)
   - Switch to Analyst role
   - Go to Analyst Dashboard
   - Click "Cohort Builder" tab
   - Click "Build Cohort"
   - Define filters and save
   - View saved cohorts in "Cohorts" page

### 6. **Test Policy Builder**
   - Navigate to "Policy Builder"
   - Create or edit a policy
   - Save - this should create a version and changelog entry

## Step 4: Verify Data

All data should come from:
- `apps/api/data/policies/` - Policy data
- `apps/api/data/observations/` - Observation data
- `apps/api/data/policy_versions/` - Version history
- `apps/api/data/cohorts/` - Saved cohorts
- `apps/api/data/target_data_model/` - Ingested data

## Troubleshooting

### Frontend won't start?
```bash
cd apps/web
npm install  # Install dependencies if needed
npm run dev
```

### API not responding?
- Check API server is still running in Terminal 1
- Check logs for errors
- Verify port 8000 is not in use

### Dashboards show empty?
- Check browser console for errors
- Verify API is responding: `curl http://localhost:8000/docs`
- Check that data files exist in `apps/api/data/`

### Can't switch roles?
- Check browser console
- Verify `RoleContext` is working
- Try refreshing the page

## Quick Commands Reference

```bash
# Start API (Terminal 1)
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_API_SERVER.sh

# Start Frontend (Terminal 2)
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev

# Check API health
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer dev-token-123"

# View API docs
open http://localhost:8000/docs
```

## What to Test

✅ **Epic 1 (RBAC):**
- Role switching works
- Persona dashboards load correctly
- Permissions are enforced

✅ **Epic 2 (Policy Lifecycle):**
- Policy versions are created on save
- Assumptions can be added/edited
- Guardrails can be added/edited
- Changelog shows history

✅ **Cohort Builder:**
- Can create cohorts with filters
- Can view saved cohorts
- Can see cohort members

✅ **Data Loading:**
- All dashboards show real data
- No hardcoded values
- Data comes from files

## Success Indicators

You'll know everything is working when:
1. ✅ Both servers start without errors
2. ✅ Frontend loads at http://localhost:3050
3. ✅ You can switch between all 4 personas
4. ✅ Each dashboard shows relevant data
5. ✅ Policies page shows all your policies
6. ✅ Policy Workspace shows versions, assumptions, guardrails
7. ✅ Cohort Builder works
8. ✅ No console errors (except React DevTools suggestion)

## Next: Generate More Data (Optional)

If you want to test with more data:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./scripts/generate_all_synthetic_data.sh
```

This will generate:
- More policies
- More observations
- More policy lifecycle data

---

**You're all set! Start the frontend and begin testing! 🚀**
