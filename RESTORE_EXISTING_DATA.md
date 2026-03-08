# Restore Existing Data to Portal

## Problem
Your existing policies, baselines, and other data are not showing up in the portal because the API is looking in a different location than where the data currently exists.

## Solution

I've updated the code to automatically find your existing data in multiple locations. The API will now check:

1. `/tmp/policies_{tenant_id}.json` (migrated location)
2. `data/policies_{tenant_id}.json` (project data directory)
3. `data/valid_policies.json` (legacy format - contains your existing policies)
4. Individual policy files in `data/` directory (`policy_*.json`)

## Quick Fix

**Option 1: Just Restart the API (Recommended)**
The code has been updated to automatically find your existing data. Simply restart the API:

```bash
# Stop the current API (CTRL+C if running)
./START_API_NOW.sh
```

Then refresh your browser - your policies should appear!

**Option 2: Run Migration Script (Optional)**
If you want to consolidate all policies into one location:

```bash
./MIGRATE_EXISTING_DATA.sh
```

Then restart the API:
```bash
./START_API_NOW.sh
```

## What Data Will Be Found

The API will automatically find:
- ✅ Policies from `data/valid_policies.json` (5 policies)
- ✅ Policies from individual `data/policy_*.json` files
- ✅ Baselines from `data/baselines/`
- ✅ Analyses from `data/analyses/`
- ✅ Observations from `data/observations/`
- ✅ Scorecards from `data/scorecards/`
- ✅ All other data in the `data/` directory

## Verification

After restarting the API, check:
1. Open http://localhost:3050/policies - you should see your policies
2. Open http://localhost:3050/analyses - you should see your analyses
3. Open http://localhost:8000/docs - test the API endpoints

## Troubleshooting

If policies still don't appear:

1. **Check API logs** for messages like:
   ```
   ✅ Loaded policies from valid_policies.json
   ```

2. **Verify data exists**:
   ```bash
   ls -la data/policy_*.json
   ls -la data/valid_policies.json
   ```

3. **Check tenant ID**: The default tenant ID is `00000000-0000-0000-0000-000000000001`. Make sure your policies have the correct `tenant_id` field.

4. **Manual migration**: If needed, you can manually copy policies:
   ```bash
   # Copy valid_policies.json to the expected location
   cp data/valid_policies.json /tmp/policies_00000000-0000-0000-0000-000000000002.json
   ```

## Next Steps

Once your data is visible:
- ✅ All your existing policies will be available
- ✅ Baselines and analyses will be accessible
- ✅ You can continue working with your preconfigured data
- ✅ New data will be saved to the standard location
