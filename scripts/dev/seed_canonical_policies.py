"""Seed canonical policy examples - real-world scenarios"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api" / "src"))

from uepi_common.models import (
    CanonicalPolicy,
    PolicyType,
    PolicyStatus,
    PolicyScope,
    EffectivePeriod,
    Enforcement,
    PolicyLever,
    ExpectedBehavioralResponse,
    AnalyticsExpectations,
    UIHints,
    EnforcementMechanism,
    PolicyTouchpoint,
    LineOfBusiness,
)


def get_canonical_policies(tenant_id: UUID) -> list[CanonicalPolicy]:
    """Get canonical policy examples - real-world scenarios"""
    
    base_date = datetime.utcnow()
    
    policies = [
        # POLICY 1 - Prior Auth with Substitution Risk (Classic)
        CanonicalPolicy(
            policy_id=UUID("10000000-0000-0000-0000-000000000001"),
            policy_name="Outpatient MRI Prior Authorization",
            policy_type=PolicyType.PRIOR_AUTH,
            description="Require prior authorization for outpatient MRI to reduce inappropriate imaging.",
            status=PolicyStatus.ACTIVE,
            effective_period=EffectivePeriod(
                start_date=base_date - timedelta(days=180),
                end_date=None
            ),
            scope=PolicyScope(
                lob=[LineOfBusiness.COMMERCIAL],
                markets=["NYC", "DFW"],
                network=["IN"]
            ),
            enforcement=Enforcement(
                mechanism=EnforcementMechanism.HARD,
                touchpoint=[PolicyTouchpoint.PA_WORKFLOW],
                override_allowed=False
            ),
            policy_levers=[
                PolicyLever(
                    lever_type=PolicyType.PRIOR_AUTH,
                    parameters={
                        "codes": ["72148", "72149", "72158"],
                        "site_of_care": "OUTPATIENT"
                    }
                )
            ],
            expected_behavioral_response=ExpectedBehavioralResponse(
                responses=["DECREASE_TARGET_SERVICE", "INCREASE_ER_IMAGING", "PROVIDER_CIRCUMVENTION"]
            ),
            analytics_expectations=AnalyticsExpectations(
                primary_metrics=["UTIL_PER_1K", "ALLOWED_PMPM"],
                secondary_metrics=["ER_UTILIZATION"],
                lag_days=[30, 60]
            ),
            ui_hints=UIHints(
                show_substitution_warning=True,
                elasticity_model=True
            )
        ),
        
        # POLICY 2 - Site of Care Shift (High ROI)
        CanonicalPolicy(
            policy_id=UUID("10000000-0000-0000-0000-000000000002"),
            policy_name="Infusion Site-of-Care Optimization",
            policy_type=PolicyType.SITE_OF_CARE,
            description="Redirect infusion services from hospital outpatient to freestanding centers.",
            status=PolicyStatus.ACTIVE,
            effective_period=EffectivePeriod(
                start_date=base_date - timedelta(days=210),
                end_date=None
            ),
            scope=PolicyScope(
                lob=[LineOfBusiness.COMMERCIAL, LineOfBusiness.MA],
                markets=["ALL"],
                network=["IN"]
            ),
            enforcement=Enforcement(
                mechanism=EnforcementMechanism.HARD,
                touchpoint=[PolicyTouchpoint.CLAIM_EDIT],
                override_allowed=True
            ),
            policy_levers=[
                PolicyLever(
                    lever_type=PolicyType.SITE_OF_CARE,
                    parameters={
                        "allowed_sites": ["FREESTANDING"],
                        "disallowed_sites": ["HOSPITAL_OP"]
                    }
                )
            ],
            expected_behavioral_response=ExpectedBehavioralResponse(
                responses=["SITE_SHIFT", "COST_REDUCTION"]
            ),
            analytics_expectations=AnalyticsExpectations(
                primary_metrics=["SITE_DISTRIBUTION", "ALLOWED_PMPM"],
                secondary_metrics=["ACCESS_DELAY"]
            ),
            ui_hints=UIHints(
                show_site_comparison=True
            )
        ),
        
        # POLICY 3 - Frequency Limit (Often Missed, Very Important)
        CanonicalPolicy(
            policy_id=UUID("10000000-0000-0000-0000-000000000003"),
            policy_name="Physical Therapy Visit Limit",
            policy_type=PolicyType.DURATION_FREQUENCY_LIMIT,
            description="Limit PT visits to 20 per calendar year.",
            status=PolicyStatus.ACTIVE,
            effective_period=EffectivePeriod(
                start_date=base_date - timedelta(days=365),
                end_date=None
            ),
            scope=PolicyScope(
                lob=[LineOfBusiness.COMMERCIAL, LineOfBusiness.MEDICAID],
                markets=["ALL"],
                network=["ALL"]
            ),
            enforcement=Enforcement(
                mechanism=EnforcementMechanism.PASSIVE,
                touchpoint=[PolicyTouchpoint.BENEFIT_ACCUMULATOR],
                override_allowed=True
            ),
            policy_levers=[
                PolicyLever(
                    lever_type=PolicyType.DURATION_FREQUENCY_LIMIT,
                    parameters={
                        "codes": ["97110", "97112", "97140"],
                        "max_visits": 20,
                        "time_period": "YEAR"
                    }
                )
            ],
            expected_behavioral_response=ExpectedBehavioralResponse(
                responses=["UTILIZATION_CAPPING", "DEFERRED_CARE"]
            ),
            analytics_expectations=AnalyticsExpectations(
                primary_metrics=["VISITS_PER_MEMBER"],
                lag_days=[90]
            ),
            ui_hints=UIHints(
                show_accumulator=True
            )
        ),
        
        # POLICY 4 - Cost Sharing Differential (Financial Lever)
        CanonicalPolicy(
            policy_id=UUID("10000000-0000-0000-0000-000000000004"),
            policy_name="Urgent Care Copay Increase",
            policy_type=PolicyType.COST_SHARING,
            description="Increase copay for urgent care visits to discourage low-acuity use.",
            status=PolicyStatus.ACTIVE,
            effective_period=EffectivePeriod(
                start_date=base_date - timedelta(days=120),
                end_date=None
            ),
            scope=PolicyScope(
                lob=[LineOfBusiness.COMMERCIAL],
                markets=["ALL"],
                network=["IN"]
            ),
            enforcement=Enforcement(
                mechanism=EnforcementMechanism.PASSIVE,
                touchpoint=[PolicyTouchpoint.BENEFIT_ACCUMULATOR],
                override_allowed=False
            ),
            policy_levers=[
                PolicyLever(
                    lever_type=PolicyType.COST_SHARING,
                    parameters={
                        "service_category": "URGENT_CARE",
                        "copay_change": {
                            "from": 40,
                            "to": 75
                        }
                    }
                )
            ],
            expected_behavioral_response=ExpectedBehavioralResponse(
                responses=["DECREASE_UCC", "INCREASE_ER"]
            ),
            analytics_expectations=AnalyticsExpectations(
                primary_metrics=["VISIT_MIX", "ER_UTILIZATION"]
            ),
            ui_hints=UIHints(
                show_financial_impact=True
            )
        ),
        
        # POLICY 5 - Compound Policy (Very Realistic, Very Important)
        CanonicalPolicy(
            policy_id=UUID("10000000-0000-0000-0000-000000000005"),
            policy_name="Advanced Imaging Control Bundle",
            policy_type=PolicyType.COMPOSITE,
            description="Combined PA and frequency controls for advanced imaging.",
            status=PolicyStatus.ACTIVE,
            effective_period=EffectivePeriod(
                start_date=base_date - timedelta(days=365),
                end_date=None
            ),
            scope=PolicyScope(
                lob=[LineOfBusiness.COMMERCIAL],
                markets=["NYC"],
                network=["IN"]
            ),
            enforcement=Enforcement(
                mechanism=EnforcementMechanism.HARD,
                touchpoint=[PolicyTouchpoint.PA_WORKFLOW, PolicyTouchpoint.CLAIM_EDIT],
                override_allowed=False
            ),
            policy_levers=[
                PolicyLever(
                    lever_type=PolicyType.PRIOR_AUTH,
                    parameters={
                        "codes": ["70551", "70552", "70553"]
                    }
                ),
                PolicyLever(
                    lever_type=PolicyType.DURATION_FREQUENCY_LIMIT,
                    parameters={
                        "codes": ["70551", "70552", "70553"],
                        "max_visits": 2,
                        "time_period": "YEAR"
                    }
                )
            ],
            expected_behavioral_response=ExpectedBehavioralResponse(
                responses=["STRONG_UTIL_REDUCTION", "SUBSTITUTION_RISK"]
            ),
            analytics_expectations=AnalyticsExpectations(
                primary_metrics=["UTIL_PER_1K", "ALLOWED_PMPM"],
                secondary_metrics=["ALTERNATE_IMAGING"]
            ),
            ui_hints=UIHints(
                show_compound_policy=True,
                require_warning_ack=True
            )
        ),
    ]
    
    return policies


if __name__ == "__main__":
    """Save canonical policies to JSON file for file-based storage"""
    tenant_id = UUID("00000000-0000-0000-0000-000000000002")  # Demo tenant
    policies = get_canonical_policies(tenant_id)
    
    # Convert to JSON-serializable format
    policies_data = {
        'tenant_id': str(tenant_id),
        'updated_at': datetime.utcnow().isoformat(),
        'policies': [p.model_dump(mode='json') for p in policies]
    }
    
    # Save to local file (can be uploaded to object storage)
    output_file = Path(__file__).parent.parent.parent / "data" / "canonical_policies.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(policies_data, f, indent=2, default=str)
    
    print(f"✅ Saved {len(policies)} canonical policies to {output_file}")

