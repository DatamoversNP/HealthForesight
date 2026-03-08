#!/usr/bin/env python3
"""
Seed complete policies with all 6 workflow levels - PURE JSON VERSION (NO DEPENDENCIES)
- Standalone policies (single lever)
- Composite policies (multiple levers)
- All policies have complete: Basic Info, Scope, Levers, Conditions, Exceptions, Review metadata
- Writes JSON files directly - no database, no pydantic, no dependencies needed
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4


def create_standalone_policies():
    """Create standalone policy definitions (one policy = one lever)"""
    base_date = datetime.utcnow()
    
    policies = [
        {
            "name": "Outpatient MRI Prior Authorization",
            "policy_type": "PRIOR_AUTH",
            "owner_role": "UM_LEADER",
            "description": "Require prior authorization for outpatient MRI to reduce inappropriate imaging. Owned by UM, frequently changed independently.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=180)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["NYC", "DFW"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "codes": ["72148", "72149", "72158"],
                        "code_type": "CPT",
                        "enforcement": "HARD",
                        "site_of_care": "OUTPATIENT"
                    }
                }
            ],
            "conditions": [
                {
                    "field": "place_of_service",
                    "operator": "IN",
                    "values": ["11", "22"]
                },
                {
                    "field": "provider_specialty",
                    "operator": "IN",
                    "values": ["Radiology", "Diagnostic Radiology"]
                }
            ],
            "exceptions": [
                {"type": "ER", "description": "Emergency room services excluded"},
                {"type": "URGENT", "description": "Urgent conditions excluded"},
                {"type": "AGE", "parameters": {"min_age": None, "max_age": 18}, "description": "Pediatric members excluded"}
            ],
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW"],
                "override_allowed": False
            }
        },
        {
            "name": "Physical Therapy Visit Limit",
            "policy_type": "DURATION_FREQUENCY_LIMIT",
            "owner_role": "BENEFIT_ADMIN",
            "description": "Limit PT visits to 20 per calendar year. Benefit design driven, often negotiated annually.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=365)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL", "MEDICAID"],
                "markets": ["ALL"],
                "network": ["ALL"]
            },
            "levers": [
                {
                    "lever_type": "DURATION_FREQUENCY_LIMIT",
                    "parameters": {
                        "codes": ["97110", "97112", "97140"],
                        "code_type": "CPT",
                        "max_visits": 20,
                        "time_period": "YEAR"
                    }
                }
            ],
            "conditions": [{"field": "service_category", "operator": "EQUALS", "values": ["PHYSICAL_THERAPY"]}],
            "exceptions": [
                {"type": "POST_SURGICAL", "description": "Post-surgical rehabilitation excluded from limit"},
                {"type": "MEDICAL_NECESSITY", "description": "Medical necessity override available"}
            ],
            "enforcement": {
                "mechanism": "PASSIVE",
                "touchpoint": ["BENEFIT_ACCUMULATOR"],
                "override_allowed": True
            }
        },
        {
            "name": "Urgent Care Cost Sharing Policy",
            "policy_type": "COST_SHARING",
            "owner_role": "ACTUARIAL",
            "description": "Increase copay for urgent care visits to discourage low-acuity use. Financial lever only, owned by benefits/actuarial.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=120)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": "COST_SHARING",
                    "parameters": {
                        "service_category": "URGENT_CARE",
                        "place_of_service": ["20"],
                        "copay": {"from": 40, "to": 75},
                        "coinsurance": None
                    }
                }
            ],
            "conditions": [{"field": "place_of_service", "operator": "EQUALS", "values": ["20"]}],
            "exceptions": [{"type": "ER", "description": "ER visits not affected"}],
            "enforcement": {
                "mechanism": "PASSIVE",
                "touchpoint": ["BENEFIT_ACCUMULATOR"],
                "override_allowed": False
            }
        },
        {
            "name": "Step Therapy for High-Cost Biologic",
            "policy_type": "STEP_THERAPY",
            "owner_role": "PHARMACY_ADMIN",
            "description": "Require step therapy before approving high-cost biologic treatments. Requires lower-cost therapy before higher-cost option.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=90)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL", "MA"],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": "STEP_THERAPY",
                    "parameters": {
                        "codes": ["96413", "96415"],
                        "code_type": "CPT",
                        "step_sequence": [
                            {"step": 1, "code": "J9310", "duration_days": 90},
                            {"step": 2, "code": "96413", "duration_days": None}
                        ],
                        "required_duration_per_step": 90
                    }
                }
            ],
            "conditions": [
                {"field": "diagnosis_group", "operator": "IN", "values": ["ONCOLOGY", "IMMUNOLOGY"]},
                {"field": "prior_treatment_history", "operator": "EQUALS", "values": ["NONE"]}
            ],
            "exceptions": [
                {"type": "CONTRAINDICATION", "description": "Contraindications to step 1 medication"},
                {"type": "FAILURE_DOCUMENTATION", "description": "Documented failure of step 1 therapy"}
            ],
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW"],
                "override_allowed": True
            }
        },
    ]
    
    return policies


def create_composite_policies():
    """Create composite policy definitions (one policy = multiple levers)"""
    base_date = datetime.utcnow()
    
    policies = [
        {
            "name": "Advanced Imaging Utilization Management Policy",
            "policy_type": "PRIOR_AUTH",
            "owner_role": "UM_LEADER",
            "description": "Comprehensive imaging control combining Prior Auth, Site of Care, and Clinical Criteria. Interaction effects matter - PA alone may shift volume, SOC alone may increase ER imaging, together they behave non-linearly.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=240)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["NYC", "BOS"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "codes": ["70551", "70552", "70553", "72148", "72149"],
                        "code_type": "CPT",
                        "enforcement": "HARD",
                        "site_of_care": "OUTPATIENT"
                    }
                },
                {
                    "lever_type": "SITE_OF_CARE",
                    "parameters": {
                        "allowed_sites": ["FREESTANDING"],
                        "disallowed_sites": ["HOSPITAL_OP"],
                        "differential_cost_sharing": {
                            "hospital_op_copay": 150,
                            "freestanding_copay": 75
                        }
                    }
                },
                {
                    "lever_type": "CLINICAL_CRITERIA",
                    "parameters": {
                        "criteria_set": "INTERNAL_IMAGING_GUIDELINES",
                        "strictness_level": "MEDIUM",
                        "reference_standard": "ACR_APPROPRIATENESS"
                    }
                }
            ],
            "conditions": [
                {"field": "place_of_service", "operator": "IN", "values": ["11", "22"]},
                {"field": "provider_specialty", "operator": "IN", "values": ["Radiology", "Diagnostic Radiology"]}
            ],
            "exceptions": [
                {"type": "ER", "description": "Emergency room services excluded"},
                {"type": "CLINICAL_COMPLEXITY", "description": "High clinical complexity cases excluded"}
            ],
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
                "override_allowed": False
            }
        },
        {
            "name": "Specialty Drug Utilization Policy",
            "policy_type": "STEP_THERAPY",
            "owner_role": "PHARMACY_ADMIN",
            "description": "Comprehensive specialty drug control combining Step Therapy, Prior Auth, Quantity Limits, and Clinical Criteria. Drugs almost always require bundles.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=180)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL", "MA"],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": "STEP_THERAPY",
                    "parameters": {
                        "codes": ["J9310", "J9311"],
                        "code_type": "HCPCS",
                        "step_sequence": [
                            {"step": 1, "code": "J9310", "duration_days": 90},
                            {"step": 2, "code": "J9311", "duration_days": None}
                        ]
                    }
                },
                {
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "codes": ["J9310", "J9311"],
                        "code_type": "HCPCS",
                        "enforcement": "HARD"
                    }
                },
                {
                    "lever_type": "QUANTITY_LIMIT",
                    "parameters": {
                        "codes": ["J9310", "J9311"],
                        "code_type": "HCPCS",
                        "max_units_per_episode": 6,
                        "max_units_per_day": 1
                    }
                },
                {
                    "lever_type": "CLINICAL_CRITERIA",
                    "parameters": {
                        "criteria_set": "SPECIALTY_DRUG_GUIDELINES",
                        "strictness_level": "HIGH"
                    }
                }
            ],
            "conditions": [{"field": "diagnosis_group", "operator": "IN", "values": ["ONCOLOGY", "IMMUNOLOGY", "RHEUMATOLOGY"]}],
            "exceptions": [
                {"type": "CONTRAINDICATION", "description": "Contraindications to step therapy"},
                {"type": "MEDICAL_NECESSITY", "description": "Medical necessity override"}
            ],
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW"],
                "override_allowed": True
            }
        },
        {
            "name": "Outpatient Infusion Optimization Policy",
            "policy_type": "SITE_OF_CARE",
            "owner_role": "UM_LEADER",
            "description": "Comprehensive infusion control combining Site of Care, Cost Sharing, and Prior Authorization. Site + cost + authorization all interact.",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=210)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL", "MA"],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": "SITE_OF_CARE",
                    "parameters": {
                        "preferred_sites": ["HOME", "FREESTANDING"],
                        "disallowed_sites": ["HOSPITAL_OP"],
                        "site_preference_order": ["HOME", "FREESTANDING", "OFFICE"]
                    }
                },
                {
                    "lever_type": "COST_SHARING",
                    "parameters": {
                        "codes": ["96413", "96415", "96417"],
                        "code_type": "CPT",
                        "differential_by_site": {
                            "hospital_op": {"copay": 200, "coinsurance": 20},
                            "freestanding": {"copay": 100, "coinsurance": 10},
                            "home": {"copay": 75, "coinsurance": 10}
                        }
                    }
                },
                {
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "codes": ["96413", "96415", "96417"],
                        "code_type": "CPT",
                        "enforcement": "HARD",
                        "site_specific": {
                            "hospital_op": "REQUIRED",
                            "freestanding": "REQUIRED",
                            "home": "OPTIONAL"
                        }
                    }
                }
            ],
            "conditions": [
                {"field": "service_category", "operator": "EQUALS", "values": ["INFUSION"]},
                {"field": "place_of_service", "operator": "IN", "values": ["22", "19", "12"]}
            ],
            "exceptions": [
                {"type": "CLINICAL_COMPLEXITY", "description": "High complexity cases may require hospital setting"},
                {"type": "PATIENT_SAFETY", "description": "Patient safety concerns override site restrictions"}
            ],
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
                "override_allowed": True
            }
        },
        {
            "name": "High-Cost Provider Control Policy",
            "policy_type": "NETWORK_RESTRICTION",
            "owner_role": "NETWORK_ADMIN",
            "description": "Multi-lever policy targeting high-cost provider behavior. Combines Prior Auth (high-cost providers only), Network Restriction (narrow tier), and Payment Policy (fee cap).",
            "status": "ACTIVE",
            "effective_start_date": (base_date - timedelta(days=150)).isoformat(),
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["NYC", "DFW"],
                "network": ["TIER_2"]
            },
            "levers": [
                {
                    "lever_type": "PRIOR_AUTH",
                    "parameters": {
                        "codes": ["ALL"],
                        "enforcement": "HARD",
                        "provider_segment": "HIGH_COST",
                        "cost_threshold_percentile": 90
                    }
                },
                {
                    "lever_type": "NETWORK_RESTRICTION",
                    "parameters": {
                        "network_tier": "TIER_2",
                        "provider_list": "HIGH_COST_PROVIDERS",
                        "restriction_type": "REQUIRE_TIER_1_PREFERRED"
                    }
                },
                {
                    "lever_type": "PAYMENT_POLICY",
                    "parameters": {
                        "fee_cap_type": "PERCENTILE",
                        "fee_cap_percentile": 75,
                        "bundling_rules": "ENCOURAGE",
                        "global_payment_preference": True
                    }
                }
            ],
            "conditions": [
                {"field": "provider_segment", "operator": "EQUALS", "values": ["HIGH_COST"]},
                {"field": "cost_percentile", "operator": "GREATER_THAN", "values": [90]}
            ],
            "exceptions": [
                {"type": "ACCESS", "description": "Access concerns in rural areas"},
                {"type": "QUALITY", "description": "High-quality providers exempt from restrictions"}
            ],
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
                "override_allowed": True
            }
        },
    ]
    
    return policies


def build_policy_json(policy_def: dict, policy_id: str) -> dict:
    """Build policy JSON structure matching CanonicalPolicy format"""
    
    return {
        "policy_id": policy_id,
        "policy_name": policy_def["name"],
        "policy_type": policy_def["policy_type"],
        "description": policy_def["description"],
        "status": policy_def["status"],
        "effective_period": {
            "start_date": policy_def["effective_start_date"],
            "end_date": None
        },
        "scope": policy_def["scope"],
        "enforcement": policy_def["enforcement"],
        "policy_levers": policy_def["levers"],
        "apply_when": policy_def.get("conditions", []),
        "global_exceptions": policy_def.get("exceptions", []),
    }


def seed_complete_policies_json(tenant_id: str, data_dir: Path = None, clear_existing: bool = False):
    """Seed complete policies using JSON file storage"""
    
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent / "data"
    
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    policies_file = data_dir / f"policies_{tenant_id}.json"
    
    # Load existing policies
    if clear_existing or not policies_file.exists():
        policies_data = {
            "tenant_id": tenant_id,
            "updated_at": datetime.utcnow().isoformat(),
            "policies": []
        }
    else:
        try:
            with open(policies_file, 'r') as f:
                policies_data = json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing policies: {e}")
            policies_data = {
                "tenant_id": tenant_id,
                "updated_at": datetime.utcnow().isoformat(),
                "policies": []
            }
    
    # Get all policy definitions
    standalone_policies = create_standalone_policies()
    composite_policies = create_composite_policies()
    all_policies = standalone_policies + composite_policies
    
    print(f"\n📋 Creating {len(all_policies)} complete policies:")
    print(f"   - {len(standalone_policies)} standalone (single lever)")
    print(f"   - {len(composite_policies)} composite (multiple levers)")
    
    # Create lookup of existing policies by name
    existing_policies = {p.get("policy_name"): p for p in policies_data.get("policies", [])}
    policies_list = policies_data.get("policies", [])
    created_count = 0
    updated_count = 0
    
    for policy_def in all_policies:
        policy_name = policy_def["name"]
        existing = existing_policies.get(policy_name)
        
        # Use existing ID or generate new
        if existing:
            policy_id = existing["policy_id"]
        else:
            policy_id = str(uuid4())
        
        # Build policy JSON
        policy_json = build_policy_json(policy_def, policy_id)
        
        # Update or add
        if existing:
            # Update existing
            for i, p in enumerate(policies_list):
                if p.get("policy_name") == policy_name:
                    policies_list[i] = policy_json
                    updated_count += 1
                    lever_count = len(policy_def["levers"])
                    print(f"   ✅ Updated: {policy_name} ({lever_count} lever(s))")
                    break
        else:
            # Add new
            policies_list.append(policy_json)
            created_count += 1
            lever_count = len(policy_def["levers"])
            print(f"   ✅ Created: {policy_name} ({lever_count} lever(s))")
    
    # Save to file
    policies_data["policies"] = policies_list
    policies_data["updated_at"] = datetime.utcnow().isoformat()
    
    with open(policies_file, 'w') as f:
        json.dump(policies_data, f, indent=2, default=str)
    
    print(f"\n✅ Complete! Created {created_count}, Updated {updated_count}")
    print(f"   Total policies: {created_count + updated_count}")
    print(f"   All policies have complete 6-level workflow definitions")
    print(f"   File: {policies_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed complete policies (file-based JSON, no dependencies)")
    parser.add_argument("--clear", action="store_true", help="Clear existing policies before seeding")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000002", help="Tenant ID")
    parser.add_argument("--data-dir", type=str, default=None, help="Data directory (default: data/)")
    
    args = parser.parse_args()
    
    try:
        seed_complete_policies_json(args.tenant_id, data_dir=args.data_dir, clear_existing=args.clear)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
