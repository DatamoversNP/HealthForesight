# HealthForesight - Enterprise Continuous System Architecture

## Vision

HealthForesight operates as a **continuous Utilization Elasticity & Policy Impact Intelligence system** that learns and adapts over time as new data arrives and policies evolve. The system operates in repeating cycles, not one-time analyses.

## Core Principles

1. **Separation of Concerns**: Baseline, Predicted, and Observed Impact are always clearly separated
2. **Traceability**: Every insight is traceable to a specific data period and policy version
3. **Behavioral Modeling**: Provider and patient behavior are modeled only to explain and predict utilization and cost changes
4. **Transparency**: The system makes it obvious when insights are refreshed due to new data or policy changes

## System Architecture

### Component 1: Data Period Management

**Purpose**: Track and version data snapshots over time

**Data Period Model**:
```json
{
  "period_id": "2024-Q1-v1",
  "tenant_id": "...",
  "period_type": "QUARTERLY",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "ingestion_timestamp": "2024-04-05T10:00:00Z",
  "ingestion_id": "...",
  "data_status": "COMPLETE",
  "baseline_eligible": true,
  "policies_effective": ["policy-id-1", "policy-id-2"],
  "version": 1,
  "parent_period_id": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**Key Operations**:
- Create period from ingestion
- Update period when data refreshed
- Determine baseline eligibility (pre-policy vs post-policy)
- Link periods to policy effective dates

### Component 2: Policy Lifecycle Management

**Purpose**: Track policy versions and lifecycle states

**Policy Version Model**:
```json
{
  "policy_id": "...",
  "version_id": "...",
  "version_number": 2,
  "parent_version_id": "...",
  "effective_start_date": "2024-04-01",
  "effective_end_date": null,
  "status": "ACTIVE",
  "scope": {...},
  "policy_levers": [...],
  "created_at": "...",
  "created_by": "...",
  "change_description": "Updated cost sharing from 20% to 30%"
}
```

**Key Operations**:
- Create version on policy update
- Track version relationships
- Manage lifecycle states (DRAFT → ACTIVE → PAUSED → RETIRED)
- Link versions to data periods

### Component 3: Baseline Management

**Purpose**: Establish and refresh baselines as new data arrives

**Baseline Model**:
```json
{
  "baseline_id": "...",
  "version": 1,
  "data_period_id": "2024-Q1-v1",
  "tenant_id": "...",
  "computed_at": "2024-04-05T10:00:00Z",
  "metrics": {
    "utilization_per_1k": 125.5,
    "cost_per_member_per_month": 450.0,
    "provider_archetypes": [...]
  },
  "policy_id": null,  // null for general baseline, policy_id for policy-specific
  "refresh_reason": "NEW_DATA",
  "parent_baseline_id": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**Refresh Logic**:
1. On new data ingestion:
   - Check if data is pre-policy (baseline eligible)
   - If yes, refresh baseline automatically
   - Compare with previous baseline (detect shifts)
   - Update baseline version
2. On policy update:
   - Recalculate baseline for affected scope
   - Mark dependent predictions for review

**Key Operations**:
- Auto-refresh baseline on new pre-policy data
- Detect baseline shifts over time
- Version baselines
- Link baselines to data periods

### Component 4: Predicted Impact Management

**Purpose**: Generate and version predicted impacts

**Prediction Model**:
```json
{
  "prediction_id": "...",
  "policy_id": "...",
  "policy_version_id": "...",
  "baseline_version_id": "...",
  "data_period_id": "2024-Q1-v1",
  "predicted_at": "2024-03-15T10:00:00Z",
  "metrics": {
    "utilization_change_per_1k": -12.5,
    "utilization_change_pct": -8.2,
    "cost_impact_millions": -2.5,
    "confidence_score": 75
  },
  "elasticity_model_version": "v1.2",
  "behavioral_model_version": "v1.1",
  "refresh_reason": "POLICY_UPDATE",
  "created_at": "...",
  "updated_at": "..."
}
```

**Generation Triggers**:
- Policy creation
- Policy update (new version)
- Baseline refresh (optional - refresh predictions)
- Manual refresh

**Key Operations**:
- Generate prediction on policy create/update
- Version predictions
- Link to policy version and baseline version
- Track prediction accuracy over time

### Component 5: Observed Impact Tracking

**Purpose**: Measure and track observed impacts across multiple periods

**Observation Model**:
```json
{
  "observation_id": "...",
  "policy_id": "...",
  "policy_version_id": "...",
  "data_period_id": "2024-Q2-v1",
  "observation_type": "PERIODIC",
  "observation_period_start": "2024-04-01",
  "observation_period_end": "2024-06-30",
  "baseline_version_id": "...",
  "prediction_id": "...",
  "computed_at": "2024-07-05T10:00:00Z",
  "metrics": {
    "observed_effect_size": -15.2,
    "observed_percent_change": -8.5,
    "confidence_interval": [-18.0, -12.4],
    "p_value": 0.02
  },
  "comparisons": {
    "vs_baseline": {
      "baseline_utilization_per_1k": 125.5,
      "change_from_baseline": -15.2,
      "change_from_baseline_pct": -12.1
    },
    "vs_predicted": {
      "predicted_effect_size": -12.5,
      "prediction_error": -2.7,
      "prediction_error_pct": 21.6,
      "prediction_accuracy_pct": 78.4,
      "within_predicted_range": true
    }
  },
  "behavioral_explanation": {
    "substitution_patterns": [...],
    "provider_response": {...},
    "patient_response": {...}
  },
  "created_at": "...",
  "updated_at": "..."
}
```

**Measurement Triggers**:
- New post-policy data ingestion
- Periodic scheduled measurement
- Manual trigger

**Key Operations**:
- Create observation from impact analysis
- Compare observations across periods
- Link to data periods and policy versions
- Generate behavioral explanations

### Component 6: Learning Loop

**Purpose**: Learn from observations to improve predictions

**Elasticity Model**:
```json
{
  "model_id": "...",
  "version": "v1.3",
  "policy_type": "PRIOR_AUTH",
  "service_category": "IMAGING",
  "learned_from_observations": ["obs-1", "obs-2", "obs-3"],
  "elasticity_coefficients": {
    "utilization_elasticity": -0.85,
    "cost_elasticity": -0.78
  },
  "confidence": 0.82,
  "updated_at": "..."
}
```

**Accuracy Tracking**:
```json
{
  "policy_id": "...",
  "accuracy_metrics": {
    "total_predictions": 5,
    "accurate_predictions": 4,
    "accuracy_rate": 0.80,
    "mean_absolute_error": 2.5,
    "mean_absolute_percentage_error": 15.2
  },
  "prediction_history": [
    {
      "prediction_id": "...",
      "observed_id": "...",
      "error": -2.7,
      "error_pct": 21.6,
      "accuracy_pct": 78.4
    }
  ],
  "updated_at": "..."
}
```

**Key Operations**:
- Update elasticity models from observations
- Track prediction accuracy
- Refine behavioral models
- Apply learnings to new predictions

### Component 7: Traceability Framework

**Purpose**: Link all insights to data periods and policy versions

**Traceability Metadata**:
```json
{
  "traceability": {
    "data_period_id": "2024-Q1-v1",
    "data_period_version": 1,
    "policy_version_id": "...",
    "baseline_version_id": "...",
    "created_at": "...",
    "updated_at": "...",
    "refresh_reason": "NEW_DATA",
    "refresh_count": 2,
    "dependencies": [
      {"type": "baseline", "id": "...", "version": 2},
      {"type": "data_period", "id": "...", "version": 1},
      {"type": "policy_version", "id": "...", "version": 2}
    ]
  }
}
```

**Key Operations**:
- Add traceability to all insights
- Query by traceability (data period, policy version)
- Detect refresh triggers
- Generate audit trails

### Component 8: Refresh Indicators

**Purpose**: Make refresh status obvious to users

**Refresh Status Model**:
```json
{
  "refresh_status": {
    "is_stale": false,
    "last_refresh": "2024-04-05T10:00:00Z",
    "refresh_reason": "NEW_DATA",
    "has_updates": false,
    "stale_reason": null,
    "dependent_insights": [
      {"type": "prediction", "id": "...", "needs_refresh": false},
      {"type": "observation", "id": "...", "needs_refresh": false}
    ],
    "refresh_priority": "LOW"
  }
}
```

**Key Operations**:
- Mark insights as stale
- Check refresh status
- Trigger refreshes
- Notify users of updates

## Continuous Workflow (8 Steps)

### Step 1: Data Ingestion ✅
**Status**: Implemented
- Data ingestion pipeline exists
- **Enhancement Needed**: Data period creation/versioning

### Step 2: Policy Create/Update ⚠️
**Status**: Partially implemented
- Policy CRUD exists
- **Enhancement Needed**: Explicit versioning, change tracking

### Step 3: Baseline Establish/Refresh ⚠️
**Status**: Partially implemented
- Baseline analysis exists
- **Enhancement Needed**: Auto-refresh, versioning, shift detection

### Step 4: Predicted Impact Generation ✅
**Status**: Implemented
- Prediction generation exists
- **Enhancement Needed**: Version tracking, refresh indicators

### Step 5: Policy Implementation ⚠️
**Status**: External
- Policy implementation is external
- **Enhancement Needed**: Status synchronization

### Step 6: Observed Impact Measurement ⚠️
**Status**: Partially implemented
- Impact analysis exists
- **Enhancement Needed**: Multi-period tracking, period linking

### Step 7: Learning from Outcomes ❌
**Status**: Not implemented
- **Need**: Elasticity updates, accuracy tracking, behavioral refinement

### Step 8: What-If Scenarios ⚠️
**Status**: Partially implemented
- Simulation exists
- **Enhancement Needed**: Integration with latest learning

## File Storage Structure

```
data/
├── periods/                          # Data period management
│   ├── periods_index.json
│   └── {tenant_id}/
│       └── {period_id}/
│           ├── metadata.json
│           ├── baseline.json
│           └── observations/
│
├── policies/                         # Policy storage (enhanced)
│   └── {tenant_id}/
│       ├── policies.json
│       └── {policy_id}/
│           ├── policy.json
│           ├── versions/
│           │   └── {version_id}.json
│           └── impact/
│               ├── predictions/
│               │   └── {prediction_id}.json
│               └── observations/
│                   └── {observation_id}.json
│
├── analytics/                        # Analytics results
│   ├── baselines/
│   │   └── {baseline_id}.json
│   ├── predictions/
│   │   └── {prediction_id}.json
│   └── observations/
│       └── {observation_id}.json
│
└── learning/                         # Learning artifacts
    └── {tenant_id}/
        ├── elasticity_models/
        │   └── {model_id}.json
        ├── accuracy_tracking/
        │   └── {policy_id}/
        │       └── accuracy_history.json
        └── behavioral_models/
            └── {model_id}.json
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- Data period management system
- Policy version management system
- Traceability framework

### Phase 2: Baseline Refresh (Week 3-4)
- Automatic baseline refresh logic
- Baseline versioning
- Baseline shift detection

### Phase 3: Observed Impact Enhancement (Week 5-6)
- Multi-period observation tracking
- Enhanced behavioral explanation
- Observation period linking

### Phase 4: Learning Loop (Week 7-8)
- Elasticity model updates
- Prediction accuracy tracking
- Behavioral model refinement

### Phase 5: Integration & UI (Week 9-10)
- Refresh indicators in UI
- Traceability display
- Learning metrics dashboard

## API Endpoints (New/Enhanced)

### Data Period Management
- `POST /api/v1/periods` - Create data period
- `GET /api/v1/periods` - List data periods
- `GET /api/v1/periods/{period_id}` - Get period
- `PUT /api/v1/periods/{period_id}` - Update period
- `GET /api/v1/periods/baseline-eligible` - Get baseline-eligible periods

### Policy Versioning
- `GET /api/v1/policies/{policy_id}/versions` - List versions
- `GET /api/v1/policies/{policy_id}/versions/{version_id}` - Get version
- `POST /api/v1/policies/{policy_id}/versions` - Create new version
- `GET /api/v1/policies/{policy_id}/active-version` - Get active version

### Baseline Management
- `POST /api/v1/baselines/refresh` - Refresh baseline
- `GET /api/v1/baselines/{baseline_id}` - Get baseline
- `GET /api/v1/baselines/{baseline_id}/shifts` - Get baseline shifts
- `GET /api/v1/baselines/for-policy/{policy_id}` - Get baseline for policy

### Observed Impact
- `POST /api/v1/observations` - Create observation
- `GET /api/v1/observations/{observation_id}` - Get observation
- `GET /api/v1/policies/{policy_id}/observations` - List observations for policy
- `GET /api/v1/observations/{observation_id}/comparison` - Get comparisons

### Learning
- `GET /api/v1/learning/accuracy/{policy_id}` - Get prediction accuracy
- `POST /api/v1/learning/update-elasticity` - Update elasticity model
- `GET /api/v1/learning/elasticity-models` - List elasticity models

## Next Steps

1. **Review architecture** with stakeholders
2. **Prioritize phases** based on business needs
3. **Start Phase 1** - Data period and policy versioning
4. **Iterate** - Build incrementally with continuous feedback
