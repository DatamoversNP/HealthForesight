#!/usr/bin/env python3
"""
Step 3: Seed Predefined Policies
- Loads policies from seed_policies.py
- Creates policies in database (skips if already exist)
- Reports creation status
"""
import os
import sys
import logging
import importlib.util
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ.setdefault('USE_FILE_STORAGE', 'false')
os.environ.setdefault('LOG_LEVEL', 'INFO')


def main():
    """Seed predefined policies"""
    logger.info("=" * 80)
    logger.info("STEP 3: Seed Predefined Policies")
    logger.info("=" * 80)
    
    try:
        from uepi_api.storage_policies import create_policy, list_policies
        from uepi_api.storage_auth import DEFAULT_TENANT_ID
        
        # Load policies from seed_policies.py
        policies_file = current_dir / "scripts" / "seed_policies.py"
        if not policies_file.exists():
            logger.warning(f"⚠️  Policies file not found: {policies_file}")
            return 1
        
        # Import the policies
        spec = importlib.util.spec_from_file_location("seed_policies", policies_file)
        seed_policies_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_policies_module)
        POLICIES = seed_policies_module.POLICIES
        
        logger.info(f"📋 Found {len(POLICIES)} predefined policies")
        
        # Check existing policies
        existing_policies = list_policies(DEFAULT_TENANT_ID)
        existing_policy_ids = {p.get('policy_id') for p in existing_policies if p.get('policy_id')}
        logger.info(f"📊 Found {len(existing_policies)} existing policies in database")
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for policy_data in POLICIES:
            policy_id = policy_data.get('policy_id')
            policy_name = policy_data.get('policy_name', 'Unknown')
            
            if policy_id in existing_policy_ids:
                logger.debug(f"⏭️  Skipping existing policy: {policy_name} ({policy_id})")
                skipped_count += 1
                continue
            
            try:
                logger.info(f"📝 Creating policy: {policy_name} ({policy_id})")
                
                # Convert policy_data to format expected by create_policy
                policy_dict = {
                    'name': policy_name,
                    'policy_type': policy_data.get('policy_type', 'PRIOR_AUTH'),
                    'description': policy_data.get('description', ''),
                    'status': policy_data.get('status', 'ACTIVE'),
                    'scope': policy_data.get('scope', {}),
                    'effective_period': policy_data.get('effective_period', {}),
                    'enforcement': policy_data.get('enforcement', {}),
                    'policy_levers': policy_data.get('policy_levers', []),
                    'expected_behavioral_response': policy_data.get('expected_behavioral_response', []),
                    'analytics_expectations': policy_data.get('analytics_expectations', {}),
                    'ui_hints': policy_data.get('ui_hints', {}),
                }
                
                # Store policy_id in metadata for lookup
                policy_dict['metadata'] = {
                    'policy_id': policy_id,
                    **policy_data.get('metadata', {})
                }
                
                created = create_policy(DEFAULT_TENANT_ID, policy_dict)
                if created:
                    logger.info(f"✅ Created policy: {policy_name}")
                    created_count += 1
                else:
                    logger.error(f"❌ Failed to create policy: {policy_name}")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error creating policy {policy_name}: {e}", exc_info=True)
                error_count += 1
        
        logger.info("=" * 80)
        logger.info(f"✅ Policy seeding complete: {created_count} created, {skipped_count} skipped, {error_count} errors")
        logger.info("=" * 80)
        
        return 0 if error_count == 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Failed to seed policies: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

