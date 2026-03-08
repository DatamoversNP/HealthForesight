"""
Seed Example Policies for Stage 2
Creates standalone and composite policy examples
"""
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import date, datetime

# Adjust PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../packages/common/src')))

from uepi_api.storage_policies import create_policy, list_policies
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_common.data_contracts.policy_logic import (
    PolicyLogic,
    PolicyLever,
    PolicyScope,
    LeverType,
)
from uepi_common.data_contracts.policy_metadata import LeverType as LeverTypeEnum


# Example 1: Standalone Policy - Outpatient MRI Prior Authorization
STANDALONE_POLICY_1 = {
    "policy_name": "Outpatient MRI Prior Authorization",
    "policy_description": "Requires prior authorization for outpatient MRI services to reduce inappropriate utilization",
    "policy_owner": "UM",
    "policy_category": "UTILIZATION",
    "scope": {
        "line_of_business": ["Commercial"],
        "markets": ["NY", "TX", "CA"],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "PRIOR_AUTH",
            "name": "MRI Prior Authorization",
            "parameters": {
                "codes": ["72148", "72149", "72158", "72159"],
                "enforcement": "HARD",
            },
            "enabled": True,
            "priority": 0,
        }
    ],
    "effective_start": "2025-01-01",
    "effective_end": None,
    "tags": ["MRI", "Prior Auth", "Outpatient"],
}

# Example 2: Standalone Policy - Physical Therapy Visit Limit
STANDALONE_POLICY_2 = {
    "policy_name": "Physical Therapy Visit Limit",
    "policy_description": "Limits physical therapy visits to 20 per year for commercial members",
    "policy_owner": "Benefits",
    "policy_category": "UTILIZATION",
    "scope": {
        "line_of_business": ["Commercial"],
        "markets": [],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "BENEFIT_LIMIT",
            "name": "PT Visit Limit",
            "parameters": {
                "max_visits": 20,
                "time_window": "YEAR",
            },
            "enabled": True,
            "priority": 0,
        }
    ],
    "effective_start": "2025-01-01",
    "effective_end": None,
    "tags": ["Physical Therapy", "Benefit Limit"],
}

# Example 3: Standalone Policy - Urgent Care Cost Sharing
STANDALONE_POLICY_3 = {
    "policy_name": "Urgent Care Cost Sharing",
    "policy_description": "Sets copay for urgent care visits",
    "policy_owner": "Benefits",
    "policy_category": "FINANCIAL",
    "scope": {
        "line_of_business": ["Commercial"],
        "markets": [],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "COST_SHARING",
            "name": "Urgent Care Copay",
            "parameters": {
                "copay": 75,
            },
            "enabled": True,
            "priority": 0,
        }
    ],
    "effective_start": "2025-01-01",
    "effective_end": None,
    "tags": ["Urgent Care", "Cost Sharing"],
}

# Example 4: Composite Policy - Advanced Imaging Utilization Management
COMPOSITE_POLICY_1 = {
    "policy_name": "Advanced Imaging Utilization Management Policy",
    "policy_description": "Comprehensive policy combining prior authorization, site of care restrictions, and clinical criteria for advanced imaging",
    "policy_owner": "UM + Strategy",
    "policy_category": "UTILIZATION",
    "scope": {
        "line_of_business": ["Commercial"],
        "markets": ["NY", "TX"],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "PRIOR_AUTH",
            "name": "MRI/CT Prior Authorization",
            "parameters": {
                "codes": ["72148", "72149", "72158", "72159", "70450", "70460"],
                "enforcement": "HARD",
            },
            "enabled": True,
            "priority": 0,
        },
        {
            "lever_type": "SITE_OF_CARE",
            "name": "Site of Care Restriction",
            "parameters": {
                "allowed_sites": ["FREESTANDING", "OFFICE"],
                "disallowed_sites": ["HOSPITAL_OP"],
            },
            "enabled": True,
            "priority": 1,
        },
        {
            "lever_type": "CLINICAL_CRITERIA",
            "name": "Clinical Criteria",
            "parameters": {
                "criteria_set": "INTERNAL_GUIDELINES",
                "strictness_level": "MEDIUM",
            },
            "enabled": True,
            "priority": 2,
        },
    ],
    "effective_start": "2025-04-01",
    "effective_end": None,
    "tags": ["Imaging", "Composite", "Prior Auth", "Site of Care"],
}

# Example 5: Composite Policy - Specialty Drug Utilization
COMPOSITE_POLICY_2 = {
    "policy_name": "Specialty Drug Utilization Policy",
    "policy_description": "Comprehensive specialty drug management with step therapy, prior auth, quantity limits, and clinical criteria",
    "policy_owner": "Pharmacy",
    "policy_category": "UTILIZATION",
    "scope": {
        "line_of_business": ["Commercial", "MA"],
        "markets": [],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "STEP_THERAPY",
            "name": "Step Therapy Sequence",
            "parameters": {
                "step_sequence": ["GENERIC", "PREFERRED_BRAND", "NON_PREFERRED_BRAND"],
            },
            "enabled": True,
            "priority": 0,
        },
        {
            "lever_type": "PRIOR_AUTH",
            "name": "Specialty Drug PA",
            "parameters": {
                "codes": ["J9000", "J9001"],
                "enforcement": "HARD",
            },
            "enabled": True,
            "priority": 1,
        },
        {
            "lever_type": "QUANTITY_LIMIT",
            "name": "Quantity Limits",
            "parameters": {
                "units_per_month": 30,
            },
            "enabled": True,
            "priority": 2,
        },
        {
            "lever_type": "CLINICAL_CRITERIA",
            "name": "Clinical Criteria",
            "parameters": {
                "criteria_set": "NCCN_GUIDELINES",
                "strictness_level": "STRICT",
            },
            "enabled": True,
            "priority": 3,
        },
    ],
    "effective_start": "2025-01-01",
    "effective_end": None,
    "tags": ["Specialty Drug", "Composite", "Step Therapy"],
}

# Example 6: Composite Policy - Outpatient Infusion Optimization
COMPOSITE_POLICY_3 = {
    "policy_name": "Outpatient Infusion Optimization Policy",
    "policy_description": "Optimizes outpatient infusion through site of care preferences, cost sharing, and prior authorization",
    "policy_owner": "Medical Management",
    "policy_category": "UTILIZATION",
    "scope": {
        "line_of_business": ["Commercial"],
        "markets": ["NY", "CA"],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "SITE_OF_CARE",
            "name": "Preferred Site - Home Infusion",
            "parameters": {
                "allowed_sites": ["HOME", "FREESTANDING"],
                "disallowed_sites": ["HOSPITAL_OP"],
            },
            "enabled": True,
            "priority": 0,
        },
        {
            "lever_type": "COST_SHARING",
            "name": "Differential Cost Sharing",
            "parameters": {
                "copay": 50,
                "differential_by_site": {
                    "HOME": 25,
                    "HOSPITAL_OP": 150,
                },
            },
            "enabled": True,
            "priority": 1,
        },
        {
            "lever_type": "PRIOR_AUTH",
            "name": "Hospital OP PA Requirement",
            "parameters": {
                "codes": ["96413", "96415", "96416"],
                "enforcement": "HARD",
            },
            "enabled": True,
            "priority": 2,
        },
    ],
    "effective_start": "2025-03-01",
    "effective_end": None,
    "tags": ["Infusion", "Composite", "Site of Care", "Cost Sharing"],
}

# Example 7: Composite Policy - High-Cost Provider Control
COMPOSITE_POLICY_4 = {
    "policy_name": "High-Cost Provider Control Policy",
    "policy_description": "Targets high-cost providers with prior authorization, network restrictions, and payment caps",
    "policy_owner": "Network Management",
    "policy_category": "NETWORK",
    "scope": {
        "line_of_business": ["Commercial"],
        "markets": ["TX"],
        "network_id": None,
    },
    "levers": [
        {
            "lever_type": "PRIOR_AUTH",
            "name": "High-Cost Provider PA",
            "parameters": {
                "codes": ["99213", "99214", "99215"],
                "enforcement": "HARD",
            },
            "enabled": True,
            "priority": 0,
        },
        {
            "lever_type": "NETWORK_RESTRICTION",
            "name": "Narrow Network Tier",
            "parameters": {
                "network_tier": "TIER_2",
            },
            "enabled": True,
            "priority": 1,
        },
        {
            "lever_type": "PAYMENT_POLICY",
            "name": "Fee Caps",
            "parameters": {
                "fee_caps": {
                    "99213": 150,
                    "99214": 200,
                    "99215": 250,
                },
            },
            "enabled": True,
            "priority": 2,
        },
    ],
    "effective_start": "2025-06-01",
    "effective_end": None,
    "tags": ["Provider Control", "Composite", "Network"],
}


def create_policy_logic_from_dict(policy_dict: dict) -> PolicyLogic:
    """Convert dictionary to PolicyLogic object"""
    scope = PolicyScope(**policy_dict["scope"])
    
    levers = []
    for lever_dict in policy_dict["levers"]:
        lever = PolicyLever(
            lever_id=uuid4(),  # Generate new UUID for each lever
            lever_type=LeverTypeEnum(lever_dict["lever_type"]),
            name=lever_dict["name"],
            parameters=lever_dict["parameters"],
            enabled=lever_dict.get("enabled", True),
            priority=lever_dict.get("priority", 0),
        )
        levers.append(lever)
    
    return PolicyLogic(
        policy_id=uuid4(),  # Generate new UUID for policy
        policy_name=policy_dict["policy_name"],
        policy_description=policy_dict.get("policy_description"),
        policy_owner=policy_dict["policy_owner"],
        policy_category=policy_dict.get("policy_category", "UTILIZATION"),
        scope=scope,
        levers=levers,
        effective_start=date.fromisoformat(policy_dict["effective_start"]),
        effective_end=date.fromisoformat(policy_dict["effective_end"]) if policy_dict.get("effective_end") else None,
        tags=policy_dict.get("tags", []),
    )


def main():
    """Seed example policies"""
    tenant_id = DEFAULT_TENANT_ID
    
    # Check existing policies
    existing = list_policies(tenant_id)
    existing_names = {p.get("name") or p.get("policy_name") for p in existing}
    
    policies_to_create = [
        ("Standalone 1", STANDALONE_POLICY_1),
        ("Standalone 2", STANDALONE_POLICY_2),
        ("Standalone 3", STANDALONE_POLICY_3),
        ("Composite 1", COMPOSITE_POLICY_1),
        ("Composite 2", COMPOSITE_POLICY_2),
        ("Composite 3", COMPOSITE_POLICY_3),
        ("Composite 4", COMPOSITE_POLICY_4),
    ]
    
    created = 0
    skipped = 0
    
    for label, policy_dict in policies_to_create:
        policy_name = policy_dict["policy_name"]
        
        if policy_name in existing_names:
            print(f"⏭️  Skipping {label}: {policy_name} (already exists)")
            skipped += 1
            continue
        
        try:
            # Create PolicyLogic object
            policy_logic = create_policy_logic_from_dict(policy_dict)
            
            # Create policy record
            policy_data = {
                "name": policy_name,
                "description": policy_dict.get("policy_description"),
                "status": "ACTIVE",
                "policy_type": "COMPOSITE" if len(policy_dict["levers"]) > 1 else policy_dict["levers"][0]["lever_type"],
                "effective_date": policy_dict["effective_start"],
                "expiration_date": policy_dict.get("effective_end"),
                "metadata": {
                    "owner": policy_dict["policy_owner"],
                    "category": policy_dict.get("policy_category", "UTILIZATION"),
                    "tags": policy_dict.get("tags", []),
                    "is_standalone": len(policy_dict["levers"]) == 1,
                    "is_composite": len(policy_dict["levers"]) > 1,
                    "lever_count": len(policy_dict["levers"]),
                },
                "logic": policy_logic.model_dump(mode='json'),
            }
            
            create_policy(tenant_id, policy_data)
            print(f"✅ Created {label}: {policy_name} ({len(policy_dict['levers'])} lever{'s' if len(policy_dict['levers']) > 1 else ''})")
            created += 1
        
        except Exception as e:
            print(f"❌ Error creating {label}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Summary: {created} created, {skipped} skipped")


if __name__ == "__main__":
    main()

