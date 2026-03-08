#!/bin/bash
# Migrate all policies from apps/api/data/policies and preserve predicted impact

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🔄 Migrating All Policies and Preserving Predicted Impact"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path
from uuid import UUID

script_dir = Path("/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution")
data_dir = script_dir / "data"
api_policies_dir = script_dir / "apps" / "api" / "data" / "policies"
tenant_id = "00000000-0000-0000-0000-000000000001"
target_file = Path(f"/tmp/policies_{tenant_id}.json")

print("📦 Step 1: Collecting all policies...\n")

all_policies = {}
policies_by_name = {}  # Track by name to deduplicate
policies_with_predicted = 0

# Helper to check if policy has predicted_impact
def has_predicted_impact(policy):
    return 'predicted_impact' in policy or (policy.get('metadata', {}).get('predicted_impact') is not None)

# Helper to merge policies (prefer version with predicted_impact)
def merge_policy(existing, new):
    # Prefer version with predicted_impact
    if has_predicted_impact(new) and not has_predicted_impact(existing):
        return new
    elif has_predicted_impact(existing) and not has_predicted_impact(new):
        return existing
    # If both or neither have predicted_impact, prefer UUID version (more standard)
    existing_is_uuid = isinstance(existing.get('policy_id'), str) and len(str(existing.get('policy_id'))) == 36
    new_is_uuid = isinstance(new.get('policy_id'), str) and len(str(new.get('policy_id'))) == 36
    if new_is_uuid and not existing_is_uuid:
        return new
    # Otherwise merge, preserving predicted_impact
    merged = {**existing, **new}
    if has_predicted_impact(existing) and 'predicted_impact' not in merged:
        merged['predicted_impact'] = existing.get('predicted_impact')
    if has_predicted_impact(existing.get('metadata', {})) and 'metadata' in existing:
        if 'metadata' not in merged:
            merged['metadata'] = {}
        if 'predicted_impact' not in merged['metadata']:
            merged['metadata']['predicted_impact'] = existing['metadata'].get('predicted_impact')
    return merged

# 1. Load from valid_policies.json
valid_file = data_dir / "valid_policies.json"
if valid_file.exists():
    print("   📄 Loading from valid_policies.json...")
    try:
        with open(valid_file, 'r') as f:
            data = json.load(f)
            for policy in data.get('policies', []):
                pid = policy.get('policy_id')
                pname = policy.get('policy_name', policy.get('name', ''))
                if pid:
                    if 'tenant_id' not in policy:
                        policy['tenant_id'] = tenant_id
                    pid_str = str(pid)
                    all_policies[pid_str] = policy
                    # Track by name for deduplication
                    if pname and pname in policies_by_name:
                        policies_by_name[pname] = merge_policy(policies_by_name[pname], policy)
                    elif pname:
                        policies_by_name[pname] = policy
                    if has_predicted_impact(policy):
                        policies_with_predicted += 1
        print(f"   ✅ Loaded {len(data.get('policies', []))} policies from valid_policies.json")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

# 2. Load from apps/api/data/policies (these might have predicted_impact)
if api_policies_dir.exists():
    print(f"\n   📄 Loading from apps/api/data/policies/...")
    count = 0
    for policy_file in api_policies_dir.glob("policy-*.json"):
        try:
            with open(policy_file, 'r') as f:
                policy = json.load(f)
                pid = policy.get('policy_id')
                if pid:
                    pid_str = str(pid)
                    # Set tenant_id if not present
                    if 'tenant_id' not in policy:
                        policy['tenant_id'] = tenant_id
                    
                    pname = policy.get('policy_name', policy.get('name', ''))
                    # Check if this is a duplicate by name
                    if pname and pname in policies_by_name:
                        # Merge with existing policy (prefer version with predicted_impact)
                        existing = policies_by_name[pname]
                        merged = merge_policy(existing, policy)
                        # Update both by ID and by name
                        existing_pid = str(existing.get('policy_id'))
                        if existing_pid in all_policies:
                            all_policies[existing_pid] = merged
                        all_policies[pid_str] = merged
                        policies_by_name[pname] = merged
                    else:
                        all_policies[pid_str] = policy
                        if pname:
                            policies_by_name[pname] = policy
                    
                    if 'predicted_impact' in policy or (policy.get('metadata', {}).get('predicted_impact') is not None):
                        policies_with_predicted += 1
                    count += 1
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Skipping {policy_file.name} (invalid JSON)")
        except Exception as e:
            print(f"   ⚠️  Error loading {policy_file.name}: {e}")
    print(f"   ✅ Loaded {count} policies from apps/api/data/policies/")

# 3. Load individual policy files from data/
print(f"\n   📄 Loading from data/policy_*.json...")
count = 0
for policy_file in data_dir.glob("policy_*.json"):
    if policy_file.name in ["valid_policies.json", "canonical_policies.json"]:
        continue
    try:
        with open(policy_file, 'r') as f:
            policy = json.load(f)
            pid = policy.get('policy_id')
            if pid:
                pid_str = str(pid)
                if 'tenant_id' not in policy:
                    policy['tenant_id'] = tenant_id
                
                # Merge if exists
                if pid_str in all_policies:
                    existing = all_policies[pid_str]
                    # Preserve predicted_impact
                    if 'predicted_impact' in policy and 'predicted_impact' not in existing:
                        existing['predicted_impact'] = policy['predicted_impact']
                    all_policies[pid_str] = {**existing, **policy}
                else:
                    all_policies[pid_str] = policy
                count += 1
    except Exception as e:
        print(f"   ⚠️  Error loading {policy_file.name}: {e}")
print(f"   ✅ Loaded {count} policies from individual files")

# Deduplicate by policy name (keep best version of each)
# Use policies_by_name to get unique policies
unique_policies = {}
for name, policy in policies_by_name.items():
    pid = str(policy.get('policy_id'))
    unique_policies[pid] = policy

# Convert to list
policies_list = list(unique_policies.values())

print(f"\n📊 Summary:")
print(f"   Total unique policies: {len(policies_list)}")
print(f"   Policies with predicted_impact: {policies_with_predicted}")

# Save to /tmp for API to find
print(f"\n💾 Saving to {target_file}...")
target_file.parent.mkdir(parents=True, exist_ok=True)
with open(target_file, 'w') as f:
    json.dump({
        'tenant_id': tenant_id,
        'updated_at': '2026-01-12T00:00:00',
        'policies': policies_list
    }, f, indent=2, default=str)

print(f"✅ Saved {len(policies_list)} policies to {target_file}")

# Also update valid_policies.json with tenant_id set correctly
print(f"\n💾 Updating valid_policies.json...")
if valid_file.exists():
    try:
        with open(valid_file, 'r') as f:
            data = json.load(f)
        # Update tenant_id on policies
        for policy in data.get('policies', []):
            if 'tenant_id' not in policy:
                policy['tenant_id'] = tenant_id
        # Save back
        with open(valid_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"✅ Updated valid_policies.json")
    except Exception as e:
        print(f"⚠️  Error updating valid_policies.json: {e}")

print("\n✅ Migration complete!")

PYTHON_SCRIPT

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ All Policies Migrated!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next Steps:"
echo "   1. Restart the API server: ./START_API_NOW.sh"
echo "   2. Refresh your browser at http://localhost:3050/policies"
echo "   3. All policies and predicted impact should now appear!"
echo ""
