#!/usr/bin/env python3
"""
Validate policies against CanonicalPolicy Pydantic model
This ensures all policies conform to the expected schema
"""
import json
import sys
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_common.models import CanonicalPolicy, PolicyLogic

policies_file = project_root / "data" / "valid_policies.json"


def validate_policy(policy_data, index):
    """Validate a single policy against CanonicalPolicy model"""
    errors = []
    warnings = []
    
    try:
        # Try to parse as CanonicalPolicy
        policy = CanonicalPolicy(**policy_data)
        
        # Additional validations
        if not policy.policy_logic:
            warnings.append("Policy has no policy_logic - may be legacy format")
        else:
            # Validate PolicyLogic structure (already parsed by CanonicalPolicy)
            logic = policy.policy_logic
            if not logic.levers:
                warnings.append("PolicyLogic has no levers")
            else:
                for i, lever in enumerate(logic.levers):
                    if not lever.targets.codes and not lever.targets.code_groups:
                        errors.append(f"Lever {i+1} has no target codes or code groups")
                    if not lever.lever_type:
                        errors.append(f"Lever {i+1} has no lever_type")
        
        # Check required fields
        if not policy.policy_name:
            errors.append("Missing policy_name")
        if not policy.policy_type:
            errors.append("Missing policy_type")
        if not policy.scope:
            errors.append("Missing scope")
        if not policy.effective_period:
            errors.append("Missing effective_period")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "policy": policy,
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Pydantic validation error: {str(e)}"],
            "warnings": warnings,
            "policy": None,
        }


def main():
    """Validate all policies in the JSON file"""
    print("🔍 Validating policies against CanonicalPolicy schema...")
    print(f"   File: {policies_file}")
    print("")
    
    if not policies_file.exists():
        print(f"❌ Policies file not found: {policies_file}")
        print("   Run: python3 scripts/dev/create_policies_json.py first")
        return 1
    
    with open(policies_file) as f:
        data = json.load(f)
    
    policies = data.get("policies", [])
    if not policies:
        print(f"❌ No policies found in {policies_file}")
        return 1
    
    print(f"📦 Found {len(policies)} policies to validate")
    print("")
    
    # Validate each policy
    results = []
    for i, policy_data in enumerate(policies, 1):
        policy_name = policy_data.get("policy_name", f"Policy {i}")
        print(f"[{i}/{len(policies)}] Validating: {policy_name}")
        
        result = validate_policy(policy_data, i)
        result["name"] = policy_name
        result["index"] = i
        results.append(result)
        
        if result["valid"]:
            status = "✅ Valid"
            if result["warnings"]:
                status += " (with warnings)"
            print(f"   {status}")
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"      ⚠️  {warning}")
        else:
            print(f"   ❌ Invalid")
            for error in result["errors"]:
                print(f"      ❌ {error}")
        print("")
    
    # Summary
    print("=" * 70)
    valid_count = sum(1 for r in results if r["valid"])
    invalid_count = len(results) - valid_count
    warning_count = sum(1 for r in results if r["warnings"])
    
    print(f"📊 Validation Summary:")
    print(f"   ✅ Valid: {valid_count}/{len(results)}")
    if invalid_count > 0:
        print(f"   ❌ Invalid: {invalid_count}/{len(results)}")
    if warning_count > 0:
        print(f"   ⚠️  Warnings: {warning_count} policies")
    print("")
    
    if invalid_count > 0:
        print("❌ Invalid policies:")
        for r in results:
            if not r["valid"]:
                print(f"   - {r['name']}:")
                for error in r["errors"]:
                    print(f"     • {error}")
        print("")
    
    if warning_count > 0:
        print("⚠️  Policies with warnings:")
        for r in results:
            if r["warnings"]:
                print(f"   - {r['name']}:")
                for warning in r["warnings"]:
                    print(f"     • {warning}")
        print("")
    
    if valid_count == len(results):
        print("✅ All policies are valid against CanonicalPolicy schema!")
        return 0
    else:
        print("❌ Some policies failed validation")
        return 1


if __name__ == "__main__":
    sys.exit(main())

