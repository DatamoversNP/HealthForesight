#!/bin/bash
# Migrate existing policies, baselines, and other data to the correct storage location

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🔄 Migrating Existing Data to Local Storage"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Default tenant ID (demo tenant)
TENANT_ID="00000000-0000-0000-0000-000000000001"
TENANT_ID_2="00000000-0000-0000-0000-000000000002"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

echo "📦 Step 1: Migrating Policies..."
echo ""

# Create Python script to migrate policies
python3 << 'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path
from uuid import UUID

script_dir = Path("/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution")
data_dir = script_dir / "data"
tenant_id = "00000000-0000-0000-0000-000000000001"
tenant_id_2 = "00000000-0000-0000-0000-000000000002"

# Target location for policies (where the API expects them)
target_file = Path(f"/tmp/policies_{tenant_id}.json")
target_file_2 = Path(f"/tmp/policies_{tenant_id_2}.json")

# Collect all policies
all_policies = []

# 1. Load from valid_policies.json (tenant 2)
valid_policies_file = data_dir / "valid_policies.json"
if valid_policies_file.exists():
    print(f"   📄 Loading from {valid_policies_file.name}...")
    try:
        with open(valid_policies_file, 'r') as f:
            data = json.load(f)
            policies = data.get('policies', [])
            print(f"   ✅ Found {len(policies)} policies in valid_policies.json")
            all_policies.extend(policies)
    except Exception as e:
        print(f"   ⚠️  Error loading valid_policies.json: {e}")

# 2. Load individual policy files (tenant 1)
policy_files = list(data_dir.glob("policy_*.json"))
for policy_file in policy_files:
    if policy_file.name in ["valid_policies.json", "canonical_policies.json", "policies_00000000-0000-0000-0000-000000000002.json"]:
        continue
    try:
        with open(policy_file, 'r') as f:
            policy = json.load(f)
            if isinstance(policy, dict) and 'policy_id' in policy:
                print(f"   📄 Loading {policy_file.name}...")
                all_policies.append(policy)
    except Exception as e:
        print(f"   ⚠️  Error loading {policy_file.name}: {e}")

# 3. Load from policies_00000000-0000-0000-0000-000000000002.json
policies_file_2 = data_dir / "policies_00000000-0000-0000-0000-000000000002.json"
if policies_file_2.exists():
    print(f"   📄 Loading from {policies_file_2.name}...")
    try:
        with open(policies_file_2, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'policies' in data:
                policies = data.get('policies', [])
                print(f"   ✅ Found {len(policies)} policies")
                all_policies.extend(policies)
            elif isinstance(data, list):
                print(f"   ✅ Found {len(data)} policies")
                all_policies.extend(data)
    except Exception as e:
        print(f"   ⚠️  Error loading policies file: {e}")

# Separate policies by tenant
tenant_1_policies = []
tenant_2_policies = []

for policy in all_policies:
    policy_tenant = str(policy.get('tenant_id', tenant_id))
    if policy_tenant == tenant_id_2:
        tenant_2_policies.append(policy)
    else:
        tenant_1_policies.append(policy)

# Save tenant 1 policies
if tenant_1_policies:
    print(f"\n   💾 Saving {len(tenant_1_policies)} policies for tenant {tenant_id}...")
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, 'w') as f:
        json.dump({
            'tenant_id': tenant_id,
            'updated_at': '2026-01-12T00:00:00',
            'policies': tenant_1_policies
        }, f, indent=2, default=str)
    print(f"   ✅ Saved to {target_file}")

# Save tenant 2 policies
if tenant_2_policies:
    print(f"\n   💾 Saving {len(tenant_2_policies)} policies for tenant {tenant_id_2}...")
    target_file_2.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file_2, 'w') as f:
        json.dump({
            'tenant_id': tenant_id_2,
            'updated_at': '2026-01-12T00:00:00',
            'policies': tenant_2_policies
        }, f, indent=2, default=str)
    print(f"   ✅ Saved to {target_file_2}")

print(f"\n✅ Policy migration complete!")
print(f"   Total policies found: {len(all_policies)}")
print(f"   Tenant 1 ({tenant_id}): {len(tenant_1_policies)} policies")
print(f"   Tenant 2 ({tenant_id_2}): {len(tenant_2_policies)} policies")

PYTHON_SCRIPT

echo ""
echo "📦 Step 2: Verifying data directories..."
echo ""

# Ensure data directories exist
mkdir -p "$SCRIPT_DIR/data/policies"
mkdir -p "$SCRIPT_DIR/data/baselines"
mkdir -p "$SCRIPT_DIR/data/analyses"
mkdir -p "$SCRIPT_DIR/data/observations"
mkdir -p "$SCRIPT_DIR/data/scorecards"

echo "✅ Data directories ready"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Migration Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next Steps:"
echo "   1. Restart the API server: ./START_API_NOW.sh"
echo "   2. Refresh your browser at http://localhost:3050"
echo "   3. Your policies, baselines, and other data should now appear!"
echo ""
