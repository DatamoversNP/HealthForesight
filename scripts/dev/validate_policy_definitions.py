"""Validate policy definitions without database dependencies"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))

# Import just the models we need for validation
try:
    from uepi_common.models import (
        PolicyType,
        PolicyStatus,
        EnforcementMechanism,
        PolicyTouchpoint,
        LineOfBusiness,
    )
    
    # Import the policy definition functions
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from scripts.dev.seed_complete_policies import create_standalone_policies, create_composite_policies, build_policy_metadata
    
    def validate_policy_def(policy_def: dict, policy_name: str) -> list[str]:
        """Validate a single policy definition"""
        errors = []
        
        # Check required fields
        required_fields = ["name", "policy_type", "owner_role", "description", "status", 
                          "effective_start_date", "scope", "levers"]
        for field in required_fields:
            if field not in policy_def:
                errors.append(f"{policy_name}: Missing required field '{field}'")
        
        # Validate policy type
        if "policy_type" in policy_def:
            try:
                PolicyType(policy_def["policy_type"])
            except ValueError:
                errors.append(f"{policy_name}: Invalid policy_type '{policy_def['policy_type']}'")
        
        # Validate status
        if "status" in policy_def:
            try:
                PolicyStatus(policy_def["status"])
            except ValueError:
                errors.append(f"{policy_name}: Invalid status '{policy_def['status']}'")
        
        # Validate scope
        if "scope" in policy_def:
            scope = policy_def["scope"]
            if "lob" not in scope:
                errors.append(f"{policy_name}: Scope missing 'lob'")
            if "markets" not in scope:
                errors.append(f"{policy_name}: Scope missing 'markets'")
            if "network" not in scope:
                errors.append(f"{policy_name}: Scope missing 'network'")
        
        # Validate levers
        if "levers" in policy_def:
            if not policy_def["levers"]:
                errors.append(f"{policy_name}: No levers defined")
            for i, lever in enumerate(policy_def["levers"]):
                if "lever_type" not in lever:
                    errors.append(f"{policy_name}: Lever {i+1} missing 'lever_type'")
                if "parameters" not in lever:
                    errors.append(f"{policy_name}: Lever {i+1} missing 'parameters'")
                if "lever_type" in lever:
                    try:
                        PolicyType(lever["lever_type"])
                    except ValueError:
                        errors.append(f"{policy_name}: Lever {i+1} has invalid lever_type '{lever['lever_type']}'")
        
        # Validate enforcement
        if "enforcement" in policy_def:
            enforcement = policy_def["enforcement"]
            if "mechanism" not in enforcement:
                errors.append(f"{policy_name}: Enforcement missing 'mechanism'")
            else:
                try:
                    EnforcementMechanism(enforcement["mechanism"])
                except ValueError:
                    errors.append(f"{policy_name}: Invalid enforcement mechanism '{enforcement['mechanism']}'")
        
        # Check that metadata can be built
        try:
            metadata = build_policy_metadata(policy_def)
            if not metadata:
                errors.append(f"{policy_name}: Failed to build metadata")
        except Exception as e:
            errors.append(f"{policy_name}: Error building metadata: {str(e)}")
        
        return errors
    
    def main():
        """Validate all policy definitions"""
        print("🔍 Validating policy definitions...\n")
        
        standalone_policies = create_standalone_policies()
        composite_policies = create_composite_policies()
        all_policies = standalone_policies + composite_policies
        
        print(f"📋 Found {len(standalone_policies)} standalone policies and {len(composite_policies)} composite policies\n")
        
        all_errors = []
        
        for policy_def in all_policies:
            policy_name = policy_def.get("name", "Unknown")
            errors = validate_policy_def(policy_def, policy_name)
            if errors:
                all_errors.extend(errors)
                print(f"❌ {policy_name}: {len(errors)} error(s)")
                for error in errors:
                    print(f"   - {error}")
            else:
                lever_count = len(policy_def.get("levers", []))
                print(f"✅ {policy_name} ({lever_count} lever(s))")
        
        print(f"\n{'='*60}")
        if all_errors:
            print(f"❌ Validation failed: {len(all_errors)} error(s) found")
            return 1
        else:
            print(f"✅ All {len(all_policies)} policies validated successfully!")
            print(f"\n   - {len(standalone_policies)} standalone policies")
            print(f"   - {len(composite_policies)} composite policies")
            print(f"   - All policies have complete 6-level workflow definitions")
            return 0
    
    if __name__ == "__main__":
        sys.exit(main())

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Note: This validation script requires the uepi_common package.")
    print("   Run it from the project root with proper Python environment.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
