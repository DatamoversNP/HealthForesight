# Real Data vs Mock Data

## Current Status

**Observations are currently using MOCK/HARDCODED data** (varied by policy_id for uniqueness).

## How the System Works

The system has **TWO paths** for creating observations:

### 1. **Real Data Path** (What you want)
- Uses actual claims data from CSV/parquet files
- Processes claims to compute real utilization and cost metrics
- Located in: `apps/api/src/uepi_api/routers/analyses_file.py`
- Endpoint: `POST /api/v1/analyses/impact` (file-based version)
- Requires: Claims data files in `apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/`

### 2. **Mock Data Path** (Current - Development Fallback)
- Used when analyses are PENDING or no claims data found
- Located in: `apps/api/src/uepi_api/routers/observations.py` (line 115-165)
- Generates mock results with varied values based on policy_id
- This is what your current observations are using

## How to Use Real Data

### Option 1: Run Impact Analyses with Real Claims Data

1. **Check if claims data exists:**
   ```bash
   ls apps/data/target_data_model/00000000-0000-0000-0000-000000000001/CLAIMS_LINES/
   ```

2. **Run impact analysis for a policy:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analyses/impact" \
     -H "Authorization: Bearer dev-token-123" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_id": "YOUR_POLICY_ID",
       "treatment_filters": {"lob": ["COMMERCIAL"]},
       "pre_window_months": 6,
       "post_window_months": 6
     }'
   ```

3. **Create observation from the analysis:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/observations/from-analysis/{analysis_id}?policy_id={policy_id}" \
     -H "Authorization: Bearer dev-token-123"
   ```

### Option 2: Remove Mock Data Fallback

To force the system to ONLY use real data (fail if no claims data):

1. Remove or comment out the mock data generation in `apps/api/src/uepi_api/routers/observations.py` (lines 115-165)
2. The system will then require real claims data to create observations

## Current Observations

Your current 35 observations were created from PENDING analyses, so they used mock data. To get real data:

1. Delete existing observations (or keep them as examples)
2. Run new impact analyses that process real claims data
3. Create observations from those analyses

## Claims Data Location

The system looks for claims data in:
- `apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/*.csv`
- `apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/*.parquet`

If these files exist with real claims data, the system will use them instead of mock data.
