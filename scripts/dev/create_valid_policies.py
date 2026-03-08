"""
Script to create valid policy examples for testing
This creates policies using the Policy Builder structure (PolicyLogic JSON)
"""
import asyncio
import json
from datetime import datetime, timedelta
from uuid import UUID
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../apps/api/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../packages/common/src')))

from uepi_common.models import (
    PolicyType,
    PolicyStatus,
    PolicyScope,
    EffectivePeriod,
    Enforcement,
    EnforcementMechanism,
    PolicyTouchpoint,
    LineOfBusiness,
    PolicyLeverLogic,
    LeverTargets,
    RuleGroup,
    Condition,
    Exception,
    PolicyLogic,
    CanonicalPolicy,
)

# Demo tenant ID (should match your demo tenant)
DEMO_TENANT_ID = UUID("00000000-0000-0000-0000-000000000002")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def create_policy_1_prior_auth_mri():
    """Prior Authorization - Outpatient MRI"""
    start_date = datetime.utcnow() + timedelta(days=30)
    
    policy_logic = PolicyLogic(
        scope=PolicyScope(
            lob=[LineOfBusiness.COMMERCIAL],
            markets=["NYC", "DFW"],
            network=["IN"],
        ),
        effective_period=EffectivePeriod(
            start_date=start_date,
            end_date=None,
        ),
        levers=[
            PolicyLeverLogic(
                lever_type=PolicyType.PRIOR_AUTH,
                targets=LeverTargets(
                    code_type="CPT",
                    codes=["72148", "72149", "72158"],
                    code_groups=[],
                ),
                config={
                    "requires_pa": True,
                    "pa_touchpoint": "PA_WORKFLOW",
                    "override_allowed": False,
                },
                apply_when=[
                    RuleGroup(
                        conditions=[
                            Condition(
                                field="place_of_service",
                                operator="IN",
                                value=["11", "22"],  # Office, Hospital OP
                            ),
                        ],
                        operator="AND",
                    ),
                ],
                exceptions=[
                    Exception(
                        field="place_of_service",
                        operator="IN",
                        value=["23"],  # ER
                        description="Do not require PA in emergency situations",
                    ),
                ],
                priority=1,
            ),
        ],
        global_exceptions=[],
        version=1,
    )
    
    return CanonicalPolicy(
        policy_id=UUID("10000000-0000-0000-0000-000000000001"),
        policy_name="Outpatient MRI Prior Authorization",
        policy_type=PolicyType.PRIOR_AUTH,
        description="Require prior authorization for outpatient MRI to reduce inappropriate imaging. Expected to reduce target MRI volume by 35% but may increase ER imaging by 45%.",
        status=PolicyStatus.ACTIVE,
        effective_period=policy_logic.effective_period,
        scope=policy_logic.scope,
        enforcement=Enforcement(
            mechanism=EnforcementMechanism.HARD,
            touchpoint=[PolicyTouchpoint.PA_WORKFLOW],
            override_allowed=False,
        ),
        policy_levers=[],
        policy_logic=policy_logic,
    )


def create_policy_2_site_of_care_infusion():
    """Site of Care - Infusion Optimization"""
    start_date = datetime.utcnow() + timedelta(days=60)
    
    policy_logic = PolicyLogic(
        scope=PolicyScope(
            lob=[LineOfBusiness.COMMERCIAL, LineOfBusiness.MA],
            markets=["ALL"],
            network=["IN"],
        ),
        effective_period=EffectivePeriod(
            start_date=start_date,
            end_date=None,
        ),
        levers=[
            PolicyLeverLogic(
                lever_type=PolicyType.SITE_OF_CARE,
                targets=LeverTargets(
                    code_type="CPT",
                    codes=["96413", "96415", "96417"],
                    code_groups=[],
                ),
                config={
                    "allowed_sites": ["FREESTANDING", "OFFICE"],
                    "disallowed_sites": ["HOSPITAL_OP"],
                    "redirect_to": "FREESTANDING",
                    "deny_if_disallowed": False,  # Redirect instead of deny
                },
                apply_when=[],
                exceptions=[],
                priority=1,
            ),
        ],
        global_exceptions=[],
        version=1,
    )
    
    return CanonicalPolicy(
        policy_id=UUID("10000000-0000-0000-0000-000000000002"),
        policy_name="Infusion Site-of-Care Optimization",
        policy_type=PolicyType.SITE_OF_CARE,
        description="Redirect infusion services from hospital outpatient to freestanding centers. Expected to reduce costs by 30% while maintaining volume.",
        status=PolicyStatus.ACTIVE,
        effective_period=policy_logic.effective_period,
        scope=policy_logic.scope,
        enforcement=Enforcement(
            mechanism=EnforcementMechanism.HARD,
            touchpoint=[PolicyTouchpoint.CLAIM_EDIT],
            override_allowed=True,
        ),
        policy_levers=[],
        policy_logic=policy_logic,
    )


def create_policy_3_frequency_limit_pt():
    """Frequency Limit - Physical Therapy"""
    start_date = datetime.utcnow() + timedelta(days=90)
    
    policy_logic = PolicyLogic(
        scope=PolicyScope(
            lob=[LineOfBusiness.COMMERCIAL, LineOfBusiness.MEDICAID],
            markets=["ALL"],
            network=["ALL"],
        ),
        effective_period=EffectivePeriod(
            start_date=start_date,
            end_date=None,
        ),
        levers=[
            PolicyLeverLogic(
                lever_type=PolicyType.DURATION_FREQUENCY_LIMIT,
                targets=LeverTargets(
                    code_type="CPT",
                    codes=["97110", "97112", "97140"],
                    code_groups=[],
                ),
                config={
                    "max_visits": 20,
                    "time_period": "YEAR",
                    "reset_date": "CALENDAR_YEAR",
                    "accumulate_across_providers": True,
                },
                apply_when=[],
                exceptions=[],
                priority=1,
            ),
        ],
        global_exceptions=[],
        version=1,
    )
    
    return CanonicalPolicy(
        policy_id=UUID("10000000-0000-0000-0000-000000000003"),
        policy_name="Physical Therapy Visit Limit",
        policy_type=PolicyType.DURATION_FREQUENCY_LIMIT,
        description="Limit PT visits to 20 per calendar year. May lead to deferred care and increased imaging utilization 60-90 days post-limit.",
        status=PolicyStatus.ACTIVE,
        effective_period=policy_logic.effective_period,
        scope=policy_logic.scope,
        enforcement=Enforcement(
            mechanism=EnforcementMechanism.PASSIVE,
            touchpoint=[PolicyTouchpoint.BENEFIT_ACCUMULATOR],
            override_allowed=True,
        ),
        policy_levers=[],
        policy_logic=policy_logic,
    )


def create_policy_4_cost_sharing_uc():
    """Cost Sharing - Urgent Care Copay"""
    start_date = datetime.utcnow() + timedelta(days=45)
    
    policy_logic = PolicyLogic(
        scope=PolicyScope(
            lob=[LineOfBusiness.COMMERCIAL],
            markets=["ALL"],
            network=["IN"],
        ),
        effective_period=EffectivePeriod(
            start_date=start_date,
            end_date=None,
        ),
        levers=[
            PolicyLeverLogic(
                lever_type=PolicyType.COST_SHARING,
                targets=LeverTargets(
                    code_type="CPT",
                    codes=["99281", "99282", "99283"],
                    code_groups=[],
                ),
                config={
                    "copay": 75.0,
                    "coinsurance": 0.0,
                    "deductible_applies": False,
                    "out_of_pocket_applies": True,
                },
                apply_when=[
                    RuleGroup(
                        conditions=[
                            Condition(
                                field="place_of_service",
                                operator="IN",
                                value=["20"],  # Urgent Care
                            ),
                        ],
                        operator="AND",
                    ),
                ],
                exceptions=[],
                priority=1,
            ),
        ],
        global_exceptions=[],
        version=1,
    )
    
    return CanonicalPolicy(
        policy_id=UUID("10000000-0000-0000-0000-000000000004"),
        policy_name="Urgent Care Copay Increase",
        policy_type=PolicyType.COST_SHARING,
        description="Increase copay for urgent care visits from $40 to $75 to discourage low-acuity use. May increase ER utilization by 35%.",
        status=PolicyStatus.ACTIVE,
        effective_period=policy_logic.effective_period,
        scope=policy_logic.scope,
        enforcement=Enforcement(
            mechanism=EnforcementMechanism.PASSIVE,
            touchpoint=[PolicyTouchpoint.BENEFIT_ACCUMULATOR],
            override_allowed=False,
        ),
        policy_levers=[],
        policy_logic=policy_logic,
    )


def create_policy_5_compound_imaging():
    """Compound Policy - Advanced Imaging Bundle"""
    start_date = datetime.utcnow() + timedelta(days=120)
    
    policy_logic = PolicyLogic(
        scope=PolicyScope(
            lob=[LineOfBusiness.COMMERCIAL],
            markets=["NYC"],
            network=["IN"],
        ),
        effective_period=EffectivePeriod(
            start_date=start_date,
            end_date=None,
        ),
        levers=[
            PolicyLeverLogic(
                lever_type=PolicyType.PRIOR_AUTH,
                targets=LeverTargets(
                    code_type="CPT",
                    codes=["70551", "70552", "70553"],
                    code_groups=[],
                ),
                config={
                    "requires_pa": True,
                    "pa_touchpoint": "PA_WORKFLOW",
                    "override_allowed": False,
                },
                apply_when=[],
                exceptions=[],
                priority=1,
            ),
            PolicyLeverLogic(
                lever_type=PolicyType.DURATION_FREQUENCY_LIMIT,
                targets=LeverTargets(
                    code_type="CPT",
                    codes=["70551", "70552", "70553"],
                    code_groups=[],
                ),
                config={
                    "max_visits": 2,
                    "time_period": "YEAR",
                    "reset_date": "CALENDAR_YEAR",
                    "accumulate_across_providers": False,
                },
                apply_when=[],
                exceptions=[],
                priority=2,
            ),
        ],
        global_exceptions=[],
        version=1,
    )
    
    return CanonicalPolicy(
        policy_id=UUID("10000000-0000-0000-0000-000000000005"),
        policy_name="Advanced Imaging Control Bundle",
        policy_type=PolicyType.COMPOSITE,
        description="Combined PA and frequency controls for advanced imaging (brain MRI with/without contrast). Strong utilization reduction expected but risk of provider circumvention.",
        status=PolicyStatus.ACTIVE,
        effective_period=policy_logic.effective_period,
        scope=policy_logic.scope,
        enforcement=Enforcement(
            mechanism=EnforcementMechanism.HARD,
            touchpoint=[PolicyTouchpoint.PA_WORKFLOW, PolicyTouchpoint.CLAIM_EDIT],
            override_allowed=False,
        ),
        policy_levers=[],
        policy_logic=policy_logic,
    )


async def create_policies_via_api():
    """Create policies via API (requires API to be running)"""
    import requests
    
    base_url = os.getenv("API_URL", "http://localhost:8000/api/v1")
    token = os.getenv("API_TOKEN", "dev-token-123")  # Mock token for dev
    
    policies = [
        create_policy_1_prior_auth_mri(),
        create_policy_2_site_of_care_infusion(),
        create_policy_3_frequency_limit_pt(),
        create_policy_4_cost_sharing_uc(),
        create_policy_5_compound_imaging(),
    ]
    
    results = []
    for policy in policies:
        # Convert to API format
        policy_data = {
            "name": policy.policy_name,
            "policy_type": policy.policy_type.value,
            "description": policy.description,
            "status": policy.status.value,
            "owner_role": "UM_LEADER",
            "scope": {
                "lob": [lob.value for lob in policy.scope.lob] if policy.scope.lob else [],
                "markets": policy.scope.markets or [],
                "network": policy.scope.network or [],
            },
            "effective_period": {
                "start_date": policy.effective_period.start_date.isoformat(),
                "end_date": policy.effective_period.end_date.isoformat() if policy.effective_period.end_date else None,
            },
            "enforcement": {
                "mechanism": policy.enforcement.mechanism.value,
                "touchpoint": [tp.value for tp in policy.enforcement.touchpoint],
                "override_allowed": policy.enforcement.override_allowed,
            },
            "policy_logic": policy.policy_logic.model_dump(mode='json') if policy.policy_logic else None,
        }
        
        try:
            response = requests.post(
                f"{base_url}/policies",
                json=policy_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            
            if response.status_code in [200, 201]:
                results.append({
                    "policy": policy.policy_name,
                    "status": "success",
                    "id": response.json().get("id"),
                })
                print(f"✅ Created: {policy.policy_name}")
            else:
                results.append({
                    "policy": policy.policy_name,
                    "status": "error",
                    "error": response.text,
                })
                print(f"❌ Failed: {policy.policy_name} - {response.status_code}: {response.text}")
        except Exception as e:
            results.append({
                "policy": policy.policy_name,
                "status": "error",
                "error": str(e),
            })
            print(f"❌ Error creating {policy.policy_name}: {e}")
    
    return results


def create_policies_json_file():
    """Create policies as JSON file for manual import"""
    policies = [
        create_policy_1_prior_auth_mri(),
        create_policy_2_site_of_care_infusion(),
        create_policy_3_frequency_limit_pt(),
        create_policy_4_cost_sharing_uc(),
        create_policy_5_compound_imaging(),
    ]
    
    output_file = os.path.join(os.path.dirname(__file__), "../../data/valid_policies.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    policies_data = {
        "tenant_id": str(DEMO_TENANT_ID),
        "generated_at": datetime.utcnow().isoformat(),
        "policies": [p.model_dump(mode='json') for p in policies],
    }
    
    with open(output_file, 'w') as f:
        json.dump(policies_data, f, indent=2, default=str)
    
    print(f"✅ Created {len(policies)} policies in {output_file}")
    return output_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create valid policy examples")
    parser.add_argument("--format", choices=["json", "api"], default="json", help="Output format")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000/api/v1", help="API base URL")
    parser.add_argument("--token", type=str, default="dev-token-123", help="API auth token")
    
    args = parser.parse_args()
    
    if args.format == "json":
        output_file = create_policies_json_file()
        print(f"\n📄 Policies saved to: {output_file}")
        print("\nTo import via API, run:")
        print(f"  python {__file__} --format api --api-url {args.api_url} --token {args.token}")
    else:
        os.environ["API_URL"] = args.api_url
        os.environ["API_TOKEN"] = args.token
        results = asyncio.run(create_policies_via_api())
        print(f"\n📊 Summary: {sum(1 for r in results if r['status'] == 'success')}/{len(results)} policies created successfully")

