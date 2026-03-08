# Phase 2: Baseline Refresh System - Implementation Plan

## Overview

Phase 2 implements the Baseline Refresh System, which automatically refreshes baselines when new data periods arrive and detects baseline shifts over time.

## Requirements from Enterprise Architecture

Based on `ENTERPRISE_CONTINUOUS_SYSTEM_ARCHITECTURE.md`, Phase 2 needs:

1. **Automatic Baseline Refresh Logic**
   - When new data period arrives, determine if baseline should be refreshed
   - Use baseline-eligible data periods (pre-policy periods)
   - Support rolling baseline windows (e.g., last 12 months)
   - Support fixed baseline windows (e.g., specific date range)

2. **Baseline Versioning**
   - Track baseline versions over time
   - Store baseline snapshots with version numbers
   - Link baselines to data periods used
   - Store baseline metrics and metadata

3. **Baseline Shift Detection**
   - Compare current baseline to previous baseline
   - Detect significant shifts in utilization patterns
   - Alert/flag when shifts are detected
   - Store shift detection results

## Implementation Components

### 1. Baseline Storage System
**File**: `apps/api/src/uepi_api/storage_baselines.py`

Functions needed:
- `create_baseline()` - Create a new baseline version
- `get_baseline()` - Get a baseline by ID
- `list_baselines()` - List all baselines for a tenant
- `get_latest_baseline()` - Get the latest baseline
- `get_baseline_by_data_period()` - Get baseline that used a specific data period

### 2. Baseline Refresh Logic
**File**: `apps/api/src/uepi_api/baseline_refresh.py`

Functions needed:
- `should_refresh_baseline()` - Determine if baseline should be refreshed
- `refresh_baseline()` - Refresh baseline using new data periods
- `compute_baseline_metrics()` - Compute baseline metrics from data periods
- `detect_baseline_shift()` - Compare two baselines and detect shifts

### 3. Baseline API Endpoints
**File**: `apps/api/src/uepi_api/routers/baselines.py`

Endpoints needed:
- `POST /baselines/refresh` - Manually trigger baseline refresh
- `GET /baselines` - List all baselines
- `GET /baselines/latest` - Get latest baseline
- `GET /baselines/{baseline_id}` - Get specific baseline
- `GET /baselines/{baseline_id}/shift` - Get shift detection for a baseline

### 4. Integration Points

- **Data Period Integration**: When data period is created (if baseline-eligible), check if baseline should be refreshed
- **Baseline Analysis Integration**: Link baseline analyses to baseline versions

## File Structure

```
apps/api/src/uepi_api/
├── storage_baselines.py          # Baseline storage (NEW)
├── baseline_refresh.py            # Baseline refresh logic (NEW)
└── routers/
    └── baselines.py               # Baseline API endpoints (NEW)

data/
└── baselines/
    └── {tenant_id}/
        └── baseline-{baseline_id}.json
```

## Baseline Data Model

```python
{
    "baseline_id": "uuid",
    "tenant_id": "uuid",
    "version": 1,
    "baseline_type": "ROLLING" | "FIXED",
    "window_start_date": "ISO date",
    "window_end_date": "ISO date",
    "data_period_ids": ["uuid", ...],  # Data periods used
    "baseline_metrics": {
        "total_members": int,
        "total_claims": int,
        "total_cost": float,
        "utilization_per_1k": float,
        "cost_per_member": float,
        # ... other metrics
    },
    "computed_at": "ISO timestamp",
    "computed_by": "system" | "user_id",
    "parent_baseline_id": "uuid | null",  # For versioning
    "shift_detected": bool,
    "shift_summary": {
        "utilization_change_pct": float,
        "cost_change_pct": float,
        "significant_shift": bool,
    },
    "metadata": {},
}
```

## Implementation Steps

1. ✅ Create baseline storage system (`storage_baselines.py`)
2. ✅ Create baseline refresh logic (`baseline_refresh.py`)
3. ✅ Create baseline API endpoints (`routers/baselines.py`)
4. ✅ Integrate baseline refresh trigger on data period creation
5. ✅ Add baseline versioning support
6. ✅ Add baseline shift detection
7. ✅ Test baseline refresh workflow

## Notes

- Baselines are computed from baseline-eligible data periods only
- Baseline refresh is triggered automatically when new baseline-eligible periods arrive
- Baseline versions track changes over time
- Shift detection compares consecutive baseline versions
