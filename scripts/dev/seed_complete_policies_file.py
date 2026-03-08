"""
Seed complete policies with all 6 workflow levels defined - FILE-BASED VERSION
- Standalone policies (single lever)
- Composite policies (multiple levers)
- All policies have complete: Basic Info, Scope, Levers, Conditions, Exceptions, Review metadata
- Uses file-based storage (JSON files) - no database required
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

from uepi_common.models import (
    PolicyType,
    PolicyStatus,
    CanonicalPolicy,
    PolicyScope,
    EffectivePeriod,
    Enforcement,
    PolicyLever,
    EnforcementMechanism,
    PolicyTouchpoint,
    LineOfBusiness,
)

# Import policy definitions from the original script
from scripts.dev.seed_complete_policies import create_standalone_policies, create_composite_policies


def build_canonical_policy(policy_def: dict, policy_id: UUID) -> CanonicalPolicy:
    """Build CanonicalPolicy from policy definition"""
    
    # Build PolicyScope
    scope = PolicyScope(
        lob=[LineOfBusiness(lob) for lob in policy_def["scope"]["lob"]],
        markets=policy_def["scope"]["markets"],
        network=policy_def["scope"]["network"]
    )
    
    # Build EffectivePeriod
    effective_period = EffectivePeriod(
        start_date=policy_def["effective_start_date"],
        end_date=None
    )
    
    # Build Enforcement
    enforcement = Enforcement(
        mechanism=EnforcementMechanism(policy_def["enforcement"]["mechanism"]),
        touchpoint=[PolicyTouchpoint(tp) for tp in policy_def["enforcement"]["touchpoint"]],
        override_allowed=policy_def["enforcement"]["override_allowed"]
    )
    
    # Build Policy Levers
    policy_levers = []
    for lever_def in policy_def["levers"]:
        policy_levers.append(
            PolicyLever(
                lever_type=PolicyType(lever_def["lever_type"]),
                parameters=lever_def["parameters"]
            )
        )
    
    # Build CanonicalPolicy
    return CanonicalPolicy(
        policy_id=policy_id,
        policy_name=policy_def["name"],
        policy_type=PolicyType(policy_def["policy_type"]),
        description=policy_def["description"],
        status=PolicyStatus(policy_def["status"]),
        effective_period=effective_period,
        scope=scope,
        enforcement=enforcement,
        policy_levers=policy_levers,
    )


def load_existing_policies(tenant_id: UUID, data_dir: Path) -> dict:
    """Load existing policies from JSON file"""
    policies_file = data_dir / f"policies_{tenant_id}.json"
    
    if policies_file.exists():
        try:
            with open(policies_file, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing policies: {e}")
    
    return {
        "tenant_id": str(tenant_id),
        "updated_at": datetime.utcnow().isoformat(),
        "policies": []
    }


def save_policies(tenant_id: UUID, policies_data: dict, data_dir: Path):
    """Save policies to JSON file"""
    data_dir.mkdir(parents=True, exist_ok=True)
    policies_file = data_dir / f"policies_{tenant_id}.json"
    
    policies_data["updated_at"] = datetime.utcnow().isoformat()
    
    with open(policies_file, 'w') as f:
        json.dump(policies_data, f, indent=2, default=str)
    
    print(f"✅ Saved policies to {policies_file}")


def seed_complete_policies_file(tenant_id: UUID, data_dir: Path = None, clear_existing: bool = False):
    """Seed complete policies using file-based storage"""
    
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent / "data"
    
    data_dir = Path(data_dir)
    
    # Load existing policies
    if clear_existing:
        print("⚠️  Clearing existing policies...")
        policies_data = {
            "tenant_id": str(tenant_id),
            "updated_at": datetime.utcnow().isoformat(),
            "policies": []
        }
    else:
        policies_data = load_existing_policies(tenant_id, data_dir)
    
    # Get all policy definitions
    standalone_policies = create_standalone_policies()
    composite_policies = create_composite_policies()
    all_policies = standalone_policies + composite_policies
    
    print(f"\n📋 Creating {len(all_policies)} complete policies:")
    print(f"   - {len(standalone_policies)} standalone (single lever)")
    print(f"   - {len(composite_policies)} composite (multiple levers)")
    
    existing_policies = {p.get("policy_name"): p for p in policies_data.get("policies", [])}
    created_count = 0
    updated_count = 0
    
    for policy_def in all_policies:
        policy_name = policy_def["name"]
        
        # Check if policy already exists
        existing = existing_policies.get(policy_name)
        
        # Generate policy ID
        if existing:
            policy_id = UUID(existing["policy_id"])
        else:
            policy_id = uuid4()
        
        # Build CanonicalPolicy
        try:
            canonical_policy = build_canonical_policy(policy_def, policy_id)
            policy_dict = canonical_policy.model_dump(mode='json')
        except Exception as e:
            print(f"❌ Error building policy '{policy_name}': {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # Update policies list
        policies_list = policies_data.get("policies", [])
        
        if existing:
            # Update existing
            for i, p in enumerate(policies_list):
                if p.get("policy_name") == policy_name:
                    policies_list[i] = policy_dict
                    updated_count += 1
                    lever_count = len(policy_def["levers"])
                    print(f"   ✅ Updated: {policy_name} ({lever_count} lever(s))")
                    break
        else:
            # Add new
            policies_list.append(policy_dict)
            created_count += 1
            lever_count = len(policy_def["levers"])
            print(f"   ✅ Created: {policy_name} ({lever_count} lever(s))")
    
    policies_data["policies"] = policies_list
    
    # Save to file
    save_policies(tenant_id, policies_data, data_dir)
    
    print(f"\n✅ Complete! Created {created_count}, Updated {updated_count}")
    print(f"   Total policies: {created_count + updated_count}")
    print(f"   All policies have complete 6-level workflow definitions")
    print(f"   File: {data_dir / f'policies_{tenant_id}.json'}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed complete policies with file-based storage")
    parser.add_argument("--clear", action="store_true", help="Clear existing policies before seeding")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000002", help="Tenant ID")
    parser.add_argument("--data-dir", type=str, default=None, help="Data directory (default: data/)")
    
    args = parser.parse_args()
    
    tenant_id = UUID(args.tenant_id)
    data_dir = Path(args.data_dir) if args.data_dir else None
    
    try:
        seed_complete_policies_file(tenant_id, data_dir=data_dir, clear_existing=args.clear)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
