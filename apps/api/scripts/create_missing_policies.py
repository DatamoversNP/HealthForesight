#!/usr/bin/env python3
"""
Create missing policies based on the user's list of 32 policies.
Handle duplicates by updating existing policies with new names/variants.
"""
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_policies import create_policy, list_policies, update_policy
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# User's list of 32 policies (in order)
REQUIRED_POLICIES = [
    "Biologic Step Therapy for Rheumatoid Arthritis",
    "Infusion Site-of-Care Optimization",
    "Specialty Drug Utilization Policy",
    "Ambulatory Surgery Center Preference",
    "Durable Medical Equipment Quantity Limits",
    "Advanced Imaging Control Bundle",
    "Home Health Care Preference",
    "Occupational Therapy Annual Limit",
    "Urgent Care Copay Increase",
    "Preferred Generic Drug Tier",
    "Outpatient MRI Prior Authorization",
    "Oncology Immunotherapy Step Therapy",
    "Outpatient MRI Prior Authorization",  # Duplicate - will be renamed
    "Outpatient Infusion Optimization Policy",
    "Spine Surgery Prior Authorization",
    "Psychiatric Inpatient Prior Authorization",
    "Opioid Quantity Limit - Chronic Pain",
    "High-Cost Provider Control Policy",
    "Telehealth Cost Sharing Parity",
    "Cardiac Imaging Comprehensive Control",
    "Outpatient MRI Prior Authorization",  # Duplicate - will be renamed
    "GLP-1 Step Therapy for Type 2 Diabetes",
    "Advanced Imaging Utilization Management Policy",
    "Physical Therapy Visit Limit",
    "Urgent Care Cost Sharing",
    "MSK Imaging + Site-of-Care + Referral Integrity Program (Enterprise Composite)",
    "Network-Specific Prior Authorization with Provider Tiering",
    "Advanced Imaging Utilization Management - Multi-State Commercial (Complex)",
    "Cardiac CT Angiography Prior Authorization",
    "Seasonal Variation Policy with Time-Bound Rules",
    "Speech Therapy Visit Limit",
    "Outpatient MRI Prior Authorization - Commercial (Simple)",
]

# Policy type mappings based on names
POLICY_TYPE_MAP = {
    "Step Therapy": "STEP_THERAPY",
    "Site-of-Care": "SITE_OF_CARE",
    "Prior Authorization": "PRIOR_AUTH",
    "Cost Sharing": "COST_SHARING",
    "Quantity Limit": "QUANTITY_LIMIT",
    "Utilization": "UTILIZATION_MANAGEMENT",
    "Preference": "SITE_OF_CARE",
    "Control": "UTILIZATION_MANAGEMENT",
    "Composite": "COMPOSITE",
    "Tiering": "NETWORK_RESTRICTION",
    "Variation": "SEASONAL_POLICY",
}

def get_policy_type(name):
    """Determine policy type from name"""
    name_upper = name.upper()
    if "STEP THERAPY" in name_upper:
        return "STEP_THERAPY"
    elif "SITE-OF-CARE" in name_upper or "PREFERENCE" in name_upper:
        return "SITE_OF_CARE"
    elif "PRIOR AUTHORIZATION" in name_upper or "PA" in name_upper:
        return "PRIOR_AUTH"
    elif "COST SHARING" in name_upper or "COPAY" in name_upper:
        return "COST_SHARING"
    elif "QUANTITY LIMIT" in name_upper or "ANNUAL LIMIT" in name_upper or "VISIT LIMIT" in name_upper:
        return "QUANTITY_LIMIT"
    elif "COMPOSITE" in name_upper or "ENTERPRISE" in name_upper:
        return "COMPOSITE"
    elif "TIERING" in name_upper or "NETWORK" in name_upper:
        return "NETWORK_RESTRICTION"
    elif "UTILIZATION" in name_upper or "CONTROL" in name_upper:
        return "UTILIZATION_MANAGEMENT"
    elif "SEASONAL" in name_upper or "VARIATION" in name_upper:
        return "SEASONAL_POLICY"
    else:
        return "PRIOR_AUTH"  # Default

def create_policy_data(name, index):
    """Create policy data structure"""
    policy_type = get_policy_type(name)
    
    # Handle duplicate names by adding variants
    if name == "Outpatient MRI Prior Authorization":
        if index == 10:  # First occurrence
            variant_name = name
        elif index == 12:  # Second occurrence
            variant_name = "Outpatient MRI Prior Authorization - Standard"
        elif index == 20:  # Third occurrence
            variant_name = "Outpatient MRI Prior Authorization - Enhanced"
        else:
            variant_name = f"{name} - Variant {index}"
    else:
        variant_name = name
    
    return {
        'name': variant_name,
        'policy_type': policy_type,
        'description': f"Policy for {variant_name}",
        'status': 'ACTIVE',
        'scope': {
            'lob': ['COMMERCIAL', 'MA'],
            'markets': ['ALL'],
            'network': ['IN']
        },
        'effective_period': {
            'start_date': '2024-01-01',
            'end_date': None
        },
        'enforcement': {
            'mechanism': 'HARD',
            'touchpoint': ['PA_WORKFLOW'],
            'override_allowed': True
        },
        'policy_levers': [],
        'expected_behavioral_response': [],
        'analytics_expectations': {},
        'ui_hints': {},
    }

def main():
    """Create or update policies to match the required list"""
    print("=" * 80)
    print("Creating/Updating Policies to Match Required List")
    print("=" * 80)
    
    # Get existing policies
    existing_policies = list_policies(DEFAULT_TENANT_ID)
    existing_by_name = {p.get('name', ''): p for p in existing_policies if p and isinstance(p, dict)}
    
    print(f"\n📋 Found {len(existing_policies)} existing policies")
    print(f"📋 Need to create/update {len(REQUIRED_POLICIES)} policies")
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    # Track which names we've seen to handle duplicates
    seen_names = {}
    
    for index, required_name in enumerate(REQUIRED_POLICIES, 1):
        try:
            # Determine the actual name (handling duplicates)
            if required_name == "Outpatient MRI Prior Authorization":
                if index == 10:
                    actual_name = required_name
                elif index == 12:
                    actual_name = "Outpatient MRI Prior Authorization - Standard"
                elif index == 20:
                    actual_name = "Outpatient MRI Prior Authorization - Enhanced"
                else:
                    actual_name = f"{required_name} - Variant {index}"
            else:
                actual_name = required_name
            
            # Check if we've already processed this exact name
            if actual_name in seen_names:
                print(f"⏭️  Skipping duplicate: {actual_name} (already processed)")
                skipped_count += 1
                continue
            
            seen_names[actual_name] = True
            
            # Check if policy exists (by exact name or similar)
            existing_policy = None
            if actual_name in existing_by_name:
                existing_policy = existing_by_name[actual_name]
            else:
                # Try to find similar name (for updates)
                for existing_name, existing in existing_by_name.items():
                    if required_name.lower() in existing_name.lower() or existing_name.lower() in required_name.lower():
                        existing_policy = existing
                        break
            
            if existing_policy:
                # Update existing policy if name doesn't match exactly
                if existing_policy.get('name') != actual_name:
                    print(f"🔄 Updating policy: {existing_policy.get('name')} -> {actual_name}")
                    try:
                        policy_id = UUID(existing_policy.get('id'))
                        policy_data = create_policy_data(actual_name, index)
                        update_policy(policy_id, DEFAULT_TENANT_ID, policy_data)
                        updated_count += 1
                        print(f"   ✅ Updated: {actual_name}")
                    except Exception as e:
                        print(f"   ❌ Failed to update: {e}")
                        error_count += 1
                else:
                    print(f"✅ Already exists: {actual_name}")
                    skipped_count += 1
            else:
                # Create new policy
                print(f"📝 Creating policy {index}/{len(REQUIRED_POLICIES)}: {actual_name}")
                try:
                    policy_data = create_policy_data(actual_name, index)
                    created = create_policy(DEFAULT_TENANT_ID, policy_data)
                    if created:
                        created_count += 1
                        print(f"   ✅ Created: {actual_name}")
                    else:
                        error_count += 1
                        print(f"   ❌ Failed to create: {actual_name}")
                except Exception as e:
                    print(f"   ❌ Error creating {actual_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    error_count += 1
                    
        except Exception as e:
            print(f"❌ Error processing policy {index} ({required_name}): {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Complete: {created_count} created, {updated_count} updated, {skipped_count} skipped, {error_count} errors")
    
    # Verify final count
    final_policies = list_policies(DEFAULT_TENANT_ID)
    print(f"📊 Total policies in database: {len(final_policies)}")
    print("=" * 80)
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

