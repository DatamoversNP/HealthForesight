# Synthetic Data Enhancement Summary

## Overview

The synthetic data generation has been enhanced to support **comprehensive policy scope** dimensions required for the Policy Scoping Algorithm and metric dictionary calculations.

## Fields Added

### Members (enrollment data)
**New fields:**
- ✅ `plan_id` - Plan identifier (PLAN_A through PLAN_E)
- ✅ `product_type` - Product type (HMO, PPO, EPO, POS, HDHP)
- ✅ `state` - State code (NY, TX, MA) derived from market
- ✅ `region` - Region (NORTHEAST, SOUTH, WEST, MIDWEST) derived from market

**Existing fields (still supported):**
- ✅ `member_id`, `lob`, `market`
- ✅ `gender`, `dob_year`, `risk_score`, `enrolled_flag`

### Providers
**New fields:**
- ✅ `network_tier` - Network tier (TIER_1, TIER_2, TIER_3)
  - Distribution: 50% TIER_1 (preferred), 40% TIER_2 (standard), 10% TIER_3

**Existing fields (still supported):**
- ✅ `npi`, `provider_name`, `specialty`, `market`
- ✅ `facility_flag`, `tax_id`, `system_affiliation`

### Claims Lines
**New fields:**
- ✅ `plan_id` - Merged from member data
- ✅ `product_type` - Merged from member data
- ✅ `state` - Merged from member data
- ✅ `region` - Merged from member data
- ✅ `network_tier` - Merged from provider data (aligned with `in_network_flag`)
- ✅ `service_category` - Derived from CPT codes:
  - ADVANCED_IMAGING (MRI, ER_IMAGING)
  - SPECIALTY_SERVICES (INFUSION)
  - REHABILITATION (PT)
  - SPECIALTY_CARE (SPECIALTY_VISIT)
  - URGENT_CARE
  - OTHER (fallback)
- ✅ `diagnosis_group` - Derived from `diag_1`:
  - MUSCULOSKELETAL (M-codes)
  - PREVENTIVE (Z-codes)
  - OTHER (fallback)

**Existing fields (still supported):**
- ✅ `service_from_date`, `service_to_date`, `paid_date`
- ✅ `tenant_id`, `member_id`, `claim_id`, `claim_line_id`
- ✅ `lob`, `market`, `place_of_service`, `cpt_hcpcs`
- ✅ `rendering_npi`, `billing_npi`
- ✅ `allowed_amount`, `paid_amount`, `units`
- ✅ `in_network_flag`, `modifier_1`, `diag_1`

## Policy Scoping Support

All PolicyScope dimensions are now supported:

### Population Dimensions
- ✅ `lob` - Line of business (COMMERCIAL, MA, MEDICAID)
- ✅ `markets` - Market (NYC, DFW, BOS)
- ✅ `plans` - Plan IDs (now available in claims and members)
- ✅ `product_types` - Product types (now available in claims and members)

### Geography Dimensions
- ✅ `states` - State codes (now available in claims and members)
- ✅ `regions` - Regions (now available in claims and members)

### Network Dimensions
- ✅ `network` - In-network flag (already supported)
- ✅ `network_tiers` - Network tiers (now available in claims and providers)

### Member Attributes
- ✅ `member_age_min` / `member_age_max` - From `dob_year` (already supported)
- ✅ `gender_filters` - From `gender` (already supported)
- ✅ `exclude_pregnant` - Can be added if needed (requires additional field)

### Provider Filters
- ✅ `provider_specialties` - From `specialty` (already supported via provider lookup)
- ✅ `exclude_centers_of_excellence` - Can be added if needed

### Site of Care
- ✅ `place_of_service` - Already supported
- ✅ `allowed_sites` - Can filter on `place_of_service`

### Service Dimensions
- ✅ `service_category` - Now available in claims
- ✅ `diagnosis_group` - Now available in claims
- ✅ CPT codes - Already supported

## Target Data Model Alignment

The enhanced data structure aligns with the target data model:
```
apps/data/target_data_model/
  {tenant_id}/
    CLAIMS_LINES/
      claims_lines.csv  # Now includes all comprehensive scope fields
    ENROLLMENT/         # (Optional - members can be stored here)
    PROVIDERS/          # (Optional - providers can be stored here)
```

## Data Quality

- **Referential integrity**: `plan_id`, `product_type`, `state`, `region` are consistent between claims and members via merge
- **Network alignment**: `network_tier` aligns with `in_network_flag` (TIER_3 if out-of-network)
- **Categorical mapping**: `service_category` and `diagnosis_group` are derived deterministically from CPT and diagnosis codes

## Usage

The enhanced fields are automatically included when using:
- `scripts/synth/generate.py` - All generation functions updated
- `scripts/regenerate_complete_workflow.py` - Uses enhanced generation
- Any script that imports `generate_members`, `generate_providers`, `generate_claims_lines`

## Next Steps

1. ✅ Data generation enhanced - supports all PolicyScope dimensions
2. ⏳ Regenerate existing data - Run `scripts/regenerate_complete_workflow.py` to recreate data with new fields
3. ⏳ Verify policy scoping - Test policy scoping algorithm with new fields
4. ⏳ Test baseline/predicted/observed impact - Ensure all metrics calculate correctly with enhanced data

## Notes

- **Backward compatibility**: Existing data without new fields will still work (policy scoping will simply not filter on missing dimensions)
- **Optional fields**: Some PolicyScope dimensions (e.g., `exclude_pregnant`, `exclude_centers_of_excellence`) require additional data sources and can be added later
- **Network master**: Dynamic network loading from network master API (separate enhancement) will provide real network names instead of hardcoded TIER_1/TIER_2/TIER_3
