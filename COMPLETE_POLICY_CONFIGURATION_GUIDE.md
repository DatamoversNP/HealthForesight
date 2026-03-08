# Complete Policy Configuration Guide

## Overview

This guide explains how to create complete policy configurations with all 6 workflow levels as defined in the Policy Workflow specification.

## Policy Workflow Levels (Authoritative)

Every policy type must be defined at all 6 wizard steps:

1. **Basic Info** – classification & intent
2. **Scope** – where/who it applies
3. **Levers** – what is being controlled
4. **Conditions** – when it applies
5. **Exceptions** – when it does NOT apply
6. **Review & Save** – human-readable summary + machine schema

If a policy cannot be defined at all 6 levels, it is not a valid policy type.

## Policy Types: Standalone vs Composite

### Standalone Policies (Single Lever)

A standalone policy contains exactly one policy lever. Examples:

1. **Outpatient MRI Prior Authorization**
   - Single lever: PRIOR_AUTH
   - Clean ownership by UM
   - Frequently changed independently

2. **Physical Therapy Visit Limit**
   - Single lever: DURATION_FREQUENCY_LIMIT
   - Benefit design driven
   - Often negotiated annually

3. **Urgent Care Cost Sharing**
   - Single lever: COST_SHARING
   - Financial lever only
   - Owned by benefits/actuarial

### Composite Policies (Multiple Levers)

A composite policy contains multiple policy levers that work together. Examples:

1. **Advanced Imaging Utilization Management Policy**
   - Lever 1: PRIOR_AUTH
   - Lever 2: SITE_OF_CARE
   - Lever 3: CLINICAL_CRITERIA
   - Interaction effects matter

2. **Specialty Drug Utilization Policy**
   - Lever 1: STEP_THERAPY
   - Lever 2: PRIOR_AUTH
   - Lever 3: QUANTITY_LIMIT
   - Lever 4: CLINICAL_CRITERIA

3. **Outpatient Infusion Optimization Policy**
   - Lever 1: SITE_OF_CARE
   - Lever 2: COST_SHARING
   - Lever 3: PRIOR_AUTH
   - Site + cost + authorization all interact

## Using the Seed Script

The `scripts/dev/seed_complete_policies.py` script creates complete policies with all 6 workflow levels defined.

### Running the Script

```bash
# Seed complete policies (keeps existing policies, updates if name matches)
python3 scripts/dev/seed_complete_policies.py

# Clear existing policies and seed fresh
python3 scripts/dev/seed_complete_policies.py --clear

# Specify tenant ID
python3 scripts/dev/seed_complete_policies.py --tenant-id 00000000-0000-0000-0000-000000000002
```

### What the Script Creates

The script creates:

- **4 Standalone Policies** (single lever each):
  1. Outpatient MRI Prior Authorization
  2. Physical Therapy Visit Limit
  3. Urgent Care Cost Sharing Policy
  4. Step Therapy for High-Cost Biologic

- **4 Composite Policies** (multiple levers each):
  1. Advanced Imaging Utilization Management Policy (3 levers)
  2. Specialty Drug Utilization Policy (4 levers)
  3. Outpatient Infusion Optimization Policy (3 levers)
  4. High-Cost Provider Control Policy (3 levers)

All policies include:
- ✅ Complete scope (LOB, markets, network)
- ✅ Effective period (start date)
- ✅ Policy levers (with parameters)
- ✅ Conditions (apply_when rules)
- ✅ Exceptions (global_exceptions)
- ✅ Enforcement configuration
- ✅ Policy code sets (linked to versions)

## Policy Metadata Structure

Each policy's `policy_metadata_json` contains:

```json
{
  "scope": {
    "lob": ["COMMERCIAL"],
    "markets": ["NYC", "DFW"],
    "network": ["IN"]
  },
  "effective_period": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": null
  },
  "policy_levers": [
    {
      "lever_type": "PRIOR_AUTH",
      "parameters": {
        "codes": ["72148", "72149"],
        "code_type": "CPT",
        "enforcement": "HARD"
      }
    }
  ],
  "apply_when": [
    {
      "field": "place_of_service",
      "operator": "IN",
      "values": ["11", "22"]
    }
  ],
  "global_exceptions": [
    {
      "type": "ER",
      "description": "Emergency room services excluded"
    }
  ],
  "enforcement": {
    "mechanism": "HARD",
    "touchpoint": ["PA_WORKFLOW"],
    "override_allowed": false
  }
}
```

## Next Steps

After seeding complete policies:

1. **Generate Predicted Impact** (Stage 3.5)
   - Use the "Generate Predicted Impact (All)" button in the UI
   - Or use the API endpoint: `POST /api/v1/policies/generate-predicted-impact`

2. **Generate Synthetic Data** (Stage 4)
   - Use `scripts/generate_post_policy_synthetic_data.py` to generate post-policy observed data

3. **Run Impact Analysis** (Stage 4)
   - Create impact analyses comparing baseline, predicted, and observed impact

## Important Notes

- Policies are defined at the policy container level
- Multiple levers can exist within a single policy (composite policies)
- Each lever can have its own conditions and exceptions
- Global exceptions apply to all levers in the policy
- Policy types are lever types, not standalone policies by default
- The system supports both single-lever and multi-lever (composite) policies
