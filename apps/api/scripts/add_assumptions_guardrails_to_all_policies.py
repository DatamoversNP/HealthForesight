#!/usr/bin/env python3
"""
Add assumptions and guardrails to all policies based on standard policy definitions.
This script ensures every policy has appropriate assumptions and guardrails.
"""
import sys
from pathlib import Path
from uuid import UUID

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_policies import list_policies, get_policy
from uepi_api.storage_policy_assumptions import create_assumption, get_assumptions
from uepi_api.storage_policy_guardrails import create_guardrail, get_guardrails
from uepi_api.storage_auth import DEFAULT_TENANT_ID

def parse_value_to_range_or_float(value_str):
    """Parse value string to either a range dict or float"""
    if not value_str or value_str == "TBD":
        return None, None
    
    value_str = str(value_str).strip()
    
    # Try to parse as range (e.g., "0.10-0.20" or "10-20%")
    if "-" in value_str:
        # Remove percentage and other text
        clean_str = value_str.replace("%", "").replace("improvement", "").replace("reduction", "").replace("variation", "").strip()
        parts = clean_str.split("-")
        if len(parts) == 2:
            try:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return {
                    "min_value": min_val,
                    "max_value": max_val,
                    "best_estimate": (min_val + max_val) / 2,
                    "confidence_level": 0.95
                }, None
            except (ValueError, TypeError):
                pass
    
    # Try to parse as single float
    try:
        # Remove common text
        clean_val = value_str.replace("%", "").replace("improvement", "").replace("reduction", "").replace("variation", "").strip()
        if clean_val:
            float_val = float(clean_val)
            return None, float_val
    except (ValueError, TypeError):
        pass
    
    # If it's a descriptive string, return None for both
    return None, None

# Standard assumptions and guardrails by policy type
POLICY_ASSUMPTIONS_GUARDRAILS = {
    "PRIOR_AUTH": {
        "assumptions": [
            {
                "assumption_type": "ELASTICITY",
                "description": "10-20% reduction in utilization due to prior authorization requirements",
                "value_str": "0.10-0.20",
                "confidence": 0.70,
                "source": "Industry standard"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "Improved appropriate use through clinical review",
                "value_str": "0.15-0.25",
                "confidence": 0.65,
                "source": "Clinical guidelines"
            }
        ],
        "guardrails": [
            {
                "metric_name": "approval_rate",
                "threshold_type": "min",
                "threshold_value": 0.70,
                "action": "alert",
                "description": "Monitor approval rate to ensure access is not overly restricted"
            },
            {
                "metric_name": "utilization_rate_change",
                "threshold_type": "change_pct",
                "threshold_value": -30.0,
                "action": "alert",
                "description": "Alert if utilization drops more than 30%"
            }
        ]
    },
    "STEP_THERAPY": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "15-30% reduction in specialty drug costs through step therapy",
                "value_str": "0.15-0.30",
                "confidence": 0.75,
                "source": "Pharmacy benefit management"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "20-40% of members will respond to first-line therapy",
                "value_str": "0.20-0.40",
                "confidence": 0.70,
                "source": "Clinical evidence"
            }
        ],
        "guardrails": [
            {
                "metric_name": "step_therapy_completion_rate",
                "threshold_type": "min",
                "threshold_value": 0.60,
                "action": "alert",
                "description": "Monitor step therapy completion to ensure appropriate progression"
            },
            {
                "metric_name": "specialty_drug_cost_pmpm",
                "threshold_type": "max",
                "threshold_value": 200,
                "action": "alert",
                "description": "Alert if specialty drug costs exceed $200 PMPM"
            }
        ]
    },
    "SITE_OF_CARE": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "20-40% cost savings by redirecting to lower-cost sites",
                "value_str": "0.20-0.40",
                "confidence": 0.80,
                "source": "Site-of-care analysis"
            },
            {
                "assumption_type": "QUALITY",
                "description": "Maintain quality outcomes while reducing costs",
                "value_str": None,
                "confidence": 0.75,
                "source": "Quality metrics"
            }
        ],
        "guardrails": [
            {
                "metric_name": "site_of_care_redirect_rate",
                "threshold_type": "min",
                "threshold_value": 0.50,
                "action": "alert",
                "description": "Monitor successful site-of-care redirections"
            },
            {
                "metric_name": "cost_savings_pmpm",
                "threshold_type": "min",
                "threshold_value": 5.0,
                "action": "alert",
                "description": "Alert if cost savings fall below $5 PMPM"
            }
        ]
    },
    "COST_SHARING": {
        "assumptions": [
            {
                "assumption_type": "ELASTICITY",
                "description": "5-15% reduction in utilization due to increased cost sharing",
                "value_str": "0.05-0.15",
                "confidence": 0.70,
                "source": "Price elasticity studies"
            },
            {
                "assumption_type": "COST",
                "description": "10-20% plan savings through cost sharing adjustments",
                "value_str": "0.10-0.20",
                "confidence": 0.75,
                "source": "Actuarial analysis"
            }
        ],
        "guardrails": [
            {
                "metric_name": "member_out_of_pocket",
                "threshold_type": "max",
                "threshold_value": 5000,
                "action": "alert",
                "description": "Monitor member out-of-pocket costs"
            },
            {
                "metric_name": "utilization_rate_change",
                "threshold_type": "change_pct",
                "threshold_value": -25.0,
                "action": "alert",
                "description": "Alert if utilization drops more than 25%"
            }
        ]
    },
    "QUANTITY_LIMIT": {
        "assumptions": [
            {
                "assumption_type": "UTILIZATION",
                "description": "10-20% reduction in utilization through quantity limits",
                "value_str": "0.10-0.20",
                "confidence": 0.70,
                "source": "Utilization management"
            },
            {
                "assumption_type": "COST",
                "description": "15-25% cost reduction through quantity limits",
                "value_str": "0.15-0.25",
                "confidence": 0.75,
                "source": "Cost analysis"
            }
        ],
        "guardrails": [
            {
                "metric_name": "limit_exceedance_rate",
                "threshold_type": "max",
                "threshold_value": 0.10,
                "action": "alert",
                "description": "Monitor how often limits are exceeded"
            },
            {
                "metric_name": "utilization_per_member",
                "threshold_type": "max",
                "threshold_value": 100,
                "action": "alert",
                "description": "Alert if average utilization exceeds 100 units per member"
            }
        ]
    },
    "NETWORK_RESTRICTION": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "10-25% cost savings through network restrictions",
                "value_str": "0.10-0.25",
                "confidence": 0.75,
                "source": "Network analysis"
            },
            {
                "assumption_type": "QUALITY",
                "description": "Maintain quality while controlling costs",
                "value_str": None,
                "confidence": 0.70,
                "source": "Quality metrics"
            }
        ],
        "guardrails": [
            {
                "metric_name": "network_penetration_rate",
                "threshold_type": "min",
                "threshold_value": 0.80,
                "action": "alert",
                "description": "Monitor in-network utilization"
            },
            {
                "metric_name": "cost_savings_pmpm",
                "threshold_type": "min",
                "threshold_value": 3.0,
                "action": "alert",
                "description": "Alert if cost savings fall below $3 PMPM"
            }
        ]
    },
    "UTILIZATION_MANAGEMENT": {
        "assumptions": [
            {
                "assumption_type": "UTILIZATION",
                "description": "15-30% reduction in inappropriate utilization",
                "value_str": "0.15-0.30",
                "confidence": 0.75,
                "source": "Utilization review"
            },
            {
                "assumption_type": "COST",
                "description": "20-35% cost savings through utilization management",
                "value_str": "0.20-0.35",
                "confidence": 0.80,
                "source": "Cost analysis"
            }
        ],
        "guardrails": [
            {
                "metric_name": "utilization_rate",
                "threshold_type": "max",
                "threshold_value": 150,
                "action": "alert",
                "description": "Monitor utilization rate per 1,000 members"
            },
            {
                "metric_name": "cost_pmpm",
                "threshold_type": "max",
                "threshold_value": 100,
                "action": "alert",
                "description": "Alert if cost exceeds $100 PMPM"
            }
        ]
    },
    "COMPOSITE": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "20-40% overall cost reduction through combined policy levers",
                "value_str": "0.20-0.40",
                "confidence": 0.75,
                "source": "Composite policy analysis"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "25-45% utilization reduction through synergistic policy effects",
                "value_str": "0.25-0.45",
                "confidence": 0.70,
                "source": "Policy modeling"
            }
        ],
        "guardrails": [
            {
                "metric_name": "overall_cost_reduction",
                "threshold_type": "min",
                "threshold_value": 0.15,
                "action": "alert",
                "description": "Monitor overall cost reduction percentage"
            },
            {
                "metric_name": "policy_compliance_rate",
                "threshold_type": "min",
                "threshold_value": 0.75,
                "action": "alert",
                "description": "Monitor compliance across all policy components"
            }
        ]
    },
    "COVERAGE": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "Cost avoidance through coverage exclusions",
                "value_str": None,
                "confidence": 0.85,
                "source": "Coverage analysis"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "100% exclusion of non-covered services",
                "value_str": "1.0",
                "confidence": 0.90,
                "source": "Coverage rules"
            }
        ],
        "guardrails": [
            {
                "metric_name": "excluded_claim_count",
                "threshold_type": "max",
                "threshold_value": 50,
                "action": "alert",
                "description": "Monitor excluded claims"
            },
            {
                "metric_name": "cost_avoidance",
                "threshold_type": "min",
                "threshold_value": 10000,
                "action": "alert",
                "description": "Monitor cost avoidance from exclusions"
            }
        ]
    },
    "BENEFIT": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "Predictable benefit costs within annual limits",
                "value_str": None,
                "confidence": 0.85,
                "source": "Benefit design"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "Benefit utilization within expected parameters",
                "value_str": None,
                "confidence": 0.80,
                "source": "Utilization patterns"
            }
        ],
        "guardrails": [
            {
                "metric_name": "benefit_utilization_rate",
                "threshold_type": "max",
                "threshold_value": 0.15,
                "action": "alert",
                "description": "Monitor benefit utilization rate"
            },
            {
                "metric_name": "annual_limit_exceedance",
                "threshold_type": "max",
                "threshold_value": 0.05,
                "action": "alert",
                "description": "Alert if more than 5% exceed annual limits"
            }
        ]
    },
    "SEASONAL_POLICY": {
        "assumptions": [
            {
                "assumption_type": "UTILIZATION",
                "description": "10-30% seasonal variation in utilization patterns",
                "value_str": "0.10-0.30",
                "confidence": 0.70,
                "source": "Seasonal analysis"
            },
            {
                "assumption_type": "COST",
                "description": "Cost adjustments based on seasonal factors",
                "value_str": None,
                "confidence": 0.65,
                "source": "Time series analysis"
            }
        ],
        "guardrails": [
            {
                "metric_name": "seasonal_variation_factor",
                "threshold_type": "max",
                "threshold_value": 1.5,
                "action": "alert",
                "description": "Monitor seasonal variation factor"
            },
            {
                "metric_name": "baseline_deviation",
                "threshold_type": "max",
                "threshold_value": 0.30,
                "action": "alert",
                "description": "Alert if deviation from baseline exceeds 30%"
            }
        ]
    },
    "CLINICAL_CRITERIA": {
        "assumptions": [
            {
                "assumption_type": "QUALITY",
                "description": "10-20% improvement in outcomes through evidence-based criteria",
                "value_str": "0.10-0.20",
                "confidence": 0.75,
                "source": "Clinical guidelines"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "15-25% reduction in inappropriate utilization",
                "value_str": "0.15-0.25",
                "confidence": 0.70,
                "source": "Clinical review"
            }
        ],
        "guardrails": [
            {
                "metric_name": "criteria_compliance_rate",
                "threshold_type": "min",
                "threshold_value": 0.85,
                "action": "alert",
                "description": "Monitor compliance with clinical criteria"
            },
            {
                "metric_name": "outcome_improvement",
                "threshold_type": "min",
                "threshold_value": 0.05,
                "action": "alert",
                "description": "Monitor outcome improvements"
            }
        ]
    },
    "PROVIDER_ELIGIBILITY": {
        "assumptions": [
            {
                "assumption_type": "QUALITY",
                "description": "10-15% improvement in outcomes with qualified providers",
                "value_str": "0.10-0.15",
                "confidence": 0.75,
                "source": "Quality metrics"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "80%+ of care with qualified providers",
                "value_str": "0.80",
                "confidence": 0.70,
                "source": "Provider analysis"
            }
        ],
        "guardrails": [
            {
                "metric_name": "qualified_provider_share",
                "threshold_type": "min",
                "threshold_value": 0.80,
                "action": "alert",
                "description": "Monitor share of qualified providers"
            },
            {
                "metric_name": "quality_score",
                "threshold_type": "min",
                "threshold_value": 0.85,
                "action": "alert",
                "description": "Monitor provider quality scores"
            }
        ]
    },
    "REFERRAL_REQUIREMENT": {
        "assumptions": [
            {
                "assumption_type": "UTILIZATION",
                "description": "5-10% reduction in direct specialist visits",
                "value_str": "0.05-0.10",
                "confidence": 0.70,
                "source": "Referral patterns"
            },
            {
                "assumption_type": "QUALITY",
                "description": "Improved care coordination through referral requirements",
                "value_str": None,
                "confidence": 0.75,
                "source": "Care coordination metrics"
            }
        ],
        "guardrails": [
            {
                "metric_name": "referral_compliance_rate",
                "threshold_type": "min",
                "threshold_value": 0.85,
                "action": "alert",
                "description": "Monitor referral compliance"
            },
            {
                "metric_name": "care_coordination_score",
                "threshold_type": "min",
                "threshold_value": 0.80,
                "action": "alert",
                "description": "Monitor care coordination scores"
            }
        ]
    },
    "PAYMENT_POLICY": {
        "assumptions": [
            {
                "assumption_type": "COST",
                "description": "15-25% cost reduction through payment model changes",
                "value_str": "0.15-0.25",
                "confidence": 0.80,
                "source": "Payment analysis"
            },
            {
                "assumption_type": "QUALITY",
                "description": "Maintain or improve quality outcomes",
                "value_str": None,
                "confidence": 0.75,
                "source": "Quality metrics"
            }
        ],
        "guardrails": [
            {
                "metric_name": "episode_cost",
                "threshold_type": "max",
                "threshold_value": 30000,
                "action": "alert",
                "description": "Monitor episode costs"
            },
            {
                "metric_name": "quality_score",
                "threshold_type": "min",
                "threshold_value": 0.85,
                "action": "alert",
                "description": "Monitor quality scores"
            }
        ]
    },
    "ADMINISTRATIVE_REQUIREMENT": {
        "assumptions": [
            {
                "assumption_type": "UTILIZATION",
                "description": "10-20% reduction in inappropriate approvals",
                "value_str": "0.10-0.20",
                "confidence": 0.65,
                "source": "Administrative review"
            },
            {
                "assumption_type": "QUALITY",
                "description": "Improved documentation and decision quality",
                "value_str": None,
                "confidence": 0.70,
                "source": "Documentation review"
            }
        ],
        "guardrails": [
            {
                "metric_name": "documentation_completeness",
                "threshold_type": "min",
                "threshold_value": 0.90,
                "action": "alert",
                "description": "Monitor documentation completeness"
            },
            {
                "metric_name": "approval_quality_score",
                "threshold_type": "min",
                "threshold_value": 0.85,
                "action": "alert",
                "description": "Monitor approval quality"
            }
        ]
    },
    "ACCESS_AVAILABILITY_RULE": {
        "assumptions": [
            {
                "assumption_type": "ACCESS",
                "description": "15-25% improvement in member satisfaction with timely access",
                "value_str": "0.15-0.25",
                "confidence": 0.70,
                "source": "Access metrics"
            },
            {
                "assumption_type": "UTILIZATION",
                "description": "Maintain appropriate utilization while improving access",
                "value_str": None,
                "confidence": 0.65,
                "source": "Utilization patterns"
            }
        ],
        "guardrails": [
            {
                "metric_name": "average_wait_time",
                "threshold_type": "max",
                "threshold_value": 21,
                "action": "alert",
                "description": "Monitor average wait times (days)"
            },
            {
                "metric_name": "access_score",
                "threshold_type": "min",
                "threshold_value": 0.80,
                "action": "alert",
                "description": "Monitor access scores"
            }
        ]
    }
}

def get_policy_type_defaults(policy_type: str):
    """Get default assumptions and guardrails for a policy type"""
    # Try exact match first
    if policy_type in POLICY_ASSUMPTIONS_GUARDRAILS:
        return POLICY_ASSUMPTIONS_GUARDRAILS[policy_type]
    
    # Try partial matches
    policy_type_upper = policy_type.upper()
    for key, value in POLICY_ASSUMPTIONS_GUARDRAILS.items():
        if key in policy_type_upper or policy_type_upper in key:
            return value
    
    # Default fallback
    return {
        "assumptions": [
            {
                "assumption_type": "ELASTICITY",
                "description": f"Expected impact for {policy_type} policy",
                "value_str": None,
                "confidence": 0.60,
                "source": "Initial estimate"
            }
        ],
        "guardrails": [
            {
                "metric_name": "utilization_rate",
                "threshold_type": "change_pct",
                "threshold_value": 20.0,
                "action": "alert",
                "description": f"Monitor utilization changes for {policy_type} policy"
            }
        ]
    }

def main():
    """Add assumptions and guardrails to all policies"""
    print("=" * 80)
    print("Adding Assumptions and Guardrails to All Policies")
    print("=" * 80)
    
    # Get all policies
    policies = list_policies(DEFAULT_TENANT_ID)
    print(f"\n📋 Found {len(policies)} policies to process")
    
    total_assumptions = 0
    total_guardrails = 0
    skipped_assumptions = 0
    skipped_guardrails = 0
    errors = 0
    
    for i, policy in enumerate(policies, 1):
        if not policy or not isinstance(policy, dict):
            continue
            
        policy_id = UUID(policy.get('id'))
        policy_name = policy.get('name', 'Unknown')
        policy_type = policy.get('policy_type', 'PRIOR_AUTH')
        
        print(f"\n[{i}/{len(policies)}] Processing: {policy_name} ({policy_type})")
        
        # Get defaults for this policy type
        defaults = get_policy_type_defaults(policy_type)
        
        # Check existing assumptions
        existing_assumptions = get_assumptions(DEFAULT_TENANT_ID, policy_id)
        existing_assumption_types = {a.get('assumption_type') for a in existing_assumptions if a}
        
        # Add missing assumptions
        for assumption_data in defaults.get("assumptions", []):
            assumption_type = assumption_data.get("assumption_type")
            if assumption_type in existing_assumption_types:
                print(f"  ⏭️  Assumption '{assumption_type}' already exists")
                skipped_assumptions += 1
                continue
            
            try:
                # Create a copy to avoid modifying the original
                assumption_copy = assumption_data.copy()
                
                # Convert value_str to range or value
                value_str = assumption_copy.pop("value_str", None)
                if value_str:
                    range_dict, float_val = parse_value_to_range_or_float(value_str)
                    if range_dict:
                        # Use range_json for ranges
                        assumption_copy["range"] = range_dict
                        assumption_copy["value"] = None
                    elif float_val is not None:
                        # Use value for single numeric values
                        assumption_copy["range"] = None
                        assumption_copy["value"] = float_val
                    else:
                        # Descriptive text - store as None
                        assumption_copy["range"] = None
                        assumption_copy["value"] = None
                else:
                    assumption_copy["range"] = None
                    assumption_copy["value"] = None
                
                create_assumption(DEFAULT_TENANT_ID, policy_id, assumption_copy)
                print(f"  ✅ Created assumption: {assumption_copy.get('description', assumption_type)[:50]}")
                total_assumptions += 1
            except Exception as e:
                print(f"  ⚠️  Failed to create assumption: {e}")
                errors += 1
        
        # Check existing guardrails
        existing_guardrails = get_guardrails(DEFAULT_TENANT_ID, policy_id)
        existing_guardrail_metrics = {g.get('metric_name') for g in existing_guardrails if g}
        
        # Add missing guardrails
        for guardrail_data in defaults.get("guardrails", []):
            metric_name = guardrail_data.get("metric_name")
            if metric_name in existing_guardrail_metrics:
                print(f"  ⏭️  Guardrail '{metric_name}' already exists")
                skipped_guardrails += 1
                continue
            
            try:
                create_guardrail(DEFAULT_TENANT_ID, policy_id, guardrail_data)
                print(f"  ✅ Created guardrail: {metric_name}")
                total_guardrails += 1
            except Exception as e:
                print(f"  ⚠️  Failed to create guardrail: {e}")
                errors += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Complete:")
    print(f"   - Created {total_assumptions} assumptions ({skipped_assumptions} skipped)")
    print(f"   - Created {total_guardrails} guardrails ({skipped_guardrails} skipped)")
    print(f"   - {errors} errors")
    print("=" * 80)
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

