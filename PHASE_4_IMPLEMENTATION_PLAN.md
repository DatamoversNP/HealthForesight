# Phase 4: Learning Loop System - Implementation Plan

## Overview

Phase 4 implements the Learning Loop System, which learns from observations to improve predictions through elasticity model updates, prediction accuracy tracking, and behavioral model refinement.

## Requirements from Enterprise Architecture

Based on `ENTERPRISE_CONTINUOUS_SYSTEM_ARCHITECTURE.md`, Phase 4 needs:

1. **Elasticity Model Updates**
   - Track elasticity models with versions
   - Learn elasticity coefficients from observations
   - Update models based on observed vs predicted comparisons
   - Support policy-type and service-category specific models

2. **Prediction Accuracy Tracking**
   - Track prediction accuracy over time
   - Compare predicted vs observed impacts
   - Calculate accuracy metrics (MAE, RMSE, etc.)
   - Store accuracy history per policy/model

3. **Behavioral Model Refinement**
   - Refine behavioral models based on observations
   - Update substitution patterns, provider response, patient response models
   - Track model performance over time

## Implementation Components

### 1. Learning Model Storage System
**File**: `apps/api/src/uepi_api/storage_learning.py`

Functions needed:
- `create_elasticity_model()` - Create a new elasticity model version
- `get_elasticity_model()` - Get elasticity model by ID
- `list_elasticity_models()` - List elasticity models
- `get_latest_elasticity_model()` - Get latest model for policy type/service category
- `update_elasticity_model()` - Update elasticity model
- `create_accuracy_record()` - Record prediction accuracy
- `get_accuracy_history()` - Get accuracy history for a policy/model

### 2. Learning Logic
**File**: `apps/api/src/uepi_api/learning_loop.py`

Functions needed:
- `calculate_prediction_accuracy()` - Calculate accuracy from observation
- `update_elasticity_from_observations()` - Update elasticity coefficients
- `refine_behavioral_model()` - Refine behavioral models
- `learn_from_observation()` - Main learning function

### 3. Learning API Endpoints
**File**: `apps/api/src/uepi_api/routers/learning.py`

Endpoints needed:
- `GET /learning/accuracy/{policy_id}` - Get prediction accuracy for policy
- `GET /learning/accuracy/history/{policy_id}` - Get accuracy history
- `POST /learning/update-elasticity` - Update elasticity model
- `GET /learning/elasticity-models` - List elasticity models
- `GET /learning/elasticity-models/{model_id}` - Get elasticity model
- `POST /learning/learn-from-observation` - Trigger learning from observation

### 4. Integration Points

- **Observation Integration**: When observation is created, trigger learning
- **Prediction Integration**: Link predictions to elasticity models
- **Accuracy Tracking**: Track accuracy for each prediction-observation pair

## File Structure

```
apps/api/src/uepi_api/
├── storage_learning.py            # Learning model storage (NEW)
├── learning_loop.py                # Learning logic (NEW)
└── routers/
    └── learning.py                 # Learning API endpoints (NEW)

data/
└── learning/
    ├── elasticity_models/
    │   └── {tenant_id}/
    │       └── model-{model_id}.json
    └── accuracy_history/
        └── {tenant_id}/
            └── accuracy-{record_id}.json
```

## Data Models

### Elasticity Model
```json
{
  "model_id": "uuid",
  "tenant_id": "uuid",
  "version": "v1.3",
  "policy_type": "PRIOR_AUTH",
  "service_category": "IMAGING",
  "elasticity_coefficients": {
    "utilization_elasticity": -0.85,
    "cost_elasticity": -0.78
  },
  "learned_from_observations": ["obs-1", "obs-2", "obs-3"],
  "confidence": 0.82,
  "training_metrics": {
    "observation_count": 15,
    "mae": 2.5,
    "rmse": 3.2
  },
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "metadata": {}
}
```

### Accuracy Record
```json
{
  "accuracy_id": "uuid",
  "tenant_id": "uuid",
  "policy_id": "uuid",
  "observation_id": "uuid",
  "prediction_id": "uuid",
  "elasticity_model_id": "uuid",
  "predicted_effect_size": -12.5,
  "observed_effect_size": -15.2,
  "prediction_error": -2.7,
  "prediction_error_pct": 21.6,
  "prediction_accuracy_pct": 78.4,
  "metrics": {
    "mae": 2.7,
    "rmse": 3.1,
    "within_range": true
  },
  "recorded_at": "ISO timestamp",
  "metadata": {}
}
```

## Implementation Steps

1. ✅ Create learning model storage system (`storage_learning.py`)
2. ✅ Create learning loop logic (`learning_loop.py`)
3. ✅ Create learning API endpoints (`routers/learning.py`)
4. ✅ Integrate learning trigger from observations
5. ✅ Add accuracy tracking
6. ✅ Add elasticity model updates
7. ✅ Test learning workflow

## Notes

- Learning is triggered when observations are created
- Elasticity models are updated based on observed vs predicted comparisons
- Accuracy is tracked over time to monitor model performance
- Models can be policy-type and service-category specific
