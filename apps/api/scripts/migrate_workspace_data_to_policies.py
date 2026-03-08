#!/usr/bin/env python3
"""
Migrate workspace data from separate files into policy files
This script reads assumptions, guardrails, versions, and changelog from separate directories
and embeds them into the policy files' metadata
"""
import json
from pathlib import Path
from uuid import UUID
from datetime import datetime

BASE_PATH = Path(__file__).parent.parent.parent.parent / "data"
TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def convert_policy_id_to_uuid(policy_id: str) -> UUID:
    """Convert string policy ID to UUID"""
    try:
        return UUID(policy_id)
    except ValueError:
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())


def migrate_assumptions(policy_file: Path, policy_data: dict):
    """Migrate assumptions from separate file to policy metadata"""
    policy_id_str = policy_data.get('policy_id') or policy_data.get('id')
    if not policy_id_str:
        return 0
    
    policy_uuid = convert_policy_id_to_uuid(str(policy_id_str))
    assumptions_file = BASE_PATH / "policy_assumptions" / str(TENANT_ID) / f"policy-{policy_uuid}.json"
    
    if not assumptions_file.exists():
        return 0
    
    try:
        with open(assumptions_file, 'r') as f:
            assumptions_data = json.load(f)
            assumptions = assumptions_data.get("assumptions", [])
        
        if assumptions:
            if "metadata" not in policy_data:
                policy_data["metadata"] = {}
            policy_data["metadata"]["assumptions"] = assumptions
            return len(assumptions)
    except Exception as e:
        print(f"  ⚠ Error loading assumptions: {e}")
        return 0
    
    return 0


def migrate_guardrails(policy_file: Path, policy_data: dict):
    """Migrate guardrails from separate file to policy metadata"""
    policy_id_str = policy_data.get('policy_id') or policy_data.get('id')
    if not policy_id_str:
        return 0
    
    policy_uuid = convert_policy_id_to_uuid(str(policy_id_str))
    guardrails_file = BASE_PATH / "policy_guardrails" / str(TENANT_ID) / f"policy-{policy_uuid}.json"
    
    if not guardrails_file.exists():
        return 0
    
    try:
        with open(guardrails_file, 'r') as f:
            guardrails_data = json.load(f)
            guardrails = guardrails_data.get("guardrails", [])
        
        if guardrails:
            if "metadata" not in policy_data:
                policy_data["metadata"] = {}
            policy_data["metadata"]["guardrails"] = guardrails
            return len(guardrails)
    except Exception as e:
        print(f"  ⚠ Error loading guardrails: {e}")
        return 0
    
    return 0


def migrate_versions(policy_file: Path, policy_data: dict):
    """Migrate versions from separate files to policy metadata"""
    policy_id_str = policy_data.get('policy_id') or policy_data.get('id')
    if not policy_id_str:
        return 0
    
    policy_uuid = convert_policy_id_to_uuid(str(policy_id_str))
    versions_dir = BASE_PATH / "policy_versions" / str(TENANT_ID) / f"policy-{policy_uuid}"
    
    if not versions_dir.exists():
        return 0
    
    versions = []
    try:
        # Read versions index
        index_file = versions_dir / "versions_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                index_data = json.load(f)
                version_infos = index_data.get("versions", [])
            
            # Load each version file
            for version_info in version_infos:
                version_number = version_info.get("version_number")
                if version_number:
                    version_file = versions_dir / f"version-{version_number}.json"
                    if version_file.exists():
                        with open(version_file, 'r') as vf:
                            version_data = json.load(vf)
                            versions.append(version_data)
        
        if versions:
            # Sort by version number
            versions.sort(key=lambda v: v.get("version_number", 0), reverse=True)
            if "metadata" not in policy_data:
                policy_data["metadata"] = {}
            policy_data["metadata"]["versions"] = versions
            return len(versions)
    except Exception as e:
        print(f"  ⚠ Error loading versions: {e}")
        return 0
    
    return 0


def migrate_changelog(policy_file: Path, policy_data: dict):
    """Migrate changelog from separate file to policy metadata"""
    policy_id_str = policy_data.get('policy_id') or policy_data.get('id')
    if not policy_id_str:
        return 0
    
    policy_uuid = convert_policy_id_to_uuid(str(policy_id_str))
    changelog_file = BASE_PATH / "policy_changelog" / str(TENANT_ID) / f"policy-{policy_uuid}.json"
    
    if not changelog_file.exists():
        return 0
    
    try:
        with open(changelog_file, 'r') as f:
            changelog_data = json.load(f)
            entries = changelog_data.get("entries", [])
        
        if entries:
            if "metadata" not in policy_data:
                policy_data["metadata"] = {}
            policy_data["metadata"]["changelog"] = entries
            return len(entries)
    except Exception as e:
        print(f"  ⚠ Error loading changelog: {e}")
        return 0
    
    return 0


def main():
    """Migrate workspace data into policy files"""
    print("🔄 Migrating workspace data into policy files")
    print("=" * 80)
    
    # Find all policy files
    policy_files = []
    for pattern in ["policy_*.json", "policies/*.json"]:
        policy_files.extend(BASE_PATH.glob(pattern))
    
    print(f"\n📋 Found {len(policy_files)} policy files\n")
    
    migrated_count = 0
    for policy_file in policy_files:
        try:
            with open(policy_file, 'r') as f:
                policy_data = json.load(f)
            
            policy_id_str = policy_data.get('policy_id') or policy_data.get('id')
            policy_name = policy_data.get('name') or policy_data.get('policy_name', 'Unknown')
            
            print(f"📌 Processing: {policy_name} ({policy_id_str})")
            
            # Migrate each type of workspace data
            assumptions_count = migrate_assumptions(policy_file, policy_data)
            guardrails_count = migrate_guardrails(policy_file, policy_data)
            versions_count = migrate_versions(policy_file, policy_data)
            changelog_count = migrate_changelog(policy_file, policy_data)
            
            # Save updated policy file
            if assumptions_count > 0 or guardrails_count > 0 or versions_count > 0 or changelog_count > 0:
                with open(policy_file, 'w') as f:
                    json.dump(policy_data, f, indent=2, default=str)
                
                print(f"  ✅ Migrated: {assumptions_count} assumptions, {guardrails_count} guardrails, {versions_count} versions, {changelog_count} changelog entries")
                migrated_count += 1
            else:
                print(f"  ⚠ No workspace data found")
            
        except Exception as e:
            print(f"  ✗ Error processing {policy_file}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"🎉 Migration complete! Updated {migrated_count} policy files")
    print("=" * 80)


if __name__ == "__main__":
    main()

