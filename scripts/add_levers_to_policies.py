#!/usr/bin/env python3
"""Add policy levers to policies that don't have them"""
import requests
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

# Policy lever templates based on policy type
LEVER_TEMPLATES = {
    'PRIOR_AUTH': {
        'lever_type': 'PRIOR_AUTH',
        'parameters': {
            'codes': ['72148', '72149', '72158'],  # Common imaging codes
            'requires_clinical_criteria': True
        }
    },
    'UTILIZATION_MANAGEMENT': {
        'lever_type': 'CLINICAL_CRITERIA',  # Map to CLINICAL_CRITERIA lever
        'parameters': {
            'codes': ['70551', '75574'],  # Common advanced imaging
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
    }
}

def get_policies_without_levers():
    """Get all policies that don't have levers"""
    response = requests.get(f'{API_BASE}/policies', timeout=30)
    if response.status_code != 200:
        print(f'❌ Failed to get policies: {response.status_code}')
        return []
    
    policies = response.json()
    policies_without_levers = []
    
    for p in policies:
        if p.get('status') == 'ACTIVE':
            policy_levers = p.get('policy_levers') or []
            metadata = p.get('policy_metadata_json') or {}
            metadata_levers = metadata.get('policy_levers') or []
            
            if not policy_levers and not metadata_levers:
                policies_without_levers.append(p)
    
    return policies_without_levers

def update_policy_with_lever(policy_id, lever):
    """Update a policy to add a lever via API"""
    try:
        # Get current policy with full data
        get_response = requests.get(
            f'{API_BASE}/policies/{policy_id}',
            headers={'Authorization': 'Bearer dev-token-123'},
            timeout=30
        )
        
        if get_response.status_code != 200:
            return False, f"Could not fetch policy: {get_response.status_code}"
        
        policy_data = get_response.json()
        
        # Get current metadata
        metadata = policy_data.get('policy_metadata_json') or {}
        if not isinstance(metadata, dict):
            metadata = {}
        
        # Add levers to metadata
        if 'policy_levers' not in metadata:
            metadata['policy_levers'] = []
        
        # Check if lever already exists
        existing_types = [l.get('lever_type') for l in metadata['policy_levers'] if isinstance(l, dict)]
        if lever['lever_type'] not in existing_types:
            metadata['policy_levers'].append(lever)
        
        # Map policy types to valid enum values
        # Valid PolicyType enum values: PRIOR_AUTH, SITE_OF_CARE, COVERAGE, STEP_THERAPY, BENEFIT,
        # CLINICAL_CRITERIA, DURATION_FREQUENCY_LIMIT, QUANTITY_LIMIT, NETWORK_RESTRICTION,
        # PROVIDER_ELIGIBILITY, REFERRAL_REQUIREMENT, COST_SHARING, PAYMENT_POLICY,
        # ADMINISTRATIVE_REQUIREMENT, ACCESS_AVAILABILITY_RULE, COMPOSITE
        policy_type_mapping = {
            'UTILIZATION_MANAGEMENT': 'CLINICAL_CRITERIA',  # Map to CLINICAL_CRITERIA
            'SEASONAL_POLICY': 'PRIOR_AUTH',  # Map to PRIOR_AUTH
            'PRIOR_AUTH': 'PRIOR_AUTH',
            'SITE_OF_CARE': 'SITE_OF_CARE',
            'COST_SHARING': 'COST_SHARING',
        }
        
        original_policy_type = policy_data.get('policy_type', 'PRIOR_AUTH')
        mapped_policy_type = policy_type_mapping.get(original_policy_type, 'PRIOR_AUTH')
        
        # Prepare full update data (PUT requires all fields)
        # Use string values directly (API will handle conversion)
        update_data = {
            'name': policy_data.get('name', ''),
            'policy_type': mapped_policy_type,  # Use mapped type
            'owner_role': policy_data.get('owner_role'),
            'description': policy_data.get('description'),
            'status': policy_data.get('status', 'ACTIVE'),
            'scope': policy_data.get('scope'),
            'effective_period': policy_data.get('effective_period'),
            'enforcement': policy_data.get('enforcement'),
            'policy_levers': metadata['policy_levers'],  # Updated with new lever
            'expected_behavioral_response': policy_data.get('expected_behavioral_response'),
            'analytics_expectations': policy_data.get('analytics_expectations'),
            'ui_hints': policy_data.get('ui_hints'),
        }
        
        # Update policy using PUT endpoint
        update_response = requests.put(
            f'{API_BASE}/policies/{policy_id}',
            headers={'Authorization': 'Bearer dev-token-123', 'Content-Type': 'application/json'},
            json=update_data,
            timeout=30
        )
        
        if update_response.status_code in [200, 204]:
            return True, "Success"
        else:
            return False, f"Update failed: {update_response.status_code} - {update_response.text[:200]}"
            
    except Exception as e:
        import traceback
        return False, f"Error: {str(e)[:200]}"

def main():
    print('🔧 Adding levers to policies without them...')
    print()
    
    policies_without_levers = get_policies_without_levers()
    
    if not policies_without_levers:
        print('✅ All policies already have levers!')
        return
    
    print(f'Found {len(policies_without_levers)} policies to update')
    print()
    
    success_count = 0
    error_count = 0
    
    for policy in policies_without_levers:
        policy_id = policy.get('id')
        policy_name = policy.get('name', 'Unknown')
        policy_type = policy.get('policy_type', 'PRIOR_AUTH')
        
        # Get appropriate lever template
        lever_template = LEVER_TEMPLATES.get(policy_type, LEVER_TEMPLATES['PRIOR_AUTH'])
        
        print(f'📝 Updating: {policy_name[:50]}')
        print(f'   Type: {policy_type}')
        print(f'   Adding lever: {lever_template["lever_type"]}')
        
        success, message = update_policy_with_lever(policy_id, lever_template)
        
        if success:
            print(f'   ✅ Added lever successfully')
            success_count += 1
        else:
            print(f'   ❌ {message}')
            error_count += 1
        
        print()
    
    print()
    print(f'📊 Summary:')
    print(f'   ✅ Success: {success_count}')
    print(f'   ❌ Errors: {error_count}')
    print()
    
    if success_count > 0:
        print('✅ Lever addition complete!')
        print('   You can now regenerate predicted impact for these policies.')

if __name__ == '__main__':
    main()
