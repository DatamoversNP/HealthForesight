# Phase 3: Observed Impact Enhancement - Implementation Plan

## Overview

Phase 3 implements enhanced observed impact tracking with multi-period observation tracking, enhanced behavioral explanation, and observation period linking.

## Requirements from Enterprise Architecture

Based on `ENTERPRISE_CONTINUOUS_SYSTEM_ARCHITECTURE.md`, Phase 3 needs:

1. **Multi-Period Observation Tracking**
   - Track observations across multiple data periods
   - Link observations to data periods
   - Support periodic observation updates as new data arrives
   - Track observation history over time

2. **Enhanced Behavioral Explanation**
   - Store behavioral explanations (substitution patterns, provider response, patient response)
   - Link to observed impact metrics
   - Support detailed behavioral analysis

3. **Observation Period Linking**
   - Link observations to specific data periods
   - Link to policy versions
   - Link to baseline versions
   - Link to predicted impact versions
   - Enable traceability

## Implementation Components

### 1. Observed Impact Storage System
**File**: `apps/api/src/uepi_api/storage_observations.py`

Functions needed:
- `create_observation()` - Create a new observed impact observation
- `get_observation()` - Get an observation by ID
- `list_observations()` - List observations (with filtering)
- `get_observations_for_policy()` - Get all observations for a policy
- `get_observations_for_period()` - Get observations for a data period
- `update_observation()` - Update an observation

### 2. Observation Enhancement Logic
**File**: `apps/api/src/uepi_api/observation_enhancement.py`

Functions needed:
- `create_observation_from_analysis()` - Create observation from impact analysis result
- `link_observation_to_periods()` - Link observation to data periods
- `enhance_with_comparisons()` - Add baseline and predicted comparisons
- `generate_behavioral_explanation()` - Generate behavioral explanation summary

### 3. Observation API Endpoints
**File**: `apps/api/src/uepi_api/routers/observations.py`

Endpoints needed:
- `POST /observations` - Create observation (from analysis)
- `GET /observations` - List observations
- `GET /observations/{observation_id}` - Get specific observation
- `GET /observations/{observation_id}/comparison` - Get comparisons (baseline, predicted)
- `GET /policies/{policy_id}/observations` - List observations for policy
- `GET /periods/{period_id}/observations` - List observations for data period

### 4. Integration Points

- **Impact Analysis Integration**: When impact analysis completes, create observation
- **Data Period Integration**: Link observations to data periods
- **Baseline Integration**: Link observations to baseline versions
- **Predicted Impact Integration**: Link observations to predicted impact

## File Structure

```
apps/api/src/uepi_api/
├── storage_observations.py          # Observation storage (NEW)
├── observation_enhancement.py        # Observation enhancement logic (NEW)
└── routers/
    └── observations.py               # Observation API endpoints (NEW)

data/
└── observations/
    └── {tenant_id}/
        └── observation-{observation_id}.json
```

## Observation Data Model

```python
{
    "observation_id": "uuid",
    "tenant_id": "uuid",
    "policy_id": "uuid",
    "policy_version_id": "uuid",
    "data_period_id": "uuid",  # Primary data period for this observation
    "data_period_ids": ["uuid", ...],  # All periods used in observation
    "observation_type": "PERIODIC" | "CUMULATIVE",
    "observation_period_start": "ISO date",
    "observation_period_end": "ISO date",
    "baseline_version_id": "uuid",
    "prediction_id": "uuid",  # Predicted impact ID
    "computed_at": "ISO timestamp",
    "metrics": {
        "observed_effect_size": float,
        "observed_percent_change": float,
        "confidence_interval": [float, float],
        "p_value": float,
        "utilization_per_1k": float,
        "cost_per_member": float,
        # ... other metrics
    },
    "comparisons": {
        "vs_baseline": {
            "baseline_utilization_per_1k": float,
            "change_from_baseline": float,
            "change_from_baseline_pct": float,
            "baseline_version_id": "uuid",
        },
        "vs_predicted": {
            "predicted_effect_size": float,
            "prediction_error": float,
            "prediction_error_pct": float,
            "prediction_accuracy_pct": float,
            "within_predicted_range": bool,
            "prediction_id": "uuid",
        },
    },
    "behavioral_explanation": {
        "substitution_patterns": [...],
        "provider_response": {...},
        "patient_response": {...},
        "summary": "text",
    },
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp",
    "metadata": {},
}
```

## Implementation Steps

1. ✅ Create observation storage system (`storage_observations.py`)
2. ✅ Create observation enhancement logic (`observation_enhancement.py`)
3. ✅ Create observation API endpoints (`routers/observations.py`)
4. ✅ Integrate observation creation from impact analysis
5. ✅ Add comparison enhancement (baseline, predicted)
6. ✅ Add behavioral explanation enhancement
7. ✅ Test observation workflow

## Notes

- Observations are created from impact analysis results (Stage 4)
- Observations link to data periods, policy versions, baseline versions, and predictions
- Comparisons are computed and stored with observations
- Behavioral explanations can be enhanced/updated over time
