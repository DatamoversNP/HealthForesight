#!/usr/bin/env python3
"""
Merge metadata (assumptions, guardrails, versions) from data/policy_*.json 
into apps/api/data/policies/policy-*.json files
"""
import json
from pathlib import Path
from uuid import UUID
import hashlib

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
API_POLICIES_DIR = PROJECT_ROOT / "apps" / "api" / "data" / "policies"

def convert_policy_id_to_uuid(policy_id: str) -> UUID:
    """Convert string policy ID to UUID (same logic as API)"""
    try:
        return UUID(policy_id)
    except ValueError:
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())

def find_policy_by_uuid(uuid_str: str, data_policies: dict) -> dict:
    """Find policy in data/policy_*.json by UUID"""
    uuid_obj = UUID(uuid_str)
    for policy_file in DATA_DIR.glob("policy_*.json"):
        try:
            with open(policy_file, 'r') as f:
                policy = json.load(f)
                policy_id = policy.get('policy_id') or policy.get('id')
                if policy_id:
                    policy_uuid = convert_policy_id_to_uuid(str(policy_id))
                    if policy_uuid == uuid_obj:
                        return policy
        except Exception as e:
            print(f"  ⚠ Error reading {policy_file.name}: {e}")
    return None

def merge_metadata(api_policy: dict, data_policy: dict) -> bool:
    """Merge metadata from data_policy into api_policy. Returns True if merged."""
    if not data_policy:
        return False
    
    data_metadata = data_policy.get('metadata', {})
    if not data_metadata:
        return False
    
    # Get metadata to merge
    assumptions = data_metadata.get('assumptions', [])
    guardrails = data_metadata.get('guardrails', [])
    versions = data_metadata.get('versions', [])
    changelog = data_metadata.get('changelog', [])
    
    if not (assumptions or guardrails or versions or changelog):
        return False
    
    # Initialize metadata in api_policy if needed
    if 'metadata' not in api_policy:
        api_policy['metadata'] = {}
    
    # Merge metadata (only if not already present or if data_policy has more)
    merged = False
    if assumptions and len(assumptions) > len(api_policy['metadata'].get('assumptions', [])):
        api_policy['metadata']['assumptions'] = assumptions
        merged = True
    if guardrails and len(guardrails) > len(api_policy['metadata'].get('guardrails', [])):
        api_policy['metadata']['guardrails'] = guardrails
        merged = True
    if versions and len(versions) > len(api_policy['metadata'].get('versions', [])):
        api_policy['metadata']['versions'] = versions
        merged = True
    if changelog and len(changelog) > len(api_policy['metadata'].get('changelog', [])):
        api_policy['metadata']['changelog'] = changelog
        merged = True
    
    return merged

def main():
    print("🔄 Merging metadata into apps/api/data/policies/ files...")
    print("=" * 70)
    
    if not API_POLICIES_DIR.exists():
        print(f"❌ Directory not found: {API_POLICIES_DIR}")
        return
    
    policy_files = list(API_POLICIES_DIR.glob("policy-*.json"))
    print(f"Found {len(policy_files)} policy files in apps/api/data/policies/")
    print()
    
    merged_count = 0
    skipped_count = 0
    
    for policy_file in policy_files:
        try:
            # Extract UUID from filename (policy-UUID.json)
            uuid_str = policy_file.stem.replace('policy-', '')
            
            # Load API policy file
            with open(policy_file, 'r') as f:
                api_policy = json.load(f)
            
            # Get policy_id and name from API policy file
            api_policy_id = api_policy.get('policy_id') or api_policy.get('id')
            api_policy_name = api_policy.get('policy_name') or api_policy.get('name', '')
            
            # Try to find matching policy in data/policy_*.json
            data_policy = None
            
            # 1. Try by UUID/string ID match
            if api_policy_id:
                for data_file in DATA_DIR.glob("policy_*.json"):
                    try:
                        with open(data_file, 'r') as f2:
                            p = json.load(f2)
                            p_id = p.get('policy_id') or p.get('id')
                            if p_id and str(p_id) == str(api_policy_id):
                                data_policy = p
                                break
                    except Exception:
                        continue
            
            # 2. If not found, try by UUID conversion
            if not data_policy:
                data_policy = find_policy_by_uuid(uuid_str, {})
            
            # 3. If still not found, try by policy name (exact match)
            if not data_policy and api_policy_name:
                for data_file in DATA_DIR.glob("policy_*.json"):
                    try:
                        with open(data_file, 'r') as f2:
                            p = json.load(f2)
                            p_name = p.get('policy_name') or p.get('name', '')
                            if p_name and p_name.strip() == api_policy_name.strip():
                                data_policy = p
                                break
                    except Exception:
                        continue
            
            if data_policy:
                # Merge metadata
                if merge_metadata(api_policy, data_policy):
                    # Save updated policy
                    with open(policy_file, 'w') as f:
                        json.dump(api_policy, f, indent=2)
                    
                    metadata = api_policy.get('metadata', {})
                    print(f"✅ {policy_file.name}")
                    print(f"   Assumptions: {len(metadata.get('assumptions', []))}")
                    print(f"   Guardrails: {len(metadata.get('guardrails', []))}")
                    print(f"   Versions: {len(metadata.get('versions', []))}")
                    print(f"   Changelog: {len(metadata.get('changelog', []))}")
                    merged_count += 1
                else:
                    skipped_count += 1
            else:
                print(f"⚠️  {policy_file.name} - No matching policy found in data/")
                skipped_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {policy_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 70)
    print(f"✅ Merged metadata into {merged_count} files")
    print(f"⚠️  Skipped {skipped_count} files")
    print()
    print("Next: Deploy with ./START_PRODUCTION_BUILD.sh")

if __name__ == "__main__":
    main()

