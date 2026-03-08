# Predicted Impact Calculation Methodology

## Overview

Predicted Impact (Stage 3.5) generates forward-looking estimates of policy impact **before implementation**. It uses elasticity models, behavioral models, and historical patterns to predict utilization and cost changes.

## 📊 Models Used

### 1. **Elasticity Model** (Primary)
- **Purpose**: Estimates how utilization responds to policy "friction"
- **Type**: Price/Utilization Elasticity Model
- **Formula**: `utilization_change_pct = friction_level × elasticity_coefficient × 100`
- **Default Elasticity Coefficients** (by service category):
  - Imaging: -0.35 (35% reduction per unit of friction)
  - Physical Therapy: -0.40
  - Specialty Care: -0.30
  - Facility Care: -0.25
  - Therapy Services: -0.35
  - General: -0.30

### 2. **Friction Level Model** (Behavioral)
- **Purpose**: Estimates policy "friction" based on lever types and enforcement
- **Range**: 0.0 (no friction) to 1.0 (maximum friction)
- **Calculation**: Based on lever types and enforcement strength
  - Prior Auth: 0.6 base friction
  - Clinical Criteria: 0.5
  - Site of Care: 0.4
  - Quantity Limit: 0.3
  - Cost Sharing: 0.5
  - Network Restriction: 0.4
  - Enforcement multipliers:
    - HARD: ×1.2
    - SOFT: ×0.8

### 3. **Substitution Model** (Behavioral)
- **Purpose**: Predicts service substitution patterns
- **Method**: Pattern-based substitution rates by service category
- **Substitution Patterns**:
  - Imaging → Urgent Care, Office Visit (15% base rate)
  - Physical Therapy → Home Health, Self Care (20% base rate)
  - Specialty Care → Primary Care, Urgent Care (25% base rate)

### 4. **Provider Response Model** (Behavioral)
- **Purpose**: Predicts provider behavior distribution
- **Outputs**: 
  - Compliant % (follows policy)
  - Adaptive % (adapts behavior)
  - Resistant % (resists policy)
  - Circumvention % (finds workarounds)
- **Logic**: Based on friction level
  - Low friction (<0.3): 70% compliant, 20% adaptive, 8% resistant, 2% circumvention
  - Medium friction (0.3-0.6): 50% compliant, 30% adaptive, 15% resistant, 5% circumvention
  - High friction (>0.6): 35% compliant, 30% adaptive, 25% resistant, 10% circumvention

### 5. **Patient Response Model** (Behavioral)
- **Purpose**: Predicts patient behavior signals
- **Outputs**:
  - Defer Rate: % of patients who defer care
  - Substitute Rate: % who substitute services
  - ER Fallback Rate: % who use ER instead (adverse effect)
- **Formula**: 
  - `defer_rate = 0.10 × friction_level`
  - `substitute_rate = 0.15 × friction_level`
  - `er_fallback_rate = 0.05 × friction_level`

### 6. **Confidence Score Model** (Quality)
- **Purpose**: Estimates prediction reliability (0-100)
- **Factors**:
  - Elasticity data quality: -30 points if default, -15 if fair
  - Baseline metrics availability: -20 points if missing
  - Policy complexity: -10 points if >3 levers
- **Range**: 0-100 (higher = more confident)

## 📥 Inputs

### Required Inputs
1. **Policy Levers** (`policy_levers: List[Dict]`)
   - Lever type (PRIOR_AUTH, SITE_OF_CARE, etc.)
   - Parameters (codes, thresholds, etc.)
   - Enforcement strength (HARD, SOFT, PASSIVE)

2. **Policy Scope** (`policy_scope: Dict`, optional)
   - Line of business (COMMERCIAL, MA, MEDICAID)
   - Markets (geographic regions)
   - Network (IN, OUT, TIERED)

### Optional Inputs (Improve Accuracy)
3. **Baseline Metrics** (`baseline_metrics: Dict`, optional)
   - `utilization_per_1k`: Baseline utilization per 1,000 members
   - `cost_pmpm`: Baseline cost per member per month
   - `member_count`: Number of members
   - **Source**: Loaded from `BaselineAnalysisResult` table in database

4. **Elasticity Data** (`elasticity_data: Dict`, optional)
   - `overall_elasticity`: Overall elasticity coefficient
   - `service_elasticities`: Service-specific elasticities
   - `model_quality`: Quality rating (GOOD, FAIR, POOR)
   - **Source**: Loaded from elasticity models in database (if available)

## 📤 Outputs

### Primary Metrics (`PredictedImpactMetrics`)
1. **Utilization Change**
   - `utilization_change_pct`: Percentage change in utilization
   - `utilization_change_per_1k`: Absolute change per 1,000 members
   - **Formula**: `baseline_utilization × (utilization_change_pct / 100)`

2. **Cost Change**
   - `cost_change_pct`: Percentage change in cost
   - `cost_change_pmpm`: Change in cost per member per month ($)
   - `cost_change_total`: Total annual cost change ($)
   - **Formula**: 
     - `cost_change_pct = utilization_change_pct × 0.9` (selection effect)
     - `cost_change_pmpm = baseline_cost_pmpm × (cost_change_pct / 100)`
     - `cost_change_total = cost_change_pmpm × member_count × 12`

3. **Confidence Metrics**
   - `confidence_score`: Prediction confidence (0-100)
   - `prediction_method`: Method used (ELASTICITY_MODEL or DEFAULT_MODEL)

### Behavioral Predictions

4. **Substitution Effects** (`PredictedSubstitutionEffect[]`)
   - `service_category`: Affected service
   - `predicted_substitution_rate`: Rate of substitution (0-1)
   - `predicted_substitute_services`: List of substitute services
   - `confidence_score`: Confidence in substitution prediction

5. **Provider Response** (`PredictedProviderResponse`)
   - `compliant_pct`: % providers predicted to comply
   - `adaptive_pct`: % predicted to adapt
   - `resistant_pct`: % predicted to resist
   - `circumvention_pct`: % predicted to circumvent
   - `confidence_score`: Confidence in provider response prediction

6. **Patient Response** (`PredictedPatientResponse`)
   - `defer_rate`: % patients predicted to defer care
   - `substitute_rate`: % predicted to substitute services
   - `er_fallback_rate`: % predicted to use ER (adverse effect)
   - `confidence_score`: Confidence in patient response prediction

### Metadata
7. **Model Versions** (`model_versions: Dict`)
   - `elasticity`: Version of elasticity model
   - `behavioral`: Version of behavioral model
   - `provider_response`: Version of provider response model
   - `patient_response`: Version of patient response model

8. **Warnings & Limitations** (`warnings: List[str]`, `limitations: List[str]`)
   - Data quality warnings
   - Model limitations
   - Prediction uncertainty indicators

## 🔄 Calculation Flow

```
1. Extract Affected Services
   └─> From policy_levers (IMAGING, PHYSICAL_THERAPY, etc.)

2. Estimate Friction Level
   └─> Based on lever types and enforcement (0.0-1.0)

3. Get Elasticity Data
   ├─> Try: Load from database (elasticity models)
   └─> Fallback: Use default elasticity by service category

4. Predict Utilization Change
   └─> utilization_change_pct = friction_level × elasticity × 100

5. Predict Cost Change
   └─> cost_change_pct = utilization_change_pct × 0.9

6. Calculate Absolute Changes
   ├─> utilization_change_per_1k = baseline × (utilization_change_pct / 100)
   ├─> cost_change_pmpm = baseline_cost × (cost_change_pct / 100)
   └─> cost_change_total = cost_change_pmpm × members × 12

7. Predict Behavioral Effects
   ├─> Substitution effects (by service category)
   ├─> Provider response distribution
   └─> Patient response signals

8. Calculate Confidence Score
   └─> Based on data quality, baseline availability, complexity

9. Return PredictedImpactResult
   └─> All metrics, behavioral predictions, warnings, limitations
```

## 📐 Key Formulas

### Utilization Change
```
utilization_change_pct = friction_level × elasticity_coefficient × 100
utilization_change_per_1k = baseline_utilization × (utilization_change_pct / 100)
```

### Cost Change
```
cost_change_pct = utilization_change_pct × 0.9  # Selection effect
cost_change_pmpm = baseline_cost_pmpm × (cost_change_pct / 100)
cost_change_total = cost_change_pmpm × member_count × 12  # Annual
```

### Friction Level
```
friction = max(lever_friction × enforcement_multiplier) for all levers
lever_friction = {
    PRIOR_AUTH: 0.6,
    CLINICAL_CRITERIA: 0.5,
    SITE_OF_CARE: 0.4,
    QUANTITY_LIMIT: 0.3,
    COST_SHARING: 0.5,
    ...
}
enforcement_multiplier = {
    HARD: 1.2,
    SOFT: 0.8,
    PASSIVE: 1.0
}
```

### Confidence Score
```
confidence = 100.0
if not elasticity_data or quality == "POOR": confidence -= 30
elif quality == "FAIR": confidence -= 15
if not baseline_metrics: confidence -= 20
if len(policy_levers) > 3: confidence -= 10
confidence = max(0.0, min(100.0, confidence))
```

## 🎯 Example Calculation

### Input
- **Policy**: Prior Authorization for MRI
- **Lever**: PRIOR_AUTH, HARD enforcement
- **Baseline**: utilization_per_1k = 50, cost_pmpm = $200, members = 10,000
- **Elasticity**: -0.35 (default for IMAGING)

### Calculation
1. **Friction Level**: 0.6 (PRIOR_AUTH) × 1.2 (HARD) = 0.72
2. **Utilization Change**: 0.72 × (-0.35) × 100 = -25.2%
3. **Cost Change**: -25.2% × 0.9 = -22.68%
4. **Absolute Changes**:
   - utilization_change_per_1k = 50 × (-25.2 / 100) = -12.6
   - cost_change_pmpm = $200 × (-22.68 / 100) = -$45.36
   - cost_change_total = -$45.36 × 10,000 × 12 = -$5,443,200/year

### Output
- Utilization: -25.2% (12.6 fewer per 1k)
- Cost: -22.68% ($45.36 PMPM, $5.4M annual savings)
- Confidence: 70% (using default elasticity, baseline available)

## 🔍 Model Quality & Limitations

### Current Implementation (MVP)
- **Simplified Models**: Uses rule-based heuristics, not ML models
- **Default Elasticity**: Falls back to defaults if no historical data
- **Confidence**: Moderate (60-80%) for most predictions

### Future Enhancements
1. **ML-Based Elasticity**: Train on historical policy impacts
2. **Provider Segmentation**: Use provider archetypes for compliance prediction
3. **Patient Segmentation**: Use patient risk segments for response prediction
4. **Time-Series Models**: Account for seasonal patterns and trends
5. **Monte Carlo Simulation**: Provide confidence intervals, not just point estimates

## 📊 Data Sources

### Database Tables Used
1. **BaselineAnalysisResult**: Baseline metrics (utilization, cost, member count)
2. **Elasticity Models**: Historical elasticity coefficients (if available)
3. **Policy**: Policy levers, scope, enforcement
4. **Historical Impact Analyses**: For elasticity model training (future)

### Storage
- **Predicted Impact**: Stored in `Policy.policy_metadata_json['predicted_impact']`
- **Format**: JSONB in PostgreSQL
- **Access**: Via policy API endpoints

## ✅ Validation

- ✅ Uses database for baseline metrics
- ✅ Stores results in database
- ✅ No file dependencies
- ✅ 35/45 policies have predicted impact generated

---

*Documentation Generated: February 6, 2026*
*Model Version: 1.0 (MVP)*
*Location: `packages/common/src/uepi_common/analytics/predicted_impact.py`*

