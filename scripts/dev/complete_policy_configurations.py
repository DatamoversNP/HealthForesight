"""Complete policy configurations - Add missing levers, scope, conditions, exceptions to all policies"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))

from sqlalchemy.orm import Session

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy, PolicyVersion, PolicyCodeSet


def get_default_scope():
    """Get default scope configuration"""
    return {
        "lob": ["COMMERCIAL"],
        "markets": ["ALL"],
        "network": ["IN"]
    }


def get_default_effective_period():
    """Get default effective period"""
    return {
        "start_date": datetime.now().isoformat(),
        "end_date": None
    }


def get_default_levers_for_policy_type(policy_type: str, policy_codes: list[str] = None) -> list[dict]:
    """Get default policy levers based on policy type"""
    
    # Default codes if none provided
    if not policy_codes:
        policy_codes = ["72148", "72149"]  # Default MRI codes
    
    policy_type_upper = policy_type.upper()
    
    if policy_type_upper in ["PRIOR_AUTH", "PA"]:
        return [{
            "lever_type": "PRIOR_AUTH",
            "parameters": {
                "requires_pa": True,
                "pa_touchpoint": "PA_WORKFLOW",
                "override_allowed": False,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],  # Limit to first 5 codes
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["SITE_OF_CARE"]:
        return [{
            "lever_type": "SITE_OF_CARE",
            "parameters": {
                "allowed_sites": ["FREESTANDING", "OFFICE"],
                "disallowed_sites": ["HOSPITAL_OP"],
                "redirect_to": "FREESTANDING",
                "deny_if_disallowed": False,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["DURATION_FREQUENCY_LIMIT", "FREQUENCY_LIMIT"]:
        return [{
            "lever_type": "DURATION_FREQUENCY_LIMIT",
            "parameters": {
                "max_visits": 20,
                "time_period": "YEAR",
                "reset_date": "CALENDAR_YEAR",
                "accumulate_across_providers": True,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["COST_SHARING"]:
        return [{
            "lever_type": "COST_SHARING",
            "parameters": {
                "copay": 75.0,
                "coinsurance": 0.0,
                "deductible_applies": False,
                "out_of_pocket_applies": True,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["NETWORK_RESTRICTION"]:
        return [{
            "lever_type": "NETWORK_RESTRICTION",
            "parameters": {
                "allowed_network": ["IN"],
                "oon_allowed": False,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["STEP_THERAPY"]:
        return [{
            "lever_type": "STEP_THERAPY",
            "parameters": {
                "requires_step_therapy": True,
                "steps": [],
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["COVERAGE"]:
        return [{
            "lever_type": "COVERAGE",
            "parameters": {
                "covered": True,
                "coverage_level": "STANDARD",
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    elif policy_type_upper in ["BENEFIT"]:
        return [{
            "lever_type": "COST_SHARING",
            "parameters": {
                "copay": 50.0,
                "coinsurance": 0.0,
                "deductible_applies": True,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]
    
    else:
        # Generic default lever
        return [{
            "lever_type": "PRIOR_AUTH",
            "parameters": {
                "requires_pa": True,
            },
            "targets": {
                "code_type": "CPT",
                "codes": policy_codes[:5],
                "code_groups": [],
            }
        }]


def get_policy_codes_from_version(db: Session, policy_id: UUID) -> list[str]:
    """Extract CPT codes from policy version code sets"""
    version = db.query(PolicyVersion).filter(
        PolicyVersion.policy_id == policy_id
    ).order_by(PolicyVersion.version_number.desc()).first()
    
    if not version:
        return []
    
    code_sets = db.query(PolicyCodeSet).filter(
        PolicyCodeSet.version_id == version.id,
        PolicyCodeSet.code_type == "CPT"
    ).all()
    
    return [cs.code for cs in code_sets]


def complete_policy_configurations(tenant_id: UUID = None):
    """Complete configurations for all policies"""
    db = SessionLocal()
    
    try:
        # Get all policies
        query = db.query(Policy)
        if tenant_id:
            query = query.filter(Policy.tenant_id == tenant_id)
        
        policies = query.all()
        
        print(f"Found {len(policies)} policies to process")
        
        updated_count = 0
        skipped_count = 0
        
        for policy in policies:
            try:
                metadata = policy.policy_metadata_json if hasattr(policy, 'policy_metadata_json') and policy.policy_metadata_json else {}
                
                # Check if policy already has complete configuration
                has_levers = metadata.get("policy_levers") and len(metadata.get("policy_levers", [])) > 0
                has_scope = metadata.get("scope")
                has_effective_period = metadata.get("effective_period")
                
                if has_levers and has_scope and has_effective_period:
                    print(f"⏭️  Skipping {policy.name} - already has complete configuration")
                    skipped_count += 1
                    continue
                
                # Get codes from policy version if available
                policy_codes = get_policy_codes_from_version(db, policy.id)
                
                # Add missing configurations
                needs_update = False
                
                # Add scope if missing
                if not has_scope:
                    metadata["scope"] = get_default_scope()
                    needs_update = True
                
                # Add effective period if missing
                if not has_effective_period:
                    # Try to get from policy version
                    version = db.query(PolicyVersion).filter(
                        PolicyVersion.policy_id == policy.id
                    ).order_by(PolicyVersion.version_number.desc()).first()
                    
                    if version and version.effective_start_date:
                        metadata["effective_period"] = {
                            "start_date": version.effective_start_date.isoformat() if hasattr(version.effective_start_date, 'isoformat') else str(version.effective_start_date),
                            "end_date": version.effective_end_date.isoformat() if version.effective_end_date and hasattr(version.effective_end_date, 'isoformat') else (str(version.effective_end_date) if version.effective_end_date else None)
                        }
                    else:
                        metadata["effective_period"] = get_default_effective_period()
                    needs_update = True
                
                # Add policy levers if missing
                if not has_levers:
                    levers = get_default_levers_for_policy_type(policy.policy_type, policy_codes)
                    metadata["policy_levers"] = levers
                    needs_update = True
                    print(f"  ➕ Added {len(levers)} policy lever(s) for {policy.name}")
                
                # Add empty conditions and exceptions if missing (for structure completeness)
                if "apply_when" not in metadata:
                    metadata["apply_when"] = []
                    needs_update = True
                
                if "global_exceptions" not in metadata:
                    metadata["global_exceptions"] = []
                    needs_update = True
                
                # Update policy if changes were made
                if needs_update:
                    policy.policy_metadata_json = metadata
                    db.commit()
                    print(f"✅ Updated {policy.name} (type: {policy.policy_type})")
                    updated_count += 1
                
            except Exception as e:
                print(f"❌ Error processing policy {policy.name}: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
                continue
        
        print(f"\n✅ Configuration completion finished!")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {len(policies)}")
        
    except Exception as e:
        print(f"❌ Error completing policy configurations: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete policy configurations")
    parser.add_argument("--tenant-id", type=str, help="Tenant ID (optional)")
    
    args = parser.parse_args()
    
    tenant_id = UUID(args.tenant_id) if args.tenant_id else None
    
    complete_policy_configurations(tenant_id)
