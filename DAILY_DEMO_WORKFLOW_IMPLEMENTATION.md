# Daily Demo Workflow Implementation

## Summary

Created a comprehensive daily demo workflow that:
1. Generates daily synthetic data (claims/enrollment) to mimic real-world patterns
2. Loads data into the database
3. Runs impact analysis for all active policies
4. Creates observations from analysis results
5. Provides rich visualizations and trend analysis

## Components Created

### 1. Daily Demo Workflow Script ✅

**File**: `apps/api/scripts/daily_demo_workflow.py`

**Features**:
- Generates synthetic claims for a specific day with realistic patterns
- Generates enrollment records for the month
- Loads data directly into database via `CanonicalDataRepository`
- Runs impact analysis for all active policies
- Creates observations from impact analysis results
- Supports command-line arguments for flexibility

**Usage**:
```bash
python3 apps/api/scripts/daily_demo_workflow.py \
  --date 2026-02-05 \
  --tenant-id 00000000-0000-0000-0000-000000000001
```

**Options**:
- `--date`: Target date (YYYY-MM-DD). Default: yesterday
- `--tenant-id`: Tenant ID. Default: DEFAULT_TENANT_ID
- `--skip-data`: Skip data generation (only run observations)
- `--skip-observations`: Skip observation creation (only generate data)

### 2. Updated Daily Jobs Router ✅

**File**: `apps/api/src/uepi_api/routers/daily_jobs.py`

**Changes**:
- Updated to use `daily_demo_workflow.py` instead of old script
- Maintains same API interface for backward compatibility
- Runs workflow in background via FastAPI BackgroundTasks

**Endpoint**: `POST /api/v1/jobs/daily-data-and-observations`

**Parameters**:
- `target_date` (optional): Date in YYYY-MM-DD format. Default: yesterday
- `run_observations` (optional): Boolean. Default: true

### 3. Enhanced Observations API ✅

**File**: `apps/api/src/uepi_api/routers/observations.py`

**New Features**:
- `include_trends` parameter in `list_observations_route`
  - Calculates trend metrics (utilization_trend, cost_trend)
  - Groups observations by policy
  - Adds trend metadata to each observation
- Enhanced `get_observations_for_policy_route`
  - Includes trend analysis by default
  - Calculates trend direction (increasing/decreasing/stable)
  - Provides observation count

**Trend Data Structure**:
```json
{
  "metadata": {
    "trend": {
      "utilization_trend": 5.2,
      "cost_trend": -10.5,
      "observation_count": 7,
      "trend_direction": "increasing"
    }
  }
}
```

### 4. Updated API Client ✅

**File**: `apps/web/src/lib/api.ts`

**Changes**:
- Updated `listObservations` to support `include_trends` parameter
- Existing `triggerDailyJob` method already supports the workflow

## Data Generation Details

### Synthetic Claims Generation

- **Service Categories**: PRIMARY_CARE, SPECIALTY_CARE, IMAGING, EMERGENCY, URGENT_CARE, PHARMACY, REHAB
- **Realistic Patterns**:
  - Utilization rates by category (e.g., 80% for primary care, 25% for imaging)
  - Cost variation (±30% from average)
  - Realistic CPT/HCPCS codes
  - Member and provider distribution

### Daily Variation

- Claims per day: ~500 (with ±10% random variation)
- Member count: 10,000 (configurable)
- Provider count: 1,000 (configurable)

## Observation Creation Flow

1. **Impact Analysis**: For each active policy
   - Creates `Analysis` record
   - Triggers `policy_impact_job` (async Celery task)
   - Uses 30-day pre/post windows

2. **Observation Creation**: After impact analysis completes
   - Reads `ImpactAnalysisResult` from database
   - Extracts metrics, comparisons, behavioral explanations
   - Creates `Observation` record with full context

3. **Trend Calculation**: When `include_trends=true`
   - Groups observations by policy
   - Sorts by date
   - Calculates utilization and cost trends
   - Determines trend direction

## Frontend Integration

### Observation Analysis Page

The existing `ObservationAnalysisPage.tsx` already has:
- Policy selection dropdown
- Observation listing
- Trend visualization (needs enhancement)

### Recommended Enhancements

1. **Policy Dropdown**: Filter observations by policy
2. **Trend Charts**: Show utilization and cost trends over time
3. **Focus Areas**: Highlight observations that need attention
   - High prediction error
   - Significant deviation from baseline
   - Unusual behavioral patterns
4. **Daily Job Trigger**: Button to run daily workflow
5. **Real-time Updates**: Refresh observations after job completes

## Usage Workflow

### Initial Setup

1. Run baseline analysis (if not already done)
2. Generate predicted impact for all policies

### Daily Operations

1. **Trigger Daily Job**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/jobs/daily-data-and-observations" \
     -H "Authorization: Bearer dev-token-123" \
     -H "Content-Type: application/json" \
     -d '{"target_date": "2026-02-05", "run_observations": true}'
   ```

2. **View Observations**:
   - Navigate to Observations page
   - Select policy from dropdown
   - View trends and metrics

3. **Analyze Trends**:
   - Review utilization trends
   - Check cost impact
   - Identify focus areas

## Database Tables Used

- `claims_lines`: Daily claims data
- `enrollment_records`: Monthly enrollment
- `analyses`: Impact analysis records
- `impact_analysis_results`: Analysis results (JSONB)
- `observations`: Observation records with metrics and comparisons

## Next Steps

1. **Frontend Enhancements**:
   - Add rich trend visualizations
   - Implement focus area highlighting
   - Add daily job status indicator
   - Show real-time observation updates

2. **Scheduling**:
   - Set up Celery Beat or cron job for daily execution
   - Configure notification on job completion/failure

3. **Data Quality**:
   - Add validation for generated data
   - Ensure realistic patterns over time
   - Add seasonal variation

4. **Performance**:
   - Optimize bulk inserts
   - Add caching for trend calculations
   - Parallelize impact analysis jobs

---

**Status**: ✅ Core Implementation Complete
**Date**: February 6, 2026
**Ready for**: Frontend enhancements and scheduling setup

