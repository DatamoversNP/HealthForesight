# Complete Policy Configuration Implementation

## Summary

I've created a comprehensive policy seeding script that defines complete policies with all 6 workflow levels, including both standalone (single lever) and composite (multiple levers) policies.

## Files Created

### 1. `scripts/dev/seed_complete_policies.py`

A comprehensive script that creates complete policy configurations with:

- **4 Standalone Policies** (single lever each):
  1. Outpatient MRI Prior Authorization (PRIOR_AUTH)
  2. Physical Therapy Visit Limit (DURATION_FREQUENCY_LIMIT)
  3. Urgent Care Cost Sharing Policy (COST_SHARING)
  4. Step Therapy for High-Cost Biologic (STEP_THERAPY)

- **4 Composite Policies** (multiple levers each):
  1. Advanced Imaging Utilization Management Policy (3 levers: PRIOR_AUTH + SITE_OF_CARE + CLINICAL_CRITERIA)
  2. Specialty Drug Utilization Policy (4 levers: STEP_THERAPY + PRIOR_AUTH + QUANTITY_LIMIT + CLINICAL_CRITERIA)
  3. Outpatient Infusion Optimization Policy (3 levers: SITE_OF_CARE + COST_SHARING + PRIOR_AUTH)
  4. High-Cost Provider Control Policy (3 levers: PRIOR_AUTH + NETWORK_RESTRICTION + PAYMENT_POLICY)

## All 6 Workflow Levels Defined

Each policy includes:

1. ✅ **Basic Info**: Policy name, type, owner, description, status
2. ✅ **Scope**: LOB, markets, network restrictions
3. ✅ **Levers**: Policy levers with complete parameters
4. ✅ **Conditions**: Apply_when rules (when the policy applies)
5. ✅ **Exceptions**: Global exceptions (when the policy does NOT apply)
6. ✅ **Review & Save**: Complete metadata structure stored in `policy_metadata_json`

## Policy Metadata Structure

Each policy's metadata includes:

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
        "enforcement": "HARD",
        "site_of_care": "OUTPATIENT"
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

## How to Use

### Option 1: Run the Script Directly

```bash
# Make sure you're in the project root and have the environment set up
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"

# Activate your Python environment (if using virtualenv/conda)
# source venv/bin/activate  # or conda activate uepi

# Run the script to seed complete policies
python3 scripts/dev/seed_complete_policies.py

# Or clear existing policies first and seed fresh
python3 scripts/dev/seed_complete_policies.py --clear

# Specify a different tenant ID
python3 scripts/dev/seed_complete_policies.py --tenant-id 00000000-0000-0000-0000-000000000002
```

### Option 2: Use via API (Recommended for Production)

The script logic can be integrated into an API endpoint. You can also use the existing `/policies/complete-configurations` endpoint, but the seed script provides more comprehensive examples.

### Option 3: Use UI Button

After running the seed script, you can use the "Complete Configurations (All)" button in the UI, though the seed script provides more comprehensive policy definitions.

## What Happens When You Run It

1. The script connects to the database
2. Optionally clears existing policies (if `--clear` flag is used)
3. Creates/updates 8 policies (4 standalone + 4 composite)
4. Each policy gets:
   - Complete metadata with all 6 workflow levels
   - Policy version with effective dates
   - Policy code sets (CPT/HCPCS codes) linked to the version
5. All policies are ready for:
   - Predicted impact generation (Stage 3.5)
   - Impact analysis (Stage 4)
   - What-if scenarios

## Key Design Decisions

1. **Composite Policies Use Primary Policy Type**: Composite policies use the primary lever type as the `policy_type` field (e.g., `PRIOR_AUTH` for Advanced Imaging UM Policy), not `COMPOSITE`.

2. **Multiple Levers in One Policy**: The `policy_levers` array can contain multiple levers, each with its own parameters.

3. **Global Conditions and Exceptions**: Conditions and exceptions are defined at the policy level and apply to all levers (unless overridden at lever level in future enhancements).

4. **Code Sets Linked to Versions**: Policy codes are stored in `PolicyCodeSet` table linked to `PolicyVersion`, not directly to the policy.

## Next Steps

After seeding the policies:

1. **Generate Predicted Impact** (Stage 3.5):
   - Use the UI button "Generate Predicted Impact (All)"
   - Or API: `POST /api/v1/policies/generate-predicted-impact`

2. **Generate Synthetic Data** (Stage 4):
   - Use `scripts/generate_post_policy_synthetic_data.py` to generate post-policy observed data

3. **Run Impact Analysis** (Stage 4):
   - Create impact analyses to compare baseline, predicted, and observed impact

## Policy Examples Included

### Standalone Policies

1. **Outpatient MRI Prior Authorization**
   - Single PRIOR_AUTH lever
   - Codes: 72148, 72149, 72158
   - Scope: Commercial, NYC/DFW, In-Network
   - Exceptions: ER, Urgent, Pediatric

2. **Physical Therapy Visit Limit**
   - Single DURATION_FREQUENCY_LIMIT lever
   - Max 20 visits per year
   - Scope: Commercial/Medicaid, All markets
   - Exceptions: Post-surgical, Medical necessity

3. **Urgent Care Cost Sharing**
   - Single COST_SHARING lever
   - Copay increase: $40 → $75
   - Scope: Commercial, All markets, In-Network
   - Exceptions: ER visits

4. **Step Therapy for High-Cost Biologic**
   - Single STEP_THERAPY lever
   - Step sequence with duration requirements
   - Scope: Commercial/MA, All markets
   - Exceptions: Contraindications, Failure documentation

### Composite Policies

1. **Advanced Imaging Utilization Management Policy**
   - 3 levers: PRIOR_AUTH + SITE_OF_CARE + CLINICAL_CRITERIA
   - Interaction effects: PA + SOC + Criteria work together
   - Scope: Commercial, NYC/BOS

2. **Specialty Drug Utilization Policy**
   - 4 levers: STEP_THERAPY + PRIOR_AUTH + QUANTITY_LIMIT + CLINICAL_CRITERIA
   - Comprehensive drug control
   - Scope: Commercial/MA, All markets

3. **Outpatient Infusion Optimization Policy**
   - 3 levers: SITE_OF_CARE + COST_SHARING + PRIOR_AUTH
   - Site + cost + authorization interactions
   - Scope: Commercial/MA, All markets

4. **High-Cost Provider Control Policy**
   - 3 levers: PRIOR_AUTH + NETWORK_RESTRICTION + PAYMENT_POLICY
   - Targets high-cost providers specifically
   - Scope: Commercial, NYC/DFW, Tier 2 network

## Important Notes

- All policies are production-ready examples
- Policies follow real-world payer policy design patterns
- Composite policies demonstrate interaction effects
- All 6 workflow levels are complete for every policy
- Policies are ready for predicted impact generation
- Policies are ready for Stage 4 impact analysis
