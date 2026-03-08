# Predicted Impact - Database-Only Implementation

## ✅ Fixed: All Predicted Impact Now Uses Database Only

### Issue
The code was storing predicted impact in `policy_metadata_json` (JSONB column) instead of the dedicated `PolicyPredictedImpact` database table. While this is still in the database, it's not using the proper table structure.

### Solution
Updated all predicted impact operations to use the dedicated `policy_predicted_impacts` database table as the **primary storage**, with metadata JSON as a fallback/backward compatibility layer.

## Changes Made

### 1. ✅ Generate Predicted Impact (`POST /policies/{policy_id}/predicted-impact`)

**Before:**
- Stored only in `policy_metadata_json`

**After:**
- **Primary storage**: `PolicyPredictedImpact` database table (via `store_predicted_impact()`)
- **Secondary storage**: `policy_metadata_json` (for backward compatibility)
- Links to baseline via `baseline_id` foreign key

### 2. ✅ Get Predicted Impact (`GET /policies/{policy_id}/predicted-impact`)

**Before:**
- Retrieved only from `policy_metadata_json`

**After:**
- **Primary source**: `PolicyPredictedImpact` database table (via `get_predicted_impact()`)
- **Fallback**: `policy_metadata_json` (for backward compatibility)

### 3. ✅ Create Policy with Predicted Impact (`POST /policies`)

**Before:**
- Stored only in `policy_metadata_json`

**After:**
- **Primary storage**: `PolicyPredictedImpact` database table
- **Secondary storage**: `policy_metadata_json` (for backward compatibility)

### 4. ✅ Generate All Policies Predicted Impact (`POST /policies/generate-predicted-impact`)

**Before:**
- Stored only in `policy_metadata_json`

**After:**
- **Primary storage**: `PolicyPredictedImpact` database table
- **Secondary storage**: `policy_metadata_json` (for backward compatibility)

## Database Schema

Predicted impact is stored in the `policy_predicted_impacts` table:

```sql
CREATE TABLE policy_predicted_impacts (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    metrics_json JSONB NOT NULL,
    model_version VARCHAR,
    confidence FLOAT,
    predicted_at TIMESTAMP NOT NULL,
    prediction_method VARCHAR,
    baseline_id UUID REFERENCES baselines(id) ON DELETE SET NULL,
    data_period_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Storage Functions

All storage operations use `apps/api/src/uepi_api/storage_policy_predicted_impact.py`:

- `get_predicted_impact()` - Get from database table
- `store_predicted_impact()` - Store in database table

**These functions are database-only** - no file operations.

## Verification

To verify predicted impact is stored in database:

```sql
SELECT 
    policy_id, 
    predicted_at, 
    prediction_method,
    confidence,
    baseline_id
FROM policy_predicted_impacts
WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
ORDER BY predicted_at DESC;
```

## Legacy Code

- `apps/api/src/uepi_api/routers/policies_file.py` - **NOT USED** (not included in main.py)
- This file is legacy and should not be used
- All active endpoints use `policies.py` which now uses database-only storage

## Summary

✅ **All predicted impact operations now:**
- Use dedicated `PolicyPredictedImpact` database table (primary storage)
- Store in `policy_metadata_json` as backup/backward compatibility
- Link to baselines via `baseline_id` foreign key
- Are database-only (no file operations)
- Use policy-specific baselines when available

✅ **No file-based operations** - everything is in the database!
