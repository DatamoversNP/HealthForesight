#!/usr/bin/env python3
"""
Update predefined policies to use comprehensive scope structure and ensure they're executable
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def update_policy_scope(scope: Dict[str, Any]) -> Dict[str, Any]:
    """Update scope to comprehensive structure"""
    # Ensure all scope fields are present with defaults
    updated_scope = {
        "lob": scope.get("lob", []) or [],
        "markets": scope.get("markets", []) or [],
        "network": scope.get("network", []) or [],
        "plans": scope.get("plans", []) or [],
        "product_types": scope.get("product_types", []) or [],
        "states": scope.get("states", []) or [],
        "regions": scope.get("regions", []) or [],
        "network_tiers": scope.get("network_tiers", []) or [],
        "member_age_min": scope.get("member_age_min"),
        "member_age_max": scope.get("member_age_max"),
        "exclude_pregnant": scope.get("exclude_pregnant"),
        "gender_filters": scope.get("gender_filters", []) or [],
        "exclude_centers_of_excellence": scope.get("exclude_centers_of_excellence"),
        "include_provider_types": scope.get("include_provider_types", []) or [],
        "exclude_provider_types": scope.get("exclude_provider_types", []) or [],
        "provider_specialties": scope.get("provider_specialties", []) or [],
        "exclude_er": scope.get("exclude_er"),
        "exclude_hospital_op": scope.get("exclude_hospital_op"),
        "allowed_sites": scope.get("allowed_sites", []) or [],
        "applies_to_all": scope.get("applies_to_all", False),
        "network_inclusion_mode": scope.get("network_inclusion_mode", "include"),
    }
    
    # Extract site-of-care exclusions from global_exceptions if present
    # This will be done in update_policy, but we include it here for completeness
    
    return updated_scope

def convert_lever_to_targets_format(lever: Dict[str, Any]) -> Dict[str, Any]:
    """Convert lever parameters to targets format if needed"""
    if "targets" in lever:
        return lever  # Already in correct format
    
    # Convert old parameters format to targets format
    parameters = lever.get("parameters", {})
    targets = {
        "code_type": parameters.get("code_type", "CPT"),
        "codes": parameters.get("codes", []),
        "code_groups": parameters.get("code_groups", []),
    }
    
    # Extract remaining config
    config = {k: v for k, v in parameters.items() if k not in ["code_type", "codes", "code_groups"]}
    
    return {
        "lever_type": lever.get("lever_type"),
        "targets": targets,
        "config": config if config else lever.get("config", {}),
        "apply_when": lever.get("apply_when", []),
        "exceptions": lever.get("exceptions", []),
        "priority": lever.get("priority", 1),
    }

def update_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    """Update a single policy to comprehensive structure"""
    updated = policy.copy()
    
    # Extract scope exclusions from global_exceptions and update scope
    if "global_exceptions" in updated and isinstance(updated["global_exceptions"], list):
        scope = updated.get("scope", {})
        for exception in updated["global_exceptions"]:
            if isinstance(exception, dict):
                exception_type = exception.get("type", "").upper()
                if "ER" in exception_type or "EMERGENCY" in exception_type:
                    scope["exclude_er"] = True
                if "PEDIATRIC" in exception_type or ("AGE" in exception_type and exception.get("parameters", {}).get("max_age") == 18):
                    scope["member_age_max"] = 18
    
    # Update scope
    updated["scope"] = update_policy_scope(updated.get("scope", {}))
    
    # Ensure enforcement is present
    if "enforcement" not in updated:
        updated["enforcement"] = {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": False,
        }
    
    # Update policy_levers to use targets format
    if "policy_levers" in updated and updated["policy_levers"]:
        updated["policy_levers"] = [
            convert_lever_to_targets_format(lever) if isinstance(lever, dict) else lever
            for lever in updated["policy_levers"]
        ]
    
    # Ensure logic structure exists (for backward compatibility and UI)
    if "logic" not in updated:
        updated["logic"] = {}
    updated["logic"]["scope"] = updated["scope"]
    if "policy_levers" not in updated["logic"]:
        updated["logic"]["policy_levers"] = updated.get("policy_levers", [])
    if "global_conditions" not in updated["logic"]:
        updated["logic"]["global_conditions"] = updated.get("apply_when", [])
    if "global_exceptions" not in updated["logic"]:
        updated["logic"]["global_exceptions"] = updated.get("global_exceptions", [])
    
    # Ensure metadata exists for UI compatibility
    if "metadata" not in updated:
        updated["metadata"] = {}
    updated["metadata"]["scope"] = updated["scope"]
    if "owner" not in updated["metadata"]:
        updated["metadata"]["owner"] = updated.get("owner_role", "UM_LEADER")
    
    # Ensure policy has required fields for execution
    if "created_at" not in updated:
        updated["created_at"] = datetime.utcnow().isoformat()
    
    return updated

def main():
    """Update policies file"""
    script_dir = Path(__file__).parent.parent
    policies_file = script_dir / "data" / "policies_00000000-0000-0000-0000-000000000002.json"
    
    if not policies_file.exists():
        print(f"ERROR: Policies file not found: {policies_file}")
        return
    
    print(f"Reading policies from: {policies_file}")
    with open(policies_file, 'r') as f:
        data = json.load(f)
    
    # Update all policies
    if "policies" in data and isinstance(data["policies"], list):
        updated_policies = []
        for policy in data["policies"]:
            updated = update_policy(policy)
            updated_policies.append(updated)
        
        data["policies"] = updated_policies
        data["updated_at"] = datetime.utcnow().isoformat()
        
        # Write back
        print(f"Writing updated policies to: {policies_file}")
        with open(policies_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Updated {len(updated_policies)} policies")
        
        # Also update /tmp copy if it exists
        tmp_file = Path("/tmp/policies_00000000-0000-0000-0000-000000000002.json")
        if tmp_file.exists():
            with open(tmp_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Updated /tmp copy")
    else:
        print("ERROR: Invalid policies file structure")

if __name__ == "__main__":
    main()
