#!/usr/bin/env python3
"""
Simple script to create valid policies via API
This bypasses the relationship issue by calling the API directly
"""
import json
import requests
import sys
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000/api/v1"
TOKEN = "dev-token-123"  # Mock token for dev

# Valid policy examples
POLICIES = [
    {
        "name": "Outpatient MRI Prior Authorization",
        "policy_type": "PRIOR_AUTH",
        "description": "Require prior authorization for outpatient MRI to reduce inappropriate imaging. Expected to reduce target MRI volume by 35% but may increase ER imaging by 45%.",
        "owner_role": "UM_LEADER",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "DFW"],
            "network": ["IN"],
        },
        "effective_period": {
            "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "end_date": None,
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": False,
        },
        "policy_logic": {
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["NYC", "DFW"],
                "network": ["IN"],
            },
            "effective_period": {
                "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "end_date": None,
            },
            "levers": [
                {
                    "lever_type": "PRIOR_AUTH",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["72148", "72149", "72158"],
                        "code_groups": [],
                    },
                    "config": {
                        "requires_pa": True,
                        "pa_touchpoint": "PA_WORKFLOW",
                        "override_allowed": False,
                    },
                    "apply_when": [
                        {
                            "conditions": [
                                {
                                    "field": "place_of_service",
                                    "operator": "IN",
                                    "value": ["11", "22"],
                                },
                            ],
                            "operator": "AND",
                        },
                    ],
                    "exceptions": [
                        {
                            "field": "place_of_service",
                            "operator": "IN",
                            "value": ["23"],
                            "description": "Do not require PA in emergency situations",
                        },
                    ],
                    "priority": 1,
                },
            ],
            "global_exceptions": [],
            "version": 1,
        },
    },
    {
        "name": "Infusion Site-of-Care Optimization",
        "policy_type": "SITE_OF_CARE",
        "description": "Redirect infusion services from hospital outpatient to freestanding centers. Expected to reduce costs by 30% while maintaining volume.",
        "owner_role": "UM_LEADER",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"],
        },
        "effective_period": {
            "start_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
            "end_date": None,
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["CLAIM_EDIT"],
            "override_allowed": True,
        },
        "policy_logic": {
            "scope": {
                "lob": ["COMMERCIAL", "MA"],
                "markets": ["ALL"],
                "network": ["IN"],
            },
            "effective_period": {
                "start_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
                "end_date": None,
            },
            "levers": [
                {
                    "lever_type": "SITE_OF_CARE",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["96413", "96415", "96417"],
                        "code_groups": [],
                    },
                    "config": {
                        "allowed_sites": ["FREESTANDING", "OFFICE"],
                        "disallowed_sites": ["HOSPITAL_OP"],
                        "redirect_to": "FREESTANDING",
                        "deny_if_disallowed": False,
                    },
                    "apply_when": [],
                    "exceptions": [],
                    "priority": 1,
                },
            ],
            "global_exceptions": [],
            "version": 1,
        },
    },
    {
        "name": "Physical Therapy Visit Limit",
        "policy_type": "DURATION_FREQUENCY_LIMIT",
        "description": "Limit PT visits to 20 per calendar year. May lead to deferred care and increased imaging utilization 60-90 days post-limit.",
        "owner_role": "UM_LEADER",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL", "MEDICAID"],
            "markets": ["ALL"],
            "network": ["ALL"],
        },
        "effective_period": {
            "start_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "end_date": None,
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": True,
        },
        "policy_logic": {
            "scope": {
                "lob": ["COMMERCIAL", "MEDICAID"],
                "markets": ["ALL"],
                "network": ["ALL"],
            },
            "effective_period": {
                "start_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "end_date": None,
            },
            "levers": [
                {
                    "lever_type": "DURATION_FREQUENCY_LIMIT",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["97110", "97112", "97140"],
                        "code_groups": [],
                    },
                    "config": {
                        "max_visits": 20,
                        "time_period": "YEAR",
                        "reset_date": "CALENDAR_YEAR",
                        "accumulate_across_providers": True,
                    },
                    "apply_when": [],
                    "exceptions": [],
                    "priority": 1,
                },
            ],
            "global_exceptions": [],
            "version": 1,
        },
    },
    {
        "name": "Urgent Care Copay Increase",
        "policy_type": "COST_SHARING",
        "description": "Increase copay for urgent care visits from $40 to $75 to discourage low-acuity use. May increase ER utilization by 35%.",
        "owner_role": "STRATEGY",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["ALL"],
            "network": ["IN"],
        },
        "effective_period": {
            "start_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
            "end_date": None,
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": False,
        },
        "policy_logic": {
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["ALL"],
                "network": ["IN"],
            },
            "effective_period": {
                "start_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
                "end_date": None,
            },
            "levers": [
                {
                    "lever_type": "COST_SHARING",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["99281", "99282", "99283"],
                        "code_groups": [],
                    },
                    "config": {
                        "copay": 75.0,
                        "coinsurance": 0.0,
                        "deductible_applies": False,
                        "out_of_pocket_applies": True,
                    },
                    "apply_when": [
                        {
                            "conditions": [
                                {
                                    "field": "place_of_service",
                                    "operator": "IN",
                                    "value": ["20"],
                                },
                            ],
                            "operator": "AND",
                        },
                    ],
                    "exceptions": [],
                    "priority": 1,
                },
            ],
            "global_exceptions": [],
            "version": 1,
        },
    },
    {
        "name": "Advanced Imaging Control Bundle",
        "policy_type": "COMPOSITE",
        "description": "Combined PA and frequency controls for advanced imaging (brain MRI with/without contrast). Strong utilization reduction expected but risk of provider circumvention.",
        "owner_role": "UM_LEADER",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC"],
            "network": ["IN"],
        },
        "effective_period": {
            "start_date": (datetime.utcnow() + timedelta(days=120)).isoformat(),
            "end_date": None,
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
            "override_allowed": False,
        },
        "policy_logic": {
            "scope": {
                "lob": ["COMMERCIAL"],
                "markets": ["NYC"],
                "network": ["IN"],
            },
            "effective_period": {
                "start_date": (datetime.utcnow() + timedelta(days=120)).isoformat(),
                "end_date": None,
            },
            "levers": [
                {
                    "lever_type": "PRIOR_AUTH",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["70551", "70552", "70553"],
                        "code_groups": [],
                    },
                    "config": {
                        "requires_pa": True,
                        "pa_touchpoint": "PA_WORKFLOW",
                        "override_allowed": False,
                    },
                    "apply_when": [],
                    "exceptions": [],
                    "priority": 1,
                },
                {
                    "lever_type": "DURATION_FREQUENCY_LIMIT",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["70551", "70552", "70553"],
                        "code_groups": [],
                    },
                    "config": {
                        "max_visits": 2,
                        "time_period": "YEAR",
                        "reset_date": "CALENDAR_YEAR",
                        "accumulate_across_providers": False,
                    },
                    "apply_when": [],
                    "exceptions": [],
                    "priority": 2,
                },
            ],
            "global_exceptions": [],
            "version": 1,
        },
    },
]


def create_policy(policy_data):
    """Create a single policy via API"""
    try:
        response = requests.post(
            f"{API_URL}/policies",
            json=policy_data,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Created: {policy_data['name']} (ID: {result.get('id', 'N/A')})")
            return {"status": "success", "policy": policy_data['name'], "id": result.get('id')}
        else:
            error_msg = response.text
            try:
                error_json = response.json()
                error_msg = error_json.get('detail', error_msg)
            except:
                pass
            print(f"❌ Failed: {policy_data['name']} - {response.status_code}: {error_msg}")
            return {"status": "error", "policy": policy_data['name'], "error": error_msg, "code": response.status_code}
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_URL}")
        print("   Make sure the API server is running: cd apps/api && uvicorn main:app --reload")
        return {"status": "error", "policy": policy_data['name'], "error": "Connection refused"}
    except Exception as e:
        print(f"❌ Error creating {policy_data['name']}: {e}")
        return {"status": "error", "policy": policy_data['name'], "error": str(e)}


def main():
    """Create all valid policies"""
    print("🚀 Creating valid policies via API...")
    print(f"   API URL: {API_URL}")
    print(f"   Token: {TOKEN}")
    print("")
    
    results = []
    for policy in POLICIES:
        result = create_policy(policy)
        results.append(result)
        print("")  # Blank line between policies
    
    # Summary
    print("=" * 60)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    print(f"📊 Summary: {successful}/{len(results)} policies created successfully")
    
    if failed > 0:
        print(f"\n❌ Failed policies:")
        for r in results:
            if r["status"] == "error":
                print(f"   - {r['policy']}: {r.get('error', 'Unknown error')}")
    
    if successful > 0:
        print(f"\n✅ Successfully created policies:")
        for r in results:
            if r["status"] == "success":
                print(f"   - {r['policy']} (ID: {r.get('id', 'N/A')})")
    
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

