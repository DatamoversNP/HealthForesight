#!/usr/bin/env python3
"""
Direct script to create valid policies using PolicyStorageAdapter
Works with both database and file-based storage
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uuid import UUID
from uepi_api.storage.policy_storage import get_policy_storage
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
        policy_logic=policy_logic,
    )


def main():
    """Create all valid policies using PolicyStorageAdapter"""
    print("🚀 Creating valid policies using PolicyStorageAdapter...")
    print("")
    
    # Get policy storage (will use database if available, otherwise file-based)
    try:
        storage = get_policy_storage(use_file_storage=False)  # Try database first
        print("✅ Using database storage")
    except Exception as e:
        print(f"⚠️  Database not available, using file-based storage: {e}")
        storage = get_policy_storage(use_file_storage=True)
        print("✅ Using file-based storage")
    
    policies = [
        create_policy_1_prior_auth_mri(),
        create_policy_2_site_of_care_infusion(),
        create_policy_3_frequency_limit_pt(),
        create_policy_4_cost_sharing_uc(),
        create_policy_5_compound_imaging(),
    ]
    
    results = []
    for policy in policies:
        try:
            created = storage.create_policy(policy, tenant_id=DEMO_TENANT_ID)
            if created:
                results.append({
                    "status": "success",
                    "policy": policy.policy_name,
                    "id": str(policy.policy_id),
                })
                print(f"✅ Created: {policy.policy_name} (ID: {policy.policy_id})")
            else:
                results.append({
                    "status": "error",
                    "policy": policy.policy_name,
                    "error": "Storage returned None",
                })
                print(f"❌ Failed: {policy.policy_name} - Storage returned None")
        except Exception as e:
            results.append({
                "status": "error",
                "policy": policy.policy_name,
                "error": str(e),
            })
            print(f"❌ Error creating {policy.policy_name}: {e}")
        print("")  # Blank line between policies
    
    # Summary
    print("=" * 70)
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
    
    # Also save as JSON file for reference
    output_file = project_root / "data" / "valid_policies.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    policies_data = {
        "tenant_id": str(DEMO_TENANT_ID),
        "generated_at": datetime.utcnow().isoformat(),
        "policies": [p.model_dump(mode='json') for p in policies],
    }
    
    with open(output_file, 'w') as f:
        json.dump(policies_data, f, indent=2, default=str)
    
    print(f"\n💾 Policies also saved to: {output_file}")
    
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

