"""
Seed complete policies with all 6 workflow levels defined
- Standalone policies (single lever)
- Composite policies (multiple levers)
- All policies have complete: Basic Info, Scope, Levers, Conditions, Exceptions, Review metadata
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api" / "src"))

from sqlalchemy.orm import Session

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy, PolicyVersion, PolicyCodeSet
from uepi_api.models.tenant import Tenant
from uepi_common.models import (
    PolicyType,
    PolicyStatus,
    PolicyScope,
    EffectivePeriod,
    Enforcement,
    PolicyLever,
    EnforcementMechanism,
    PolicyTouchpoint,
    LineOfBusiness,
)


# ============================================================================
# STANDALONE POLICIES (Single Lever)
# ============================================================================

def create_standalone_policies() -> list[dict]:
    """Create standalone policy definitions (one policy = one lever)"""
    
    base_date = datetime.utcnow()
    
    policies = [
        # STANDALONE 1: Outpatient MRI Prior Authorization
        {
            "name": "Outpatient MRI Prior Authorization",
            "policy_type": PolicyType.PRIOR_AUTH.value,
            "owner_role": "UM_LEADER",
            "description": "Require prior authorization for outpatient MRI to reduce inappropriate imaging. Owned by UM, frequently changed independently.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=180),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value],
                "markets": ["NYC", "DFW"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.PRIOR_AUTH.value,
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
                    "values": ["11", "22"]  # Office, Outpatient Hospital
                },
                {
                    "field": "provider_specialty",
                    "operator": "IN",
                    "values": ["Radiology", "Diagnostic Radiology"]
                }
            ],
            "exceptions": [
                {
                    "type": "ER",
                    "description": "Emergency room services excluded"
                },
                {
                    "type": "URGENT",
                    "description": "Urgent conditions excluded"
                },
                {
                    "type": "AGE",
                    "parameters": {
                        "min_age": None,
                        "max_age": 18
                    },
                    "description": "Pediatric members excluded"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.HARD.value,
                "touchpoint": [PolicyTouchpoint.PA_WORKFLOW.value],
                "override_allowed": False
            }
        },
        
        # STANDALONE 2: Physical Therapy Visit Limit
        {
            "name": "Physical Therapy Visit Limit",
            "policy_type": PolicyType.DURATION_FREQUENCY_LIMIT.value,
            "owner_role": "BENEFIT_ADMIN",
            "description": "Limit PT visits to 20 per calendar year. Benefit design driven, often negotiated annually.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=365),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value, LineOfBusiness.MEDICAID.value],
                "markets": ["ALL"],
                "network": ["ALL"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.DURATION_FREQUENCY_LIMIT.value,
                    "parameters": {
                        "codes": ["97110", "97112", "97140"],
                        "code_type": "CPT",
                        "max_visits": 20,
                        "time_period": "YEAR"
                    }
                }
            ],
            "conditions": [
                {
                    "field": "service_category",
                    "operator": "EQUALS",
                    "values": ["PHYSICAL_THERAPY"]
                }
            ],
            "exceptions": [
                {
                    "type": "POST_SURGICAL",
                    "description": "Post-surgical rehabilitation excluded from limit"
                },
                {
                    "type": "MEDICAL_NECESSITY",
                    "description": "Medical necessity override available"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.PASSIVE.value,
                "touchpoint": [PolicyTouchpoint.BENEFIT_ACCUMULATOR.value],
                "override_allowed": True
            }
        },
        
        # STANDALONE 3: Urgent Care Cost Sharing
        {
            "name": "Urgent Care Cost Sharing Policy",
            "policy_type": PolicyType.COST_SHARING.value,
            "owner_role": "ACTUARIAL",
            "description": "Increase copay for urgent care visits to discourage low-acuity use. Financial lever only, owned by benefits/actuarial.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=120),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.COST_SHARING.value,
                    "parameters": {
                        "service_category": "URGENT_CARE",
                        "place_of_service": ["20"],
                        "copay": {
                            "from": 40,
                            "to": 75
                        },
                        "coinsurance": None
                    }
                }
            ],
            "conditions": [
                {
                    "field": "place_of_service",
                    "operator": "EQUALS",
                    "values": ["20"]  # Urgent Care
                }
            ],
            "exceptions": [
                {
                    "type": "ER",
                    "description": "ER visits not affected"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.PASSIVE.value,
                "touchpoint": [PolicyTouchpoint.BENEFIT_ACCUMULATOR.value],
                "override_allowed": False
            }
        },
        
        # STANDALONE 4: Step Therapy for High-Cost Biologic
        {
            "name": "Step Therapy for High-Cost Biologic",
            "policy_type": PolicyType.STEP_THERAPY.value,
            "owner_role": "PHARMACY_ADMIN",
            "description": "Require step therapy before approving high-cost biologic treatments. Requires lower-cost therapy before higher-cost option.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=90),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value, LineOfBusiness.MA.value],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.STEP_THERAPY.value,
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
                {
                    "field": "diagnosis_group",
                    "operator": "IN",
                    "values": ["ONCOLOGY", "IMMUNOLOGY"]
                },
                {
                    "field": "prior_treatment_history",
                    "operator": "EQUALS",
                    "values": ["NONE"]
                }
            ],
            "exceptions": [
                {
                    "type": "CONTRAINDICATION",
                    "description": "Contraindications to step 1 medication"
                },
                {
                    "type": "FAILURE_DOCUMENTATION",
                    "description": "Documented failure of step 1 therapy"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.HARD.value,
                "touchpoint": [PolicyTouchpoint.PA_WORKFLOW.value],
                "override_allowed": True
            }
        },
    ]
    
    return policies


# ============================================================================
# COMPOSITE POLICIES (Multiple Levers)
# ============================================================================

def create_composite_policies() -> list[dict]:
    """Create composite policy definitions (one policy = multiple levers)"""
    
    base_date = datetime.utcnow()
    
    policies = [
        # COMPOSITE 1: Advanced Imaging Utilization Management Policy
        {
            "name": "Advanced Imaging Utilization Management Policy",
            "policy_type": PolicyType.PRIOR_AUTH.value,  # Primary type, but has multiple levers
            "owner_role": "UM_LEADER",
            "description": "Comprehensive imaging control combining Prior Auth, Site of Care, and Clinical Criteria. Interaction effects matter - PA alone may shift volume, SOC alone may increase ER imaging, together they behave non-linearly.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=240),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value],
                "markets": ["NYC", "BOS"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.PRIOR_AUTH.value,
                    "parameters": {
                        "codes": ["70551", "70552", "70553", "72148", "72149"],
                        "code_type": "CPT",
                        "enforcement": "HARD",
                        "site_of_care": "OUTPATIENT"
                    }
                },
                {
                    "lever_type": PolicyType.SITE_OF_CARE.value,
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
                    "lever_type": PolicyType.CLINICAL_CRITERIA.value,
                    "parameters": {
                        "criteria_set": "INTERNAL_IMAGING_GUIDELINES",
                        "strictness_level": "MEDIUM",
                        "reference_standard": "ACR_APPROPRIATENESS"
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
                {
                    "type": "ER",
                    "description": "Emergency room services excluded"
                },
                {
                    "type": "CLINICAL_COMPLEXITY",
                    "description": "High clinical complexity cases excluded"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.HARD.value,
                "touchpoint": [PolicyTouchpoint.PA_WORKFLOW.value, PolicyTouchpoint.CLAIM_EDIT.value],
                "override_allowed": False
            }
        },
        
        # COMPOSITE 2: Specialty Drug Utilization Policy
        {
            "name": "Specialty Drug Utilization Policy",
            "policy_type": PolicyType.STEP_THERAPY.value,  # Primary type
            "owner_role": "PHARMACY_ADMIN",
            "description": "Comprehensive specialty drug control combining Step Therapy, Prior Auth, Quantity Limits, and Clinical Criteria. Drugs almost always require bundles.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=180),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value, LineOfBusiness.MA.value],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.STEP_THERAPY.value,
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
                    "lever_type": PolicyType.PRIOR_AUTH.value,
                    "parameters": {
                        "codes": ["J9310", "J9311"],
                        "code_type": "HCPCS",
                        "enforcement": "HARD"
                    }
                },
                {
                    "lever_type": PolicyType.QUANTITY_LIMIT.value,
                    "parameters": {
                        "codes": ["J9310", "J9311"],
                        "code_type": "HCPCS",
                        "max_units_per_episode": 6,
                        "max_units_per_day": 1
                    }
                },
                {
                    "lever_type": PolicyType.CLINICAL_CRITERIA.value,
                    "parameters": {
                        "criteria_set": "SPECIALTY_DRUG_GUIDELINES",
                        "strictness_level": "HIGH"
                    }
                }
            ],
            "conditions": [
                {
                    "field": "diagnosis_group",
                    "operator": "IN",
                    "values": ["ONCOLOGY", "IMMUNOLOGY", "RHEUMATOLOGY"]
                }
            ],
            "exceptions": [
                {
                    "type": "CONTRAINDICATION",
                    "description": "Contraindications to step therapy"
                },
                {
                    "type": "MEDICAL_NECESSITY",
                    "description": "Medical necessity override"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.HARD.value,
                "touchpoint": [PolicyTouchpoint.PA_WORKFLOW.value],
                "override_allowed": True
            }
        },
        
        # COMPOSITE 3: Outpatient Infusion Optimization Policy
        {
            "name": "Outpatient Infusion Optimization Policy",
            "policy_type": PolicyType.SITE_OF_CARE.value,  # Primary type
            "owner_role": "UM_LEADER",
            "description": "Comprehensive infusion control combining Site of Care, Cost Sharing, and Prior Authorization. Site + cost + authorization all interact.",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=210),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value, LineOfBusiness.MA.value],
                "markets": ["ALL"],
                "network": ["IN"]
            },
            "levers": [
                {
                    "lever_type": PolicyType.SITE_OF_CARE.value,
                    "parameters": {
                        "preferred_sites": ["HOME", "FREESTANDING"],
                        "disallowed_sites": ["HOSPITAL_OP"],
                        "site_preference_order": ["HOME", "FREESTANDING", "OFFICE"]
                    }
                },
                {
                    "lever_type": PolicyType.COST_SHARING.value,
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
                    "lever_type": PolicyType.PRIOR_AUTH.value,
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
                {
                    "field": "service_category",
                    "operator": "EQUALS",
                    "values": ["INFUSION"]
                },
                {
                    "field": "place_of_service",
                    "operator": "IN",
                    "values": ["22", "19", "12"]  # Hospital OP, Off Campus, Home
                }
            ],
            "exceptions": [
                {
                    "type": "CLINICAL_COMPLEXITY",
                    "description": "High complexity cases may require hospital setting"
                },
                {
                    "type": "PATIENT_SAFETY",
                    "description": "Patient safety concerns override site restrictions"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.HARD.value,
                "touchpoint": [PolicyTouchpoint.PA_WORKFLOW.value, PolicyTouchpoint.CLAIM_EDIT.value],
                "override_allowed": True
            }
        },
        
        # COMPOSITE 4: High-Cost Provider Control Policy
        {
            "name": "High-Cost Provider Control Policy",
            "policy_type": PolicyType.NETWORK_RESTRICTION.value,  # Primary type
            "owner_role": "NETWORK_ADMIN",
            "description": "Multi-lever policy targeting high-cost provider behavior. Combines Prior Auth (high-cost providers only), Network Restriction (narrow tier), and Payment Policy (fee cap).",
            "status": PolicyStatus.ACTIVE.value,
            "effective_start_date": base_date - timedelta(days=150),
            "scope": {
                "lob": [LineOfBusiness.COMMERCIAL.value],
                "markets": ["NYC", "DFW"],
                "network": ["TIER_2"]  # Narrow network tier
            },
            "levers": [
                {
                    "lever_type": PolicyType.PRIOR_AUTH.value,
                    "parameters": {
                        "codes": ["ALL"],
                        "enforcement": "HARD",
                        "provider_segment": "HIGH_COST",
                        "cost_threshold_percentile": 90
                    }
                },
                {
                    "lever_type": PolicyType.NETWORK_RESTRICTION.value,
                    "parameters": {
                        "network_tier": "TIER_2",
                        "provider_list": "HIGH_COST_PROVIDERS",
                        "restriction_type": "REQUIRE_TIER_1_PREFERRED"
                    }
                },
                {
                    "lever_type": PolicyType.PAYMENT_POLICY.value,
                    "parameters": {
                        "fee_cap_type": "PERCENTILE",
                        "fee_cap_percentile": 75,
                        "bundling_rules": "ENCOURAGE",
                        "global_payment_preference": True
                    }
                }
            ],
            "conditions": [
                {
                    "field": "provider_segment",
                    "operator": "EQUALS",
                    "values": ["HIGH_COST"]
                },
                {
                    "field": "cost_percentile",
                    "operator": "GREATER_THAN",
                    "values": [90]
                }
            ],
            "exceptions": [
                {
                    "type": "ACCESS",
                    "description": "Access concerns in rural areas"
                },
                {
                    "type": "QUALITY",
                    "description": "High-quality providers exempt from restrictions"
                }
            ],
            "enforcement": {
                "mechanism": EnforcementMechanism.HARD.value,
                "touchpoint": [PolicyTouchpoint.PA_WORKFLOW.value, PolicyTouchpoint.CLAIM_EDIT.value],
                "override_allowed": True
            }
        },
    ]
    
    return policies


# ============================================================================
# POLICY CREATION HELPER
# ============================================================================

def build_policy_metadata(policy_def: dict) -> dict:
    """Build complete policy_metadata_json from policy definition"""
    
    metadata = {
        "scope": policy_def["scope"],
        "effective_period": {
            "start_date": policy_def["effective_start_date"].isoformat(),
            "end_date": None
        },
        "policy_levers": policy_def["levers"],
        "apply_when": policy_def.get("conditions", []),
        "global_exceptions": policy_def.get("exceptions", []),
        "enforcement": policy_def.get("enforcement", {}),
    }
    
    return metadata


def seed_complete_policies(tenant_id: UUID, db: Session, clear_existing: bool = False):
    """Seed complete policies with all 6 workflow levels"""
    
    if clear_existing:
        print("⚠️  Clearing existing policies...")
        existing_policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).all()
        for policy in existing_policies:
            # Delete related versions and code sets
            versions = db.query(PolicyVersion).filter(PolicyVersion.policy_id == policy.id).all()
            for version in versions:
                db.query(PolicyCodeSet).filter(PolicyCodeSet.version_id == version.id).delete()
            db.query(PolicyVersion).filter(PolicyVersion.policy_id == policy.id).delete()
        db.query(Policy).filter(Policy.tenant_id == tenant_id).delete()
        db.commit()
        print(f"✅ Cleared {len(existing_policies)} existing policies")
    
    # Get all policy definitions
    standalone_policies = create_standalone_policies()
    composite_policies = create_composite_policies()
    all_policies = standalone_policies + composite_policies
    
    print(f"\n📋 Creating {len(all_policies)} complete policies:")
    print(f"   - {len(standalone_policies)} standalone (single lever)")
    print(f"   - {len(composite_policies)} composite (multiple levers)")
    
    created_count = 0
    updated_count = 0
    
    for policy_def in all_policies:
        # Check if policy exists
        existing = db.query(Policy).filter(
            Policy.name == policy_def["name"],
            Policy.tenant_id == tenant_id
        ).first()
        
        # Build complete metadata
        metadata = build_policy_metadata(policy_def)
        
        if existing:
            # Update existing policy
            existing.policy_type = policy_def["policy_type"]
            existing.owner_role = policy_def["owner_role"]
            existing.description = policy_def["description"]
            existing.status = policy_def["status"]
            existing.policy_metadata_json = metadata
            existing.updated_at = datetime.utcnow()
            
            # Update or create version
            version = db.query(PolicyVersion).filter(
                PolicyVersion.policy_id == existing.id
            ).order_by(PolicyVersion.version_number.desc()).first()
            
            if not version:
                version = PolicyVersion(
                    tenant_id=tenant_id,
                    policy_id=existing.id,
                    version_number=1,
                    effective_start_date=policy_def["effective_start_date"],
                    change_type="NEW",
                    enforcement_strength="HARD",
                )
                db.add(version)
            else:
                version.effective_start_date = policy_def["effective_start_date"]
                version.updated_at = datetime.utcnow()
            
            db.flush()
            
            # Update code sets from levers
            # Clear existing code sets for this version
            db.query(PolicyCodeSet).filter(PolicyCodeSet.version_id == version.id).delete()
            
            # Add code sets from all levers
            for lever in policy_def["levers"]:
                codes = lever.get("parameters", {}).get("codes", [])
                code_type = lever.get("parameters", {}).get("code_type", "CPT")
                for code in codes:
                    code_set = PolicyCodeSet(
                        tenant_id=tenant_id,
                        version_id=version.id,
                        code=code,
                        code_type=code_type,
                        code_group=policy_def["policy_type"]
                    )
                    db.add(code_set)
            
            updated_count += 1
            print(f"   ✅ Updated: {policy_def['name']} ({len(policy_def['levers'])} lever(s))")
            
        else:
            # Create new policy
            policy = Policy(
                tenant_id=tenant_id,
                name=policy_def["name"],
                policy_type=policy_def["policy_type"],
                owner_role=policy_def["owner_role"],
                description=policy_def["description"],
                status=policy_def["status"],
                policy_metadata_json=metadata,
            )
            db.add(policy)
            db.flush()
            
            # Create policy version
            version = PolicyVersion(
                tenant_id=tenant_id,
                policy_id=policy.id,
                version_number=1,
                effective_start_date=policy_def["effective_start_date"],
                change_type="NEW",
                enforcement_strength=policy_def.get("enforcement", {}).get("mechanism", "HARD"),
            )
            db.add(version)
            db.flush()
            
            # Create code sets from all levers
            for lever in policy_def["levers"]:
                codes = lever.get("parameters", {}).get("codes", [])
                code_type = lever.get("parameters", {}).get("code_type", "CPT")
                for code in codes:
                    code_set = PolicyCodeSet(
                        tenant_id=tenant_id,
                        version_id=version.id,
                        code=code,
                        code_type=code_type,
                        code_group=policy_def["policy_type"]
                    )
                    db.add(code_set)
            
            created_count += 1
            print(f"   ✅ Created: {policy_def['name']} ({len(policy_def['levers'])} lever(s))")
    
    db.commit()
    print(f"\n✅ Complete! Created {created_count}, Updated {updated_count}")
    print(f"   Total policies: {created_count + updated_count}")
    print(f"   All policies have complete 6-level workflow definitions")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed complete policies with all 6 workflow levels")
    parser.add_argument("--clear", action="store_true", help="Clear existing policies before seeding")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000002", help="Tenant ID")
    
    args = parser.parse_args()
    
    tenant_id = UUID(args.tenant_id)
    
    db = SessionLocal()
    try:
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant {tenant_id} not found")
            return
        
        seed_complete_policies(tenant_id, db, clear_existing=args.clear)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
