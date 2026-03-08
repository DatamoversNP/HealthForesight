# Metric Coverage Analysis

## Current Status vs Required Metric Dictionary

### ✅ DEFINED in metric_dictionary.py

**Denominators (D1-D3):**
- ✅ D1: `member_months` - Defined
- ✅ D2: `unique_members` - Defined
- ✅ D3: `policy_eligible_member_months` - Defined

**Primary Outcome Metrics (M1-M7):**
- ✅ M1: `util_rate_total_per_1000_mm` - Defined
- ✅ M2: `util_rate_target_per_1000_mm` - Defined
- ✅ M3: `allowed_pmpm_total` - Defined
- ✅ M4: `allowed_pmpm_target` - Defined
- ✅ M5: `paid_pmpm_total` - Defined
- ⚠️ M6: `member_cost_share_pmpm` - **NOT DEFINED** (marked optional)
- ✅ M7: `allowed_total_annualized` - Defined

**Mix Metrics (M8-M13):**
- ✅ M8: `soc_share_target_ER` - Defined (example)
- ✅ M9: `soc_share_target_HOPD` - Defined (example)
- ✅ M10: `soc_share_target_ASC` - Defined (example)
- ⚠️ M9: `service_share_target_{code_or_group}` - **NOT DEFINED** (dynamic pattern needed)
- ⚠️ M10: `provider_hhi_target` - **NOT DEFINED**
- ✅ M11: `top10_provider_share_target` - Defined
- ✅ M12: `inn_share_target` - Defined
- ✅ M13: `oon_leakage_rate_target_per_1000_mm` - Defined

**Substitution/Spillover Metrics (M14-M16):**
- ⚠️ M14: `substitution_uplift_{candidate}_per_1000_mm` - **NOT DEFINED**
- ⚠️ M15: `soc_share_delta_target_{soc_category}` - **NOT DEFINED**
- ⚠️ M16: `deferral_index_target` - **NOT DEFINED**

**Behavioral Attribution Metrics (M17-M19):**
- ⚠️ M17: `provider_archetype_share_{type}` - **NOT DEFINED**
- ⚠️ M18: `provider_ordering_intensity_target_per_1000_mm` - **NOT DEFINED**
- ⚠️ M19: `patient_response_share_{segment}_{response}` - **NOT DEFINED**

**Prediction vs Observed & Learning Metrics (M20-M22):**
- ⚠️ M20: `prediction_error_util_pp` - **NOT DEFINED** (computed in observation_enhancement but not in dictionary)
- ⚠️ M21: `prediction_error_cost_pmpm` - **NOT DEFINED** (computed in observation_enhancement but not in dictionary)
- ⚠️ M22: `confidence_score` - **NOT DEFINED** in metric dictionary (but exists in predicted impact models)

## ⚠️ MISSING Metrics That Should Be Added

1. **M6: Member Cost Share PMPM** (optional but should be available)
2. **M9: Service Share Target** (dynamic - need pattern support)
3. **M10: Provider HHI Target** (concentration index)
4. **M14-M16: Substitution/Spillover Metrics** (computed in substitution detection but not in metric dictionary)
5. **M17-M19: Behavioral Attribution Metrics** (computed in provider segmentation but not in metric dictionary)
6. **M20-M22: Learning Metrics** (computed in observations but not in metric dictionary)

## 📊 COMPUTATION Status

### Baseline Metrics Computation
- ✅ Computes: member_months, unique_members, util_rate_total_per_1000_mm, allowed_pmpm_total
- ✅ Computes policy-scoped: util_rate_target_per_1000_mm, allowed_pmpm_target
- ⚠️ Partially computes mix metrics (soc_share for specific categories, inn_share)
- ❌ Does NOT compute: provider_hhi, service_share patterns, oon_leakage_rate, annualized cost

### Predicted Impact
- ✅ Computes: utilization_change_per_1k, cost_change_pmpm, effect_size, confidence_score
- ⚠️ Substitution effects exist but not as formal metrics
- ❌ Does NOT compute: soc_share_delta, deferral_index, prediction errors as metrics

### Observed Impact (Observations)
- ✅ Extracts: utilization_per_1k, cost_pmpm, effect_size
- ✅ Computes comparison metrics: baseline vs observed, predicted vs observed
- ⚠️ Prediction errors computed but not stored as dictionary metrics
- ❌ Does NOT compute: substitution_uplift, soc_share_delta, behavioral attribution metrics

## 🎯 MINIMAL CARD-READY SET (A8)

Required for cards:
- ✅ `util_rate_target_per_1000_mm` - Computed
- ✅ `allowed_pmpm_target` - Computed
- ⚠️ `allowed_total_annualized` - Defined but **NOT COMPUTED** in baseline
- ⚠️ `soc_share_target_{key categories}` - Partially computed (ER, HOPD, ASC defined, but not all categories)
- ✅ `inn_share_target` - Computed
- ⚠️ `oon_leakage_rate_target_per_1000_mm` - Defined but **NOT COMPUTED** in baseline
- ✅ `confidence_score` - Computed (in predicted impact, not baseline)

## 🔧 RECOMMENDATIONS

1. **Add missing metric definitions** to metric_dictionary.py:
   - M6: member_cost_share_pmpm
   - M10: provider_hhi_target
   - M14-M16: Substitution/spillover metrics
   - M17-M19: Behavioral attribution metrics
   - M20-M22: Learning metrics

2. **Enhance baseline computation** to compute:
   - allowed_total_annualized (from allowed_pmpm_target * member_months / period_months * 12)
   - oon_leakage_rate_target_per_1000_mm (from claims data filtering in_network=false)
   - provider_hhi_target (from provider concentration in target claims)
   - More soc_share categories dynamically

3. **Enhance observed impact** to compute and store:
   - substitution_uplift metrics from substitution detection
   - soc_share_delta metrics (post - baseline)
   - deferral_index from timing analysis

4. **Store prediction errors as metrics** (not just in comparisons):
   - prediction_error_util_pp
   - prediction_error_cost_pmpm
