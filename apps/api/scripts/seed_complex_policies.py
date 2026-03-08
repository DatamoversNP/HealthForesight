#!/usr/bin/env python3
"""Seed complex, realistic policy examples demonstrating enterprise-grade complexity"""
import sys
import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))

from uepi_api.storage import policy_storage, init_storage
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# Initialize storage
init_storage()

# COMPLEX POLICY EXAMPLES - Demonstrating Real-World Enterprise Complexity

COMPLEX_POLICIES = [
    # EXAMPLE 1: Simple Standalone Policy (Baseline)
    {
        "policy_id": "SIMPLE_MRI_PA_001",
        "policy_name": "Outpatient MRI Prior Authorization - Commercial (Simple)",
        "policy_type": "PRIOR AUTH",
        "description": "Require prior authorization for outpatient MRI procedures. This is the simplest form of a utilization management policy.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2025-01-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["ALL"],
            "network": ["IN"],
            "member_age_min": 18,
            "allowed_sites": ["OUTPATIENT", "FREESTANDING"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["70551", "70552", "70553", "72141", "72142", "72146", "72147", "72148", "72149"],
                    "site_of_care": "OUTPATIENT",
                    "requires_clinical_doc": True,
                    "clinical_requirements": [
                        "FAILED_CONSERVATIVE_THERAPY_6_WEEKS",
                        "PROVIDER_SPECIALTY_ORTHO_NEURO_PCP"
                    ]
                }
            }
        ],
        "exceptions": {
            "emergency_services": True,
            "oncology_diagnosis_codes": ["C00-C97"],
            "trauma_within_72h": True
        },
        "expected_behavioral_response": [
            "DECREASE_TARGET_SERVICE",
            "INCREASE_ER_IMAGING",
            "PROVIDER_CIRCUMVENTION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["UTIL_PER_1K", "ALLOWED_PMPM"],
            "secondary_metrics": ["ER_UTILIZATION", "DENIAL_RATE"],
            "lag_days": [30, 60]
        },
        "ui_hints": {
            "show_substitution_warning": True,
            "elasticity_model": True
        }
    },
    
    # EXAMPLE 2: Moderately Complex Policy (Realistic)
    {
        "policy_id": "COMPLEX_IMG_UM_002",
        "policy_name": "Advanced Imaging Utilization Management - Multi-State Commercial (Complex)",
        "policy_type": "COMPOSITE",
        "description": "Multi-state, multi-network, provider-aware imaging policy with conditional logic, exceptions, and behavioral guardrails. This demonstrates realistic enterprise complexity.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-06-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["TX", "FL", "CA"],
            "network": ["PPO_A", "PPO_B"],
            "provider_types": ["INDEPENDENT_PHYSICIANS"],
            "exclude_provider_types": ["IDN_EMPLOYED"],
            "member_age_min": 18
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
            "override_allowed": True,
            "network_specific": {
                "PPO_A": {"mechanism": "HARD", "deny_without_auth": True},
                "PPO_B": {"mechanism": "SOFT", "education_required": True}
            }
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": {
                        "MRI": ["70551", "70552", "70553", "72141", "72142", "72146", "72147", "72148", "72149"],
                        "CT": ["70450", "70460", "70470", "71250", "71260", "71270"],
                        "PET": ["78811", "78812", "78813", "78814", "78815", "78816"]
                    },
                    "conditional_logic": {
                        "MRI": {
                            "requires_auth": True,
                            "bypass_conditions": [
                                "IN_NETWORK_ORTHO_SPECIALIST",
                                "TWO_RELATED_VISITS_90_DAYS"
                            ]
                        },
                        "CT": {
                            "requires_auth": False,
                            "auth_required_if": [
                                "REPEAT_IMAGING_30_DAYS",
                                "PROVIDER_DENIAL_RATE_ABOVE_10"
                            ]
                        }
                    }
                }
            }
        ],
        "provider_exceptions": {
            "tier_1_providers": {
                "bypass_auth": True,
                "auto_approval": True
            },
            "low_denial_rate_providers": {
                "threshold": 0.05,
                "auto_approval": True
            }
        },
        "patient_exceptions": {
            "oncology": True,
            "pregnancy": True,
            "pediatric": {"age_max": 18}
        },
        "temporal_rules": {
            "auth_validity_days": 60,
            "repeat_imaging_resets_conditions": True,
            "lookback_period_days": 90
        },
        "expected_behavioral_response": [
            "DECREASE_TARGET_SERVICE",
            "PROVIDER_ADAPTATION",
            "NETWORK_VARIATION",
            "PATIENT_ED_SHIFT"
        ],
        "analytics_expectations": {
            "primary_metrics": ["UTIL_PER_1K", "ALLOWED_PMPM", "DENIAL_RATE"],
            "secondary_metrics": ["ER_UTILIZATION", "PROVIDER_BEHAVIOR_SHIFTS", "NETWORK_COMPLIANCE"],
            "lag_days": [30, 60, 90]
        },
        "ui_hints": {
            "show_network_variation": True,
            "show_provider_tiering": True,
            "show_conditional_logic": True,
            "require_warning_ack": True
        }
    },
    
    # EXAMPLE 3: Highly Complex Composite Policy (Enterprise Reality)
    {
        "policy_id": "COMPOSITE_MSK_BUNDLE_003",
        "policy_name": "MSK Imaging + Site-of-Care + Referral Integrity Program (Enterprise Composite)",
        "policy_type": "COMPOSITE",
        "description": "Enterprise-grade composite policy bundle combining imaging prior auth, site-of-care steering, and referral pathway integrity. This demonstrates the full complexity of real-world payer policies with nested conditions, behavioral guardrails, and multi-dimensional enforcement.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-03-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["PPO", "NARROW_NETWORK", "EMPLOYER_CUSTOM"],
            "exclude_diagnosis_codes": ["C00-C97"],  # Oncology
            "exclude_conditions": ["TRAUMA", "POST_SURGICAL_FOLLOWUP_90D"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT", "AUTHORIZATION", "CARE_MANAGEMENT"],
            "override_allowed": True,
            "graduated_enforcement": {
                "first_offense": "EDUCATION",
                "repeat_non_compliance": "DENIAL",
                "high_risk_provider": "PRE_PAYMENT_REVIEW"
            }
        },
        "sub_policies": [
            {
                "sub_policy_id": "SP1_IMAGING_PA",
                "name": "MSK Imaging Prior Authorization",
                "applies_to": {
                    "services": ["MRI", "CT"],
                    "body_regions": ["SPINE", "KNEE", "SHOULDER"]
                },
                "conditions": {
                    "prior_conservative_therapy": {
                        "duration_weeks": {"min": 6, "max": 12},
                        "required": True
                    },
                    "prior_plain_radiograph": {
                        "required": True,
                        "within_days": 90
                    },
                    "ordering_provider_specialty": {
                        "allowed": ["ORTHOPEDICS", "NEUROLOGY", "RHEUMATOLOGY"],
                        "requires_justification_if_other": True
                    }
                },
                "dynamic_rules": {
                    "tier_1_providers": {
                        "auth_waived": True
                    },
                    "repeat_imaging": {
                        "stricter_rules": True,
                        "requires_peer_review": True
                    }
                }
            },
            {
                "sub_policy_id": "SP2_SITE_STEERING",
                "name": "Site-of-Care Steering",
                "objective": "Shift imaging from hospital outpatient to freestanding centers",
                "logic": {
                    "if_imaging_approved": {
                        "redirect_to": "FREESTANDING",
                        "unless": [
                            "PATIENT_MOBILITY_LIMITATION",
                            "DISTANCE_GREATER_THAN_30_MILES",
                            "PROVIDER_JUSTIFICATION_SUBMITTED"
                        ]
                    }
                },
                "network_specific": {
                    "EMPLOYER_CUSTOM": {
                        "opt_out_allowed": True
                    },
                    "NARROW_NETWORK": {
                        "stricter_steering": True,
                        "enforcement": "HARD"
                    }
                }
            },
            {
                "sub_policy_id": "SP3_REFERRAL_INTEGRITY",
                "name": "Referral Pathway Integrity",
                "objective": "Prevent self-referral abuse",
                "logic": {
                    "if_ordering_provider_owns_equipment": {
                        "require_additional_review": True,
                        "exception": {
                            "integrated_idns": {
                                "value_based_contracts": True,
                                "bypass_allowed": True
                            }
                        }
                    }
                }
            }
        ],
        "behavioral_guardrails": {
            "provider_adaptation_detection": {
                "monitor": [
                    "CPT_UPCODING",
                    "SHIFT_TO_ADJACENT_PROCEDURES",
                    "SITE_SHIFTING"
                ],
                "if_detected": {
                    "action": "FLAG_FOR_REVIEW",
                    "notify": "UM_LEAD",
                    "enforcement_adjustment": "MAY_SOFTEN"
                }
            },
            "patient_risk_signals": {
                "monitor": [
                    "ED_UTILIZATION_SPIKE",
                    "DEFERRED_CARE_BEYOND_60_DAYS",
                    "ACCESS_COMPLAINTS"
                ],
                "if_detected": {
                    "action": "AUTOMATIC_REVIEW",
                    "policy_adjustment": "MAY_RELAX"
                }
            }
        },
        "measurement_requirements": {
            "cannot_evaluate_on_imaging_alone": True,
            "must_measure": [
                "TARGET_IMAGING_UTIL",
                "DOWNSTREAM_ED_UTIL",
                "INPATIENT_ADMISSIONS",
                "TOTAL_MSK_PMPM",
                "PROVIDER_APPEALS_VOLUME",
                "PATIENT_ACCESS_COMPLAINTS"
            ],
            "requires_elasticity_model": True,
            "requires_behavioral_attribution": True
        },
        "expected_behavioral_response": [
            "STRONG_UTIL_REDUCTION",
            "SITE_MIGRATION",
            "PROVIDER_ADAPTATION",
            "PATIENT_ACCESS_IMPACT",
            "COST_REDISTRIBUTION"
        ],
        "analytics_expectations": {
            "primary_metrics": [
                "IMAGING_UTIL_PER_1K",
                "SITE_DISTRIBUTION",
                "TOTAL_MSK_PMPM",
                "COST_SAVINGS"
            ],
            "secondary_metrics": [
                "ED_UTILIZATION",
                "INPATIENT_ADMISSIONS",
                "PROVIDER_BEHAVIOR_SHIFTS",
                "PATIENT_ACCESS_METRICS",
                "APPEALS_RATE"
            ],
            "lag_days": [30, 60, 90, 180],
            "requires_causal_inference": True,
            "requires_elasticity_modeling": True
        },
        "ui_hints": {
            "show_composite_structure": True,
            "show_sub_policy_interactions": True,
            "show_behavioral_guardrails": True,
            "show_measurement_requirements": True,
            "require_warning_ack": True,
            "show_complexity_warning": True
        }
    },
    
    # EXAMPLE 4: Network-Specific Conditional Policy
    {
        "policy_id": "NETWORK_CONDITIONAL_004",
        "policy_name": "Network-Specific Prior Authorization with Provider Tiering",
        "policy_type": "PRIOR AUTH",
        "description": "Demonstrates how policies must vary by network, provider tier, and member segment with complex conditional logic.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-05-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "CHICAGO", "LA"],
            "network": ["PPO", "HMO", "EPO"],
            "member_segments": ["STANDARD", "PREMIUM", "EMPLOYER_GROUP_A", "EMPLOYER_GROUP_B"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": True,
            "network_specific_enforcement": {
                "PPO": {
                    "mechanism": "SOFT",
                    "education_first": True
                },
                "HMO": {
                    "mechanism": "HARD",
                    "deny_without_auth": True
                },
                "EPO": {
                    "mechanism": "HARD",
                    "no_out_of_network": True
                }
            }
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["70551", "70552", "70553", "72148", "72149"],
                    "conditional_by_network": {
                        "PPO": {
                            "requires_auth": False,
                            "auth_required_if": [
                                "REPEAT_30_DAYS",
                                "PROVIDER_TIER_3"
                            ]
                        },
                        "HMO": {
                            "requires_auth": True,
                            "always_required": True
                        },
                        "EPO": {
                            "requires_auth": True,
                            "in_network_only": True
                        }
                    },
                    "provider_tier_rules": {
                        "tier_1": {
                            "bypass_auth": True,
                            "auto_approval": True
                        },
                        "tier_2": {
                            "requires_auth": True,
                            "expedited_review": True
                        },
                        "tier_3": {
                            "requires_auth": True,
                            "peer_review_required": True
                        }
                    },
                    "member_segment_rules": {
                        "PREMIUM": {
                            "relaxed_criteria": True,
                            "faster_approval": True
                        },
                        "EMPLOYER_GROUP_A": {
                            "custom_criteria": True,
                            "employer_override_allowed": True
                        }
                    }
                }
            }
        ],
        "expected_behavioral_response": [
            "NETWORK_VARIATION",
            "PROVIDER_TIER_MIGRATION",
            "MEMBER_SEGMENT_IMPACT",
            "EMPLOYER_CUSTOMIZATION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["UTIL_PER_1K", "DENIAL_RATE", "NETWORK_COMPLIANCE"],
            "secondary_metrics": ["PROVIDER_TIER_DISTRIBUTION", "MEMBER_SEGMENT_UTIL", "EMPLOYER_FEEDBACK"],
            "lag_days": [30, 60, 90]
        },
        "ui_hints": {
            "show_network_variation": True,
            "show_provider_tiering": True,
            "show_member_segmentation": True,
            "show_conditional_logic_tree": True
        }
    },
    
    # EXAMPLE 5: Time-Bound Policy with Seasonal Variations
    {
        "policy_id": "TEMPORAL_COMPLEX_005",
        "policy_name": "Seasonal Variation Policy with Time-Bound Rules",
        "policy_type": "COMPOSITE",
        "description": "Demonstrates complex temporal rules, seasonal variations, and time-bound policy adjustments based on utilization patterns.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": "2025-12-31"},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
            "override_allowed": True,
            "temporal_adjustments": {
                "seasonal_variation": {
                    "Q1": {"enforcement": "MODERATE", "rationale": "Post-holiday catch-up"},
                    "Q2": {"enforcement": "STRICT", "rationale": "Normal operations"},
                    "Q3": {"enforcement": "MODERATE", "rationale": "Summer utilization patterns"},
                    "Q4": {"enforcement": "LENIENT", "rationale": "Year-end considerations"}
                },
                "utilization_thresholds": {
                    "if_util_above_threshold": {
                        "threshold": 1.2,
                        "action": "TIGHTEN_ENFORCEMENT"
                    },
                    "if_util_below_threshold": {
                        "threshold": 0.8,
                        "action": "RELAX_ENFORCEMENT"
                    }
                }
            }
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["70551", "70552", "70553"],
                    "temporal_rules": {
                        "auth_validity_days": {
                            "standard": 60,
                            "high_util_periods": 30,
                            "low_util_periods": 90
                        },
                        "repeat_imaging_rules": {
                            "within_30_days": "DENY",
                            "within_60_days": "REQUIRE_PEER_REVIEW",
                            "within_90_days": "REQUIRE_JUSTIFICATION",
                            "beyond_90_days": "STANDARD_RULES"
                        }
                    }
                }
            }
        ],
        "expected_behavioral_response": [
            "SEASONAL_ADAPTATION",
            "UTILIZATION_PATTERN_SHIFTS",
            "PROVIDER_TIMING_ADJUSTMENTS"
        ],
        "analytics_expectations": {
            "primary_metrics": ["UTIL_PER_1K", "SEASONAL_VARIATION", "ENFORCEMENT_EFFECTIVENESS"],
            "secondary_metrics": ["PROVIDER_ADAPTATION", "PATIENT_TIMING"],
            "lag_days": [30, 60, 90],
            "requires_temporal_analysis": True
        },
        "ui_hints": {
            "show_temporal_rules": True,
            "show_seasonal_variation": True,
            "show_utilization_thresholds": True
        }
    }
]


def seed_complex_policies():
    """Seed complex policy examples"""
    print(f"Seeding complex policy examples for tenant: {DEFAULT_TENANT_ID}")
    
    existing_policies = policy_storage.list_all()
    existing_ids = {p.get("policy_id") for p in existing_policies if "policy_id" in p}
    
    created_count = 0
    skipped_count = 0
    
    for policy_data in COMPLEX_POLICIES:
        policy_id_str = policy_data["policy_id"]
        
        # Check if policy already exists
        if policy_id_str in existing_ids:
            print(f"  ⏭️  Skipping {policy_id_str} (already exists)")
            skipped_count += 1
            continue
        
        # Create policy record
        policy_uuid = uuid4()
        
        policy_record = {
            "tenant_id": str(DEFAULT_TENANT_ID),
            "id": str(policy_uuid),
            "policy_id": policy_id_str,
            "name": policy_data["policy_name"],
            "description": policy_data["description"],
            "status": policy_data["status"].lower(),
            "policy_type": policy_data["policy_type"],
            "effective_date": policy_data["effective_period"]["start_date"],
            "expiration_date": policy_data["effective_period"].get("end_date"),
            "metadata": {
                "scope": policy_data["scope"],
                "enforcement": policy_data["enforcement"],
                "policy_levers": policy_data.get("policy_levers", []),
                "expected_behavioral_response": policy_data.get("expected_behavioral_response", []),
                "analytics_expectations": policy_data.get("analytics_expectations", {}),
                "ui_hints": policy_data.get("ui_hints", {}),
                "exceptions": policy_data.get("exceptions"),
                "provider_exceptions": policy_data.get("provider_exceptions"),
                "patient_exceptions": policy_data.get("patient_exceptions"),
                "temporal_rules": policy_data.get("temporal_rules"),
                "sub_policies": policy_data.get("sub_policies"),
                "behavioral_guardrails": policy_data.get("behavioral_guardrails"),
                "measurement_requirements": policy_data.get("measurement_requirements"),
                "complexity_level": "SIMPLE" if "Simple" in policy_data["policy_name"] else "MODERATE" if "Complex" in policy_data["policy_name"] else "ENTERPRISE"
            },
            "logic": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Store using policy_id as key
        policy_storage.create(policy_uuid, policy_record)
        print(f"  ✅ Created {policy_id_str}: {policy_data['policy_name']}")
        created_count += 1
    
    print(f"\n✅ Seeding complete!")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(COMPLEX_POLICIES)}")
    print(f"\n📊 Complexity Breakdown:")
    print(f"   - Simple: 1 policy")
    print(f"   - Moderate: 1 policy")
    print(f"   - Enterprise Composite: 3 policies")
    
    return created_count, skipped_count


if __name__ == "__main__":
    seed_complex_policies()

