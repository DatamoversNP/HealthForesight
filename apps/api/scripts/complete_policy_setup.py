#!/usr/bin/env python3
"""
Complete policy setup script:
1. Seeds all 32 policies if not already present
2. Verifies policies are accessible via API
"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_policies import list_policies, create_policy
from uepi_api.storage_auth import DEFAULT_TENANT_ID

def main():
    """Seed all 32 policies"""
    print("=" * 80)
    print("🚀 COMPLETE POLICY SETUP")
    print("=" * 80)
    
    # Check existing policies
    existing_policies = list_policies(DEFAULT_TENANT_ID)
    print(f"\n📋 Found {len(existing_policies)} existing policies")
    
    if len(existing_policies) >= 32:
        print("✅ All 32 policies are already seeded!")
        for i, policy in enumerate(existing_policies[:5], 1):
            print(f"   {i}. {policy.get('name', 'Unknown')} ({policy.get('id', 'no-id')})")
        if len(existing_policies) > 5:
            print(f"   ... and {len(existing_policies) - 5} more")
        return 0
    
    # Import and run seed_all_32_policies
    try:
        seed_script = current_dir / "scripts" / "seed_all_32_policies.py"
        if not seed_script.exists():
            print(f"❌ Seed script not found: {seed_script}")
            return 1
        
        print(f"\n📦 Running seed_all_32_policies.py...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(seed_script)],
            cwd=str(current_dir),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Seed script failed:")
            print(result.stderr)
            return 1
        
        print(result.stdout)
        
        # Verify policies were created
        final_policies = list_policies(DEFAULT_TENANT_ID)
        print(f"\n✅ Policy seeding complete! Total policies: {len(final_policies)}")
        
        if len(final_policies) >= 32:
            print("✅ All 32 policies are now available!")
        else:
            print(f"⚠️  Expected 32 policies, but found {len(final_policies)}")
        
        return 0
    except Exception as e:
        print(f"❌ Error running seed script: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
