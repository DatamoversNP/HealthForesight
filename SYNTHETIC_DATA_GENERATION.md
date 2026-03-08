# Synthetic Data Generation Guide

## Overview

This system uses **comprehensive synthetic data generation** to create realistic payer/client data. **No hardcoded data exists in the code** - everything is generated from data files.

## Generated Data Types

### 1. Policies with Full Lifecycle Management
- **Policies**: Complete policy definitions with scope, levers, enforcement
- **Policy Versions**: Version history with state transitions (DRAFT → PROPOSED → APPROVED → ACTIVE)
- **Policy Assumptions**: Elasticity ranges, substitution rates, lag months
- **Policy Guardrails**: Rollback triggers with thresholds and actions
- **Policy Changelogs**: Complete audit trail of all changes

### 2. Observations
- Generated from synthetic post-policy claims data
- Includes observed vs predicted comparisons
- Data quality metrics (completeness, validity, timeliness)

### 3. Predicted Impacts
- Calculated from policy assumptions
- Includes utilization and cost impact metrics
- Confidence scores and method tracking

### 4. Source Data
- Member master data
- Provider directories
- Claims data (pre and post-policy)
- Eligibility/enrollment data

## Generation Scripts

### Primary Scripts

1. **`generate_complete_payer_synthetic_data.py`**
   - Generates policies with full Epic 2 lifecycle features
   - Creates versions, assumptions, guardrails, changelogs
   - Generates predicted impacts
   - **Usage**: `python3 scripts/generate_complete_payer_synthetic_data.py`

2. **`generate_observations_from_synthetic_data.py`**
   - Generates observations from policies and predicted impacts
   - Creates realistic variance in observed metrics
   - **Usage**: `python3 scripts/generate_observations_from_synthetic_data.py --days 30`

3. **`generate_all_synthetic_data.sh`**
   - Master script that runs all generation steps
   - **Usage**: `./scripts/generate_all_synthetic_data.sh`

### Supporting Scripts

- `generate_all_comprehensive_synthetic.py`: Generates source data (members, providers, claims)
- `generate_post_policy_synthetic_data.py`: Generates post-policy claims data
- `generate_predicted_impact_all.py`: Generates predicted impacts for all policies

## Data Storage Structure

```
data/
├── policy_versions/
│   └── {tenant_id}/
│       └── policy-{policy_id}/
│           ├── version-1.json
│           ├── version-2.json
│           └── versions_index.json
├── policy_assumptions/
│   └── {tenant_id}/
│       └── policy-{policy_id}.json
├── policy_guardrails/
│   └── {tenant_id}/
│       └── policy-{policy_id}.json
├── policy_changelog/
│   └── {tenant_id}/
│       └── policy-{policy_id}.json
├── observations/
│   └── {tenant_id}/
│       └── policy-{policy_id}.json
└── predicted_impacts/
    └── {tenant_id}/
        └── policy-{policy_id}.json

apps/api/data/policies/
└── policy-{policy_id}.json
```

## Policy Templates

The system includes realistic policy templates representing common payer scenarios:

1. **Outpatient MRI Prior Authorization**
   - Type: PRIOR_AUTH
   - Scope: Commercial, MA in NYC, DFW, BOS
   - Assumptions: 10-15% utilization reduction
   - Guardrails: Alert if >25% drop, suspend if cost increases

2. **Step Therapy for Specialty Drugs**
   - Type: STEP_THERAPY
   - Scope: Commercial, MA in multiple markets
   - Assumptions: 12-20% utilization reduction, 3-month lag
   - Guardrails: Alert on utilization or appeals volume

3. **Network Tiering - Outpatient Services**
   - Type: NETWORK_RESTRICTION
   - Scope: Commercial with tiered network
   - Assumptions: 5-10% shift to in-network
   - Guardrails: Rollback if member satisfaction drops

4. **Physical Therapy Visit Limit**
   - Type: DURATION_FREQUENCY_LIMIT
   - Scope: Commercial, MA
   - Assumptions: 4-8% utilization reduction
   - Guardrails: Alert if >15% drop

5. **Telemedicine Coverage Expansion**
   - Type: COVERAGE
   - Scope: Commercial, MA in multiple markets
   - Assumptions: 15-25% utilization increase
   - Guardrails: Alert if cost increases

## No Hardcoded Data

**All data comes from files:**
- ✅ Policies loaded from JSON files
- ✅ Versions, assumptions, guardrails, changelogs from files
- ✅ Observations from files
- ✅ Predicted impacts from files
- ✅ Source data from CSV/JSON files

**Only exception:** AuthContext uses a fallback demo user when API is unavailable (for development only).

## Running the Generation

### Quick Start

```bash
# Generate all synthetic data
./scripts/generate_all_synthetic_data.sh
```

### Step-by-Step

```bash
# Step 1: Generate policies with lifecycle data
python3 scripts/generate_complete_payer_synthetic_data.py

# Step 2: Generate observations
python3 scripts/generate_observations_from_synthetic_data.py --days 30

# Step 3: Generate source data (if needed)
python3 scripts/generate_all_comprehensive_synthetic.py --count 100 --months 36
```

## Verification

After generation, verify data:

```bash
# Check policies
ls -la apps/api/data/policies/

# Check versions
ls -la data/policy_versions/00000000-0000-0000-0000-000000000001/

# Check observations
ls -la data/observations/00000000-0000-0000-0000-000000000001/
```

## Epic 2 Policy Functionality

All Epic 2 features are fully implemented and use synthetic data:

✅ **Policy Versioning**
- Automatic version creation
- Version comparison
- State transitions

✅ **Assumptions Management**
- Elasticity ranges
- Substitution rates
- Lag months
- Confidence scoring

✅ **Guardrails Management**
- Threshold-based triggers
- Multiple action types (alert, suspend, rollback)
- Real-time checking

✅ **Changelog**
- Automatic entry creation
- Complete audit trail
- Version linking

✅ **Workspace UI**
- Tabbed interface
- All lifecycle features accessible
- Real-time updates

## Next Steps

1. Run the generation scripts to create data
2. Start the API server: `cd apps/api && python -m uvicorn uepi_api.main:app --reload`
3. Access the UI and verify all policy functionality works with synthetic data


