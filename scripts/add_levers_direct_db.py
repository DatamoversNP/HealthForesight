#!/usr/bin/env python3
"""Add policy levers directly to database"""
import sys
from pathlib import Path
from uuid import UUID

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "common" / "src"))

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy

# Policy lever templates
LEVER_TEMPLATES = {
    'PRIOR_AUTH': {
        'lever_type': 'PRIOR_AUTH',
        'parameters': {
            'codes': ['72148', '72149', '72158'],
            'requires_clinical_criteria': True
        }
    },
    'UTILIZATION_MANAGEMENT': {
        'lever_type': 'CLINICAL_CRITERIA',
        'parameters': {
            'codes': ['70551', '75574'],
            'requires_criteria_match': True,
            'guideline_source': 'MCG'
        }
    },
    'COST_SHARING': {
        'lever_type': 'COST_SHARING',
        'parameters': {
            'copay': 75,
            'coinsurance': 0,
            'service_category': 'URGENT_CARE'
        }
    },
    'SITE_OF_CARE': {
        'lever_type': 'SITE_OF_CARE',
        'parameters': {
            'preferred_sites': ['FREESTANDING'],
            'disallowed_sites': ['HOSPITAL_OP']
        }
    },
    'SEASONAL_POLICY': {
        'lever_type': 'PRIOR_AUTH',
        'parameters': {
            'codes': ['72148', '72149'],
            'seasonal_variation': True
        }
    },
    'CLINICAL_CRITERIA': {
        'lever_type': 'CLINICAL_CRITERIA',
        'parameters': {
            'codes': ['70551', '75574'],
            'requires_criteria_match': True,
            'guideline_source': 'MCG'
        }
    }
}

def main():
    db = SessionLocal()
    tenant_id = UUID('00000000-0000-0000-0000-000000000001')
    
    try:
        # Get all active policies
        policies = db.query(Policy).filter(
            Policy.tenant_id == tenant_id,
            Policy.status == 'ACTIVE'
        ).all()
        
        print(f'Found {len(policies)} active policies')
        print()
        
        success_count = 0
        updated_count = 0
        
        for policy in policies:
            # Check if policy has levers
            metadata = policy.policy_metadata_json or {}
            if not isinstance(metadata, dict):
                metadata = {}
            
            existing_levers = metadata.get('policy_levers', [])
            
            if existing_levers:
                continue  # Skip if already has levers
            
            # Get appropriate lever template
            policy_type = policy.policy_type or 'PRIOR_AUTH'
            lever_template = LEVER_TEMPLATES.get(policy_type, LEVER_TEMPLATES['PRIOR_AUTH'])
            
            # Add lever to metadata
            if 'policy_levers' not in metadata:
                metadata['policy_levers'] = []
            
            metadata['policy_levers'].append(lever_template)
            policy.policy_metadata_json = metadata
            
            print(f'✅ Updated: {policy.name[:50]}')
            print(f'   Added lever: {lever_template["lever_type"]}')
            updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print()
            print(f'✅ Successfully updated {updated_count} policies')
            print('   Levers added to database')
        else:
            print('✅ All policies already have levers')
        
    except Exception as e:
        db.rollback()
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
