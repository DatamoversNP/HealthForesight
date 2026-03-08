# Policy Scoping Architecture - First-Class Concept

## Core Principle

**In real payer operations, policies are ALWAYS selectively scoped, not universal.**

HealthForesight treats policy scope as a **first-class concept** that drives:
- Baseline computation (policy-scoped, not global)
- Predicted impact (only on scoped population)
- Observed impact (only on scoped population)
- Spillover detection (changes outside scope = leakage/substitution)

## Policy Scope Definition

Policy scope is defined through **multiple layers**:

### 1. PolicyScope (High-Level Population/Geography/Network Filters)

Located in: `policy.scope` or `policy.metadata.scope`

**Dimensions:**
- **Population**: `lob`, `markets`, `plans`, `product_types`
- **Geography**: `states`, `regions` (if markets isn't sufficient)
- **Network**: `network` (["IN"], ["OUT"], or None = all), `network_tiers`
- **Member Attributes**: `member_age_min/max`, `exclude_pregnant`, `gender_filters`
- **Provider Filters**: `exclude_centers_of_excellence`, `include_provider_types`, `provider_specialties`
- **Site of Care**: `exclude_er`, `exclude_hospital_op`, `allowed_sites`
- **Explicit "All"**: `applies_to_all` (for benefit design policies)

**Example:**
```json
{
  "lob": ["COMMERCIAL"],
  "markets": ["NYC", "DFW"],
  "network": ["IN"],  // In-network only
  "exclude_er": true,
  "member_age_min": 18,
  "applies_to_all": false
}
```

### 2. PolicyLever.targets (Service Codes)

Located in: `policy.logic.policy_levers[].targets`

Defines **which services/codes** are affected:
- `codes`: List of CPT/HCPCS codes
- `code_groups`: Pre-defined code groups
- `all_codes_in_category`: Apply to all codes in a category

**Example:**
```json
{
  "lever_type": "PRIOR_AUTH",
  "targets": {
    "code_type": "CPT",
    "codes": ["72141", "72142", "72146"]
  }
}
```

### 3. PolicyLever.apply_when (Conditions)

Located in: `policy.logic.policy_levers[].apply_when`

Defines **when** the policy applies (member attributes, clinical criteria):
- Age conditions
- Diagnosis conditions
- Prior therapy requirements
- Clinical criteria

**Example:**
```json
{
  "apply_when": [
    {
      "conditions": [
        {"field": "age", "operator": "GREATER_THAN_OR_EQUAL", "value": 18},
        {"field": "diagnosis", "operator": "IN", "value": ["M54.5", "M54.9"]}
      ],
      "operator": "AND"
    }
  ]
}
```

### 4. PolicyLever.exceptions (Carve-Outs)

Located in: `policy.logic.policy_levers[].exceptions`

Defines **when NOT to apply** (carve-outs):
- ER carve-out
- Oncology carve-out
- Pregnancy carve-out
- Specific provider/facility exclusions

**Example:**
```json
{
  "exceptions": [
    {"field": "place_of_service", "operator": "EQUALS", "value": "23", "description": "ER carve-out"},
    {"field": "provider_id", "operator": "IN", "value": ["COE_001", "COE_002"], "description": "COE exclusion"}
  ]
}
```

### 5. PolicyLever.config (Site/Provider Restrictions)

Located in: `policy.logic.policy_levers[].config`

Lever-specific restrictions:
- **SiteOfCareLeverConfig**: `allowed_sites`, `disallowed_sites`
- **NetworkRestrictionLeverConfig**: `allowed_network`, `tier_restrictions`
- Other lever-specific configs

**Example:**
```json
{
  "config": {
    "allowed_sites": ["FREESTANDING", "ASC"],
    "disallowed_sites": ["HOSPITAL_OP", "ER"],
    "redirect_to": "FREESTANDING"
  }
}
```

## How Scoping Works in Practice

### Policy Scoping Algorithm

The `compute_comprehensive_policy_scope()` function:
1. Applies PolicyScope filters to enrollment → **eligible_member_months**
2. Applies PolicyScope + PolicyLever.targets + conditions + exceptions to claims → **final_target_claim_lines**
3. Identifies **exposed members** (had target utilization pre-policy)
4. Identifies **impacted providers** (high-volume target drivers)
5. Constructs **control pool** candidates for DiD

### Baseline Computation

**Baseline is ALWAYS policy-scoped:**
- Uses `eligible_member_months` as denominator (not global member-months)
- Uses `final_target_claim_lines` for utilization/cost metrics (not all claims)
- Computes mix baselines (site of care, provider, network) on scoped population only

**Metrics computed:**
- `util_rate_target_per_1000_mm`: Target utilization per 1K policy-eligible member-months
- `allowed_pmpm_target`: Target allowed cost PMPM for scoped population
- `policy_eligible_member_months`: Denominator for all policy-scoped metrics

### Predicted Impact

**Predicted impact is ALWAYS on scoped population:**
- Uses policy-scoped baseline as reference
- Elasticity models applied to scoped services only
- Confidence scores account for scope specificity

### Observed Impact

**Observed impact is ALWAYS on scoped population:**
- Compares observed metrics to policy-scoped baseline (not global)
- Detects spillover (changes outside scope) separately
- Substitution/leakage detected relative to scope boundaries

## Default Behavior

### If Scope is Not Provided

**Default PolicyScope:**
- `lob`: `None` (all LOBs)
- `markets`: `None` (all markets)
- `network`: `None` (all networks)
- `applies_to_all`: `False` (assume selective, even if not specified)

**BUT:** Policy must have `policy_levers` with `targets.codes` to define what services are affected.

**If no scope AND no lever targets:** Warning logged, global baseline used (not recommended).

### "All Population" Policies

For benefit design policies (annual maximums, cost-sharing changes):
- Set `applies_to_all: true` in PolicyScope
- Still compute scope explicitly (even if "all")
- This distinguishes from UM policies (which are always selective)

## UI/UX Implications

### Policy Creation

1. **Scope should be prominent** (not hidden in "advanced settings")
2. **Default to selective scoping** (don't default to "all")
3. **Show scope summary** before policy creation
4. **Validate scope completeness** (at minimum, need service targets)

### Baseline/Predicted/Observed Pages

1. **Always show scope** alongside metrics
2. **Make scope visible** in metric cards (e.g., "MRI utilization per 1K (Commercial, NYC, In-Network)")
3. **Distinguish scope changes** when comparing baselines
4. **Show spillover** separately from primary impact

## Implementation Files

- **PolicyScope Model**: `packages/common/src/uepi_common/models.py`
- **Comprehensive Scoping**: `apps/api/src/uepi_api/policy_scoping_enhanced.py`
- **Baseline Metrics**: `apps/api/src/uepi_api/baseline_metrics_computation.py`
- **Metric Dictionary**: `packages/common/src/uepi_common/metrics/metric_dictionary.py`

## Key Takeaways

1. ✅ **Scope is first-class** - not optional metadata
2. ✅ **Baseline is policy-scoped** - not global averages
3. ✅ **Predictions respect scope** - only compute on scoped population
4. ✅ **Observations respect scope** - compare to policy-scoped baseline
5. ✅ **Spillover is explicit** - changes outside scope are measured separately
