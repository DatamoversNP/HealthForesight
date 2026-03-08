# Database Workflow Validation and Fix

## Expected Workflow

1. **Claims data loaded into database** → `claims_lines` table (ClaimsLineDB)
2. **Baseline computed from database** → Query `claims_lines` table
3. **Policies configured and activated** → Stored in `policies` and `policy_versions` tables
4. **Predicted impact computed** → Stored in `analyses` table
5. **Daily claims data loaded** → Written to same `claims_lines` table
6. **Observations computed from database** → Query `claims_lines` based on policy activation dates
7. **Comparisons** → Against baseline (from database) and predicted (from analyses)

## Current Status

✅ **Database tables exist:**
- `claims_lines` (ClaimsLineDB)
- `policies` and `policy_versions`
- `analyses` and `impact_analysis_results`
- `observations`

❌ **Issues:**
- Observations use mock data instead of database queries
- Some code still reads from files instead of database
- Impact analyses use file-based loading instead of database

## Fixes Required

### 1. Create Database-Based Claims Loader for Observations
- Use `CanonicalDataRepository.get_claims_lines()` to query database
- Filter by policy activation date and scope

### 2. Update Observation Computation
- Query `claims_lines` table for pre/post periods based on policy activation
- Compute metrics from database results
- Compare against baseline (from database) and predicted (from analyses)

### 3. Update Impact Analysis to Use Database
- Use `CanonicalDataRepository` instead of file loading
- Query `claims_lines` table with proper filters

### 4. Ensure Daily Data Loading Writes to Database
- Verify ingestion pipelines write to `claims_lines` table
- Use `CanonicalDataRepository.bulk_insert_claims_lines()`

## Implementation Plan

1. Create `load_claims_from_database()` function
2. Update `create_observation_from_analysis_route()` to use database
3. Update `analyses_file.py` to use database (or create `analyses_db.py`)
4. Verify ingestion writes to database
5. Test end-to-end workflow
