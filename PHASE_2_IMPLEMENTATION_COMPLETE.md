# Phase 2: Baseline Refresh System - COMPLETE ✅

## Summary

Successfully implemented Phase 2: Baseline Refresh System, which automatically refreshes baselines when new data periods arrive and detects baseline shifts over time.

## Completed Components

### ✅ 1. Baseline Storage System
**File**: `apps/api/src/uepi_api/storage_baselines.py`

**Functions Implemented**:
- `create_baseline()` - Create a new baseline version
- `get_baseline()` - Get a baseline by ID
- `list_baselines()` - List all baselines (with optional filtering)
- `get_latest_baseline()` - Get the latest baseline
- `get_baseline_by_data_period()` - Get baseline that used a specific data period
- `update_baseline()` - Update an existing baseline

**Features**:
- File-based storage in `data/baselines/{tenant_id}/`
- Baseline indexing for efficient queries
- Support for policy-specific and general baselines
- Baseline versioning support

### ✅ 2. Baseline Refresh Logic
**File**: `apps/api/src/uepi_api/baseline_refresh.py`

**Functions Implemented**:
- `should_refresh_baseline()` - Determine if baseline should be refreshed
- `refresh_baseline()` - Refresh baseline using new data periods
- `compute_baseline_metrics()` - Compute baseline metrics from data periods (simplified)
- `detect_baseline_shift()` - Compare two baselines and detect shifts

**Features**:
- Automatic refresh detection (new periods, age-based)
- Support for ROLLING and FIXED baseline windows
- Baseline versioning with parent-child relationships
- Shift detection (5% threshold for significant shifts)
- Simplified metrics computation (can be enhanced with actual data aggregation)

### ✅ 3. Baseline API Endpoints
**File**: `apps/api/src/uepi_api/routers/baselines.py`

**Endpoints Implemented**:
- `POST /api/v1/baselines/refresh` - Manually trigger baseline refresh
- `GET /api/v1/baselines` - List all baselines (with optional filtering)
- `GET /api/v1/baselines/latest` - Get latest baseline
- `GET /api/v1/baselines/{baseline_id}` - Get specific baseline
- `GET /api/v1/baselines/{baseline_id}/shift` - Get shift detection results
- `GET /api/v1/baselines/for-policy/{policy_id}` - Get baseline for policy
- `GET /api/v1/baselines/should-refresh` - Check if refresh is needed

### ✅ 4. Integration Points

**Data Period Integration**:
- Modified `integration_helpers.py::create_data_period_from_ingestion()`
- When a baseline-eligible data period is created, automatically triggers baseline refresh check
- If refresh is needed, automatically refreshes baseline

**Router Registration**:
- Added baseline router to `main.py`
- Router registered with prefix `/api/v1` and tag `Baselines`

## Baseline Data Model

```json
{
  "baseline_id": "uuid",
  "tenant_id": "uuid",
  "version": 1,
  "baseline_type": "ROLLING" | "FIXED",
  "window_start_date": "ISO date",
  "window_end_date": "ISO date",
  "data_period_ids": ["uuid", ...],
  "baseline_metrics": {
    "total_members": int,
    "total_claims": int,
    "total_cost": float,
    "utilization_per_1k": float,
    "cost_per_member": float,
    "cost_per_member_per_month": float,
    "claims_per_member": float,
    "data_periods_count": int,
    "window_months": int
  },
  "computed_at": "ISO timestamp",
  "computed_by": "system" | "user_id",
  "parent_baseline_id": "uuid | null",
  "policy_id": "uuid | null",
  "shift_detected": bool,
  "shift_summary": {
    "shift_detected": bool,
    "significant_shift": bool,
    "utilization_change_pct": float,
    "cost_change_pct": float,
    "current_utilization_per_1k": float,
    "previous_utilization_per_1k": float,
    "current_cost_pmpm": float,
    "previous_cost_pmpm": float
  },
  "refresh_reason": "NEW_DATA" | "MANUAL" | "POLICY_UPDATE",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "metadata": {}
}
```

## How It Works

### Automatic Baseline Refresh

1. **Data Period Creation**:
   - When ingestion completes, data period is created
   - If period is baseline-eligible, refresh check is triggered

2. **Refresh Decision**:
   - `should_refresh_baseline()` checks:
     - If no baseline exists → Create initial baseline
     - If new periods since last baseline → Refresh
     - If baseline is >90 days old → Refresh recommended

3. **Baseline Refresh**:
   - `refresh_baseline()` creates new baseline:
     - Gets baseline-eligible periods
     - Filters to window (ROLLING: last N months, FIXED: all periods)
     - Computes metrics from periods
     - Detects shifts from previous baseline
     - Creates new version with parent reference

4. **Shift Detection**:
   - Compares current vs previous baseline metrics
   - Detects significant shifts (>5% change)
   - Stores shift summary in baseline

### Manual Baseline Refresh

Users can manually trigger baseline refresh via:
- `POST /api/v1/baselines/refresh` endpoint
- Specify baseline type, window months, refresh reason

## Files Created

1. **`apps/api/src/uepi_api/storage_baselines.py`** - Baseline storage system
2. **`apps/api/src/uepi_api/baseline_refresh.py`** - Baseline refresh logic
3. **`apps/api/src/uepi_api/routers/baselines.py`** - Baseline API endpoints
4. **`DEFERRED_TRACEABILITY_TASKS.md`** - Tracked deferred tasks
5. **`PHASE_2_IMPLEMENTATION_PLAN.md`** - Implementation plan (reference)

## Files Modified

1. **`apps/api/src/uepi_api/integration_helpers.py`** - Added baseline refresh trigger
2. **`apps/api/src/uepi_api/main.py`** - Registered baselines router

## Notes

### Simplified Metrics Computation

The `compute_baseline_metrics()` function currently uses simplified/estimated metrics. In production, this would:
- Load actual claims data from data periods
- Aggregate metrics from real data
- Handle member counts, enrollment, etc.
- Support more sophisticated aggregations

### Future Enhancements

- Enhanced metrics computation with real data aggregation
- Policy-specific baseline refresh on policy updates
- Baseline comparison endpoints
- Baseline visualization/metrics export
- Configurable shift detection thresholds

## Testing Recommendations

1. **Test Baseline Creation**:
   - Create baseline-eligible data periods
   - Verify baseline is automatically created
   - Check baseline metrics and version

2. **Test Baseline Refresh**:
   - Add new baseline-eligible periods
   - Verify baseline refresh is triggered
   - Check version increment and shift detection

3. **Test Manual Refresh**:
   - Call `POST /api/v1/baselines/refresh`
   - Verify baseline is refreshed
   - Check refresh reason is set correctly

4. **Test Shift Detection**:
   - Create baseline with metrics
   - Create another baseline with different metrics
   - Verify shift detection identifies changes

## Status

✅ **Phase 2: Baseline Refresh System - COMPLETE**

Ready to proceed with:
- Testing the baseline refresh system
- Phase 3 (Observed Impact Enhancement)
- Or other priorities

## Deferred Tasks

The following traceability integration tasks remain deferred:
- Add traceability to predicted impact generation
- Add traceability to baseline analyses
- Add traceability to observed impacts

See `DEFERRED_TRACEABILITY_TASKS.md` for details.
