#!/usr/bin/env python3
"""Seed predefined policies for HealthForesight"""
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

# Predefined policies (from user specification)
POLICIES = [
    {
        "policy_id": "PA_MRI_OP_001",
        "policy_name": "Outpatient MRI Prior Authorization",
        "policy_type": "PRIOR AUTH",
        "description": "Require prior authorization for outpatient MRI to reduce inappropriate imaging.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "DFW"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["72148", "72149", "72158"],
                    "site_of_care": "OUTPATIENT"
                }
            }
        ],
        "expected_behavioral_response": [
            "DECREASE_TARGET_SERVICE",
            "INCREASE_ER_IMAGING",
            "PROVIDER_CIRCUMVENTION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["UTIL_PER_1K", "ALLOWED_PMPM"],
            "secondary_metrics": ["ER_UTILIZATION"],
            "lag_days": [30, 60]
        },
        "ui_hints": {
            "show_substitution_warning": True,
            "elasticity_model": True
        }
    },
    {
        "policy_id": "SOC_INFUSION_002",
        "policy_name": "Infusion Site-of-Care Optimization",
        "policy_type": "SITE OF CARE",
        "description": "Redirect infusion services from hospital outpatient to freestanding centers.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-07-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["CLAIM_EDIT"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "SITE_OF_CARE",
                "parameters": {
                    "allowed_sites": ["FREESTANDING"],
                    "disallowed_sites": ["HOSPITAL_OP"]
                }
            }
        ],
        "expected_behavioral_response": [
            "SITE_SHIFT",
            "COST_REDUCTION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["SITE_DISTRIBUTION", "ALLOWED_PMPM"],
            "secondary_metrics": ["ACCESS_DELAY"]
        },
        "ui_hints": {
            "show_site_comparison": True
        }
    },
    {
        "policy_id": "PT_FREQ_003",
        "policy_name": "Physical Therapy Visit Limit",
        "policy_type": "DURATION / FREQUENCY LIMIT",
        "description": "Limit PT visits to 20 per calendar year.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-01-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MEDICAID"],
            "markets": ["ALL"],
            "network": ["ALL"]
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "FREQUENCY_LIMIT",
                "parameters": {
                    "codes": ["97110", "97112", "97140"],
                    "max_visits": 20,
                    "time_period": "YEAR"
                }
            }
        ],
        "expected_behavioral_response": [
            "UTILIZATION_CAPPING",
            "DEFERRED_CARE"
        ],
        "analytics_expectations": {
            "primary_metrics": ["VISITS_PER_MEMBER"],
            "lag_days": [90]
        },
        "ui_hints": {
            "show_accumulator": True
        }
    },
    {
        "policy_id": "CS_UCC_004",
        "policy_name": "Urgent Care Copay Increase",
        "policy_type": "COST SHARING",
        "description": "Increase copay for urgent care visits to discourage low-acuity use.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-04-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "COST_SHARING",
                "parameters": {
                    "service_category": "URGENT_CARE",
                    "copay_change": {
                        "from": 40,
                        "to": 75
                    }
                }
            }
        ],
        "expected_behavioral_response": [
            "DECREASE_UCC",
            "INCREASE_ER"
        ],
        "analytics_expectations": {
            "primary_metrics": ["VISIT_MIX", "ER_UTILIZATION"]
        },
        "ui_hints": {
            "show_financial_impact": True
        }
    },
    {
        "policy_id": "COMPOUND_IMG_005",
        "policy_name": "Advanced Imaging Control Bundle",
        "policy_type": "COMPOSITE",
        "description": "Combined PA and frequency controls for advanced imaging.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["70551", "70552", "70553"]
                }
            },
            {
                "lever_type": "FREQUENCY_LIMIT",
                "parameters": {
                    "codes": ["70551", "70552", "70553"],
                    "max_visits": 2,
                    "time_period": "YEAR"
                }
            }
        ],
        "expected_behavioral_response": [
            "STRONG_UTIL_REDUCTION",
            "SUBSTITUTION_RISK"
        ],
        "analytics_expectations": {
            "primary_metrics": ["UTIL_PER_1K", "ALLOWED_PMPM"],
            "secondary_metrics": ["ALTERNATE_IMAGING"]
        },
        "ui_hints": {
            "show_compound_policy": True,
            "require_warning_ack": True
        }
    },
    {
        "policy_id": "ST_BIOLOGIC_006",
        "policy_name": "Biologic Step Therapy for Rheumatoid Arthritis",
        "policy_type": "STEP THERAPY",
        "description": "Require trial of conventional DMARDs before approving biologic agents for rheumatoid arthritis treatment.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-09-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN", "OON"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "STEP_THERAPY",
                "parameters": {
                    "target_codes": ["J0135", "J1745", "J1602"],
                    "required_trials": ["METHOTREXATE", "SULFASALAZINE"],
                    "trial_duration_days": 90,
                    "failure_criteria": ["INEFFECTIVE", "INTOLERABLE"]
                }
            }
        ],
        "expected_behavioral_response": [
            "DELAYED_BIOLOGIC_START",
            "INCREASED_DMARD_USE",
            "COST_SAVINGS"
        ],
        "analytics_expectations": {
            "primary_metrics": ["BIOLOGIC_UTIL", "DMARD_UTIL", "COST_PMPM"],
            "secondary_metrics": ["DISEASE_ACTIVITY", "PATIENT_OUTCOMES"],
            "lag_days": [90, 180]
        },
        "ui_hints": {
            "show_step_sequence": True,
            "show_trial_tracking": True
        }
    },
    {
        "policy_id": "QL_OPIOID_007",
        "policy_name": "Opioid Quantity Limit - Chronic Pain",
        "policy_type": "QUANTITY LIMIT",
        "description": "Limit opioid prescriptions to 90 MME per day for chronic non-cancer pain management.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-03-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MEDICAID", "MA"],
            "markets": ["ALL"],
            "network": ["ALL"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["CLAIM_EDIT", "PA_WORKFLOW"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "QUANTITY_LIMIT",
                "parameters": {
                    "codes": ["J2175", "J3490", "J2794"],
                    "max_daily_mme": 90,
                    "requires_pa_above": 120,
                    "exceptions": ["CANCER", "HOSPICE", "PALLIATIVE"]
                }
            }
        ],
        "expected_behavioral_response": [
            "REDUCED_OPIOID_VOLUME",
            "INCREASED_NON_OPIOID_USE",
            "SAFETY_IMPROVEMENT"
        ],
        "analytics_expectations": {
            "primary_metrics": ["OPIOID_MME", "OPIOID_CLAIMS", "OVERDOSE_RISK"],
            "secondary_metrics": ["NON_OPIOID_UTIL", "PA_REQUESTS"],
            "lag_days": [30, 90]
        },
        "ui_hints": {
            "show_mme_calculator": True,
            "show_safety_warnings": True
        }
    },
    {
        "policy_id": "PA_CARDIAC_CT_008",
        "policy_name": "Cardiac CT Angiography Prior Authorization",
        "policy_type": "PRIOR AUTH",
        "description": "Require prior authorization for cardiac CT angiography to ensure appropriate use criteria compliance.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-02-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "CHICAGO", "LA"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["75574", "75572", "75573"],
                    "requires_auc": True,
                    "approval_criteria": ["CHEST_PAIN", "CORONARY_RISK", "PRE_OP_EVAL"]
                }
            }
        ],
        "expected_behavioral_response": [
            "DECREASE_INAPPROPRIATE_CT",
            "INCREASE_STRESS_TEST",
            "COST_REDUCTION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["CT_UTIL_PER_1K", "AUC_COMPLIANCE", "ALLOWED_PMPM"],
            "secondary_metrics": ["ALTERNATIVE_IMAGING", "DENIAL_RATE"],
            "lag_days": [60, 120]
        },
        "ui_hints": {
            "show_auc_tool": True,
            "show_alternative_options": True
        }
    },
    {
        "policy_id": "SOC_SURGERY_009",
        "policy_name": "Ambulatory Surgery Center Preference",
        "policy_type": "SITE OF CARE",
        "description": "Prefer ambulatory surgery centers over hospital outpatient departments for eligible procedures.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-11-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "SOFT",
            "touchpoint": ["CLAIM_EDIT", "AUTHORIZATION"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "SITE_OF_CARE",
                "parameters": {
                    "preferred_sites": ["ASC"],
                    "disallowed_sites": ["HOSPITAL_OP"],
                    "codes": ["45378", "45385", "27447", "29881"],
                    "cost_differential_threshold": 0.15
                }
            }
        ],
        "expected_behavioral_response": [
            "SITE_MIGRATION_TO_ASC",
            "COST_REDUCTION",
            "ACCESS_MAINTAINED"
        ],
        "analytics_expectations": {
            "primary_metrics": ["SITE_DISTRIBUTION", "COST_PMPM", "SAVINGS"],
            "secondary_metrics": ["ACCESS_METRICS", "QUALITY_SCORES"],
            "lag_days": [90]
        },
        "ui_hints": {
            "show_site_comparison": True,
            "show_cost_savings": True
        }
    },
    {
        "policy_id": "CS_TELEHEALTH_010",
        "policy_name": "Telehealth Cost Sharing Parity",
        "policy_type": "COST SHARING",
        "description": "Maintain cost sharing parity for telehealth visits to encourage virtual care utilization.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": "2025-12-31"},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN", "OON"]
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "COST_SHARING",
                "parameters": {
                    "codes": ["99441", "99442", "99443", "G2012", "G2010"],
                    "copay_parity": True,
                    "coinsurance_parity": True
                }
            }
        ],
        "expected_behavioral_response": [
            "INCREASE_TELEHEALTH",
            "REDUCE_IN_PERSON_VISITS",
            "IMPROVE_ACCESS"
        ],
        "analytics_expectations": {
            "primary_metrics": ["TELEHEALTH_UTIL", "IN_PERSON_UTIL", "ACCESS_SCORES"],
            "secondary_metrics": ["COST_PER_VISIT", "PATIENT_SATISFACTION"],
            "lag_days": [30, 60]
        },
        "ui_hints": {
            "show_telehealth_options": True,
            "show_access_benefits": True
        }
    },
    {
        "policy_id": "PT_FREQ_OT_011",
        "policy_name": "Occupational Therapy Annual Limit",
        "policy_type": "DURATION / FREQUENCY LIMIT",
        "description": "Limit occupational therapy visits to 30 per calendar year per condition.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-06-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MEDICAID"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "FREQUENCY_LIMIT",
                "parameters": {
                    "codes": ["97165", "97166", "97167", "97168"],
                    "max_visits": 30,
                    "time_period": "YEAR",
                    "per_condition": True
                }
            }
        ],
        "expected_behavioral_response": [
            "UTILIZATION_CAPPING",
            "EARLY_DISCHARGE_PLANNING",
            "COST_CONTROL"
        ],
        "analytics_expectations": {
            "primary_metrics": ["OT_VISITS_PER_MEMBER", "ANNUAL_UTIL"],
            "secondary_metrics": ["FUNCTIONAL_OUTCOMES", "REHAB_DURATION"],
            "lag_days": [90]
        },
        "ui_hints": {
            "show_accumulator": True,
            "show_condition_tracking": True
        }
    },
    {
        "policy_id": "ST_DIABETES_012",
        "policy_name": "GLP-1 Step Therapy for Type 2 Diabetes",
        "policy_type": "STEP THERAPY",
        "description": "Require trial of metformin and SGLT2 inhibitors before approving GLP-1 receptor agonists.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-05-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN", "OON"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "STEP_THERAPY",
                "parameters": {
                    "target_codes": ["J3490", "J3590", "S0148"],
                    "required_trials": ["METFORMIN", "SGLT2_INHIBITOR"],
                    "trial_duration_days": 90,
                    "failure_criteria": ["A1C_ABOVE_7", "INTOLERABLE", "CONTRAINDICATED"]
                }
            }
        ],
        "expected_behavioral_response": [
            "DELAYED_GLP1_START",
            "INCREASED_METFORMIN_USE",
            "COST_SAVINGS"
        ],
        "analytics_expectations": {
            "primary_metrics": ["GLP1_UTIL", "METFORMIN_UTIL", "COST_PMPM"],
            "secondary_metrics": ["A1C_IMPROVEMENT", "WEIGHT_LOSS"],
            "lag_days": [90, 180]
        },
        "ui_hints": {
            "show_step_sequence": True,
            "show_clinical_rationale": True
        }
    },
    {
        "policy_id": "PA_PSYCH_013",
        "policy_name": "Psychiatric Inpatient Prior Authorization",
        "policy_type": "PRIOR AUTH",
        "description": "Require prior authorization for non-emergent psychiatric inpatient admissions.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-12-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"]
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
                    "codes": ["10121", "10122", "10123"],
                    "requires_criteria": ["ACUITY_SCORE", "RISK_ASSESSMENT"],
                    "initial_days": 3,
                    "extensions_require_review": True
                }
            }
        ],
        "expected_behavioral_response": [
            "REDUCED_INPATIENT_DAYS",
            "INCREASED_OUTPATIENT_USE",
            "IMPROVED_CARE_COORDINATION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["INPATIENT_DAYS", "ADMISSION_RATE", "COST_PMPM"],
            "secondary_metrics": ["OUTPATIENT_UTIL", "READMISSION_RATE"],
            "lag_days": [30, 90]
        },
        "ui_hints": {
            "show_criteria_tool": True,
            "show_alternative_options": True
        }
    },
    {
        "policy_id": "QL_DME_014",
        "policy_name": "Durable Medical Equipment Quantity Limits",
        "policy_type": "QUANTITY LIMIT",
        "description": "Limit replacement frequency for DME items based on expected lifespan and medical necessity.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-15", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MEDICARE", "MA"],
            "markets": ["ALL"],
            "network": ["IN", "OON"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["CLAIM_EDIT", "PA_WORKFLOW"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "QUANTITY_LIMIT",
                "parameters": {
                    "codes": ["E1390", "E0260", "E0277", "K0001"],
                    "replacement_intervals": {
                        "E1390": 365,  # Oxygen concentrator - 1 year
                        "E0260": 730,  # Hospital bed - 2 years
                        "E0277": 180,  # CPAP supplies - 6 months
                        "K0001": 1825  # Wheelchair - 5 years
                    },
                    "requires_justification_early": True
                }
            }
        ],
        "expected_behavioral_response": [
            "REDUCED_DME_COSTS",
            "APPROPRIATE_REPLACEMENT_TIMING",
            "FRAUD_REDUCTION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["DME_COST_PMPM", "REPLACEMENT_FREQUENCY", "CLAIM_VOLUME"],
            "secondary_metrics": ["EARLY_REPLACEMENT_RATE", "JUSTIFICATION_RATE"],
            "lag_days": [90, 180]
        },
        "ui_hints": {
            "show_replacement_calculator": True,
            "show_lifespan_guidelines": True
        }
    },
    {
        "policy_id": "SOC_HOME_015",
        "policy_name": "Home Health Care Preference",
        "policy_type": "SITE OF CARE",
        "description": "Prefer home health services over skilled nursing facility when clinically appropriate.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-08-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA", "MEDICARE"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "SOFT",
            "touchpoint": ["AUTHORIZATION", "CARE_MANAGEMENT"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "SITE_OF_CARE",
                "parameters": {
                    "preferred_sites": ["HOME"],
                    "alternative_sites": ["SNF"],
                    "codes": ["G0151", "G0152", "G0153"],
                    "requires_assessment": True,
                    "cost_savings_threshold": 0.20
                }
            }
        ],
        "expected_behavioral_response": [
            "INCREASE_HOME_HEALTH",
            "REDUCE_SNF_DAYS",
            "COST_SAVINGS",
            "PATIENT_PREFERENCE"
        ],
        "analytics_expectations": {
            "primary_metrics": ["HOME_HEALTH_UTIL", "SNF_DAYS", "COST_PMPM"],
            "secondary_metrics": ["PATIENT_SATISFACTION", "OUTCOMES"],
            "lag_days": [60, 120]
        },
        "ui_hints": {
            "show_home_assessment": True,
            "show_cost_comparison": True
        }
    },
    {
        "policy_id": "COMPOUND_CARDIAC_016",
        "policy_name": "Cardiac Imaging Comprehensive Control",
        "policy_type": "COMPOSITE",
        "description": "Combined prior authorization, frequency limits, and site of care controls for cardiac imaging procedures.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-04-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "CHICAGO", "DFW"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT", "AUTHORIZATION"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "parameters": {
                    "codes": ["75574", "78452", "78454"],
                    "requires_auc": True
                }
            },
            {
                "lever_type": "FREQUENCY_LIMIT",
                "parameters": {
                    "codes": ["75574", "78452", "78454"],
                    "max_visits": 1,
                    "time_period": "YEAR"
                }
            },
            {
                "lever_type": "SITE_OF_CARE",
                "parameters": {
                    "preferred_sites": ["FREESTANDING", "HOSPITAL_OP"],
                    "disallowed_sites": ["ER"]
                }
            }
        ],
        "expected_behavioral_response": [
            "STRONG_UTIL_REDUCTION",
            "APPROPRIATE_USE",
            "COST_OPTIMIZATION"
        ],
        "analytics_expectations": {
            "primary_metrics": ["IMAGING_UTIL", "AUC_COMPLIANCE", "COST_PMPM"],
            "secondary_metrics": ["SITE_DISTRIBUTION", "DENIAL_RATE"],
            "lag_days": [90, 180]
        },
        "ui_hints": {
            "show_compound_policy": True,
            "show_auc_tool": True,
            "require_warning_ack": True
        }
    },
    {
        "policy_id": "CS_PREFERRED_017",
        "policy_name": "Preferred Generic Drug Tier",
        "policy_type": "COST SHARING",
        "description": "Lower copay for preferred generic medications to encourage cost-effective prescribing.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-06-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": False
        },
        "policy_levers": [
            {
                "lever_type": "COST_SHARING",
                "parameters": {
                    "tier": "PREFERRED_GENERIC",
                    "copay": 5,
                    "coinsurance": 0,
                    "applies_to": ["GENERIC_DRUGS"]
                }
            }
        ],
        "expected_behavioral_response": [
            "INCREASE_GENERIC_USE",
            "REDUCE_BRAND_USE",
            "COST_SAVINGS"
        ],
        "analytics_expectations": {
            "primary_metrics": ["GENERIC_FILL_RATE", "COST_PMPM", "ADHERENCE"],
            "secondary_metrics": ["BRAND_UTIL", "PATIENT_OUTCOMES"],
            "lag_days": [30, 90]
        },
        "ui_hints": {
            "show_tier_comparison": True,
            "show_savings_calculator": True
        }
    },
    {
        "policy_id": "PA_SPINE_018",
        "policy_name": "Spine Surgery Prior Authorization",
        "policy_type": "PRIOR AUTH",
        "description": "Require prior authorization and conservative treatment trial before spine surgery procedures.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-10-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN"]
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
                    "codes": ["22551", "22552", "22612", "22614"],
                    "requires_conservative_trial": True,
                    "trial_duration_days": 90,
                    "requires_imaging": True,
                    "approval_criteria": ["FAILED_PT", "PROGRESSIVE_SYMPTOMS", "NEUROLOGIC_DEFICIT"]
                }
            }
        ],
        "expected_behavioral_response": [
            "REDUCED_SURGERY_RATE",
            "INCREASED_CONSERVATIVE_CARE",
            "IMPROVED_OUTCOMES",
            "COST_SAVINGS"
        ],
        "analytics_expectations": {
            "primary_metrics": ["SURGERY_RATE", "CONSERVATIVE_CARE_UTIL", "COST_PMPM"],
            "secondary_metrics": ["OUTCOMES", "READMISSION_RATE"],
            "lag_days": [90, 180, 365]
        },
        "ui_hints": {
            "show_conservative_trial_tracking": True,
            "show_imaging_requirements": True,
            "show_alternative_options": True
        }
    },
    {
        "policy_id": "ST_ONCO_019",
        "policy_name": "Oncology Immunotherapy Step Therapy",
        "policy_type": "STEP THERAPY",
        "description": "Require progression on standard chemotherapy before approving immunotherapy for certain cancers.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-07-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["ALL"],
            "network": ["IN", "OON"]
        },
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "STEP_THERAPY",
                "parameters": {
                    "target_codes": ["J9271", "J9272", "J9299"],
                    "required_trials": ["STANDARD_CHEMO"],
                    "trial_duration_days": 60,
                    "failure_criteria": ["DISEASE_PROGRESSION", "INTOLERABLE"],
                    "cancer_types": ["LUNG", "MELANOMA", "RENAL"]
                }
            }
        ],
        "expected_behavioral_response": [
            "DELAYED_IMMUNOTHERAPY",
            "INCREASED_CHEMO_USE",
            "COST_DEFERRAL"
        ],
        "analytics_expectations": {
            "primary_metrics": ["IMMUNOTHERAPY_UTIL", "CHEMO_UTIL", "COST_PMPM"],
            "secondary_metrics": ["SURVIVAL_METRICS", "PROGRESSION_FREE_SURVIVAL"],
            "lag_days": [90, 180, 365]
        },
        "ui_hints": {
            "show_step_sequence": True,
            "show_clinical_evidence": True,
            "show_outcome_tracking": True
        }
    },
    {
        "policy_id": "PT_FREQ_SPEECH_020",
        "policy_name": "Speech Therapy Visit Limit",
        "policy_type": "DURATION / FREQUENCY LIMIT",
        "description": "Limit speech therapy visits to 25 per calendar year for non-acute conditions.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-05-01", "end_date": None},
        "scope": {
            "lob": ["COMMERCIAL", "MEDICAID"],
            "markets": ["ALL"],
            "network": ["IN"]
        },
        "enforcement": {
            "mechanism": "PASSIVE",
            "touchpoint": ["BENEFIT_ACCUMULATOR"],
            "override_allowed": True
        },
        "policy_levers": [
            {
                "lever_type": "FREQUENCY_LIMIT",
                "parameters": {
                    "codes": ["92507", "92508", "92526"],
                    "max_visits": 25,
                    "time_period": "YEAR",
                    "exceptions": ["ACUTE_STROKE", "TRAUMATIC_BRAIN_INJURY"]
                }
            }
        ],
        "expected_behavioral_response": [
            "UTILIZATION_CAPPING",
            "FOCUSED_TREATMENT",
            "COST_CONTROL"
        ],
        "analytics_expectations": {
            "primary_metrics": ["SPEECH_THERAPY_VISITS", "ANNUAL_UTIL"],
            "secondary_metrics": ["FUNCTIONAL_IMPROVEMENT", "TREATMENT_DURATION"],
            "lag_days": [90]
        },
        "ui_hints": {
            "show_accumulator": True,
            "show_exception_criteria": True
        }
    }
]


def seed_policies():
    """Seed predefined policies"""
    print(f"Seeding policies for tenant: {DEFAULT_TENANT_ID}")
    
    existing_policies = policy_storage.list_all()
    existing_ids = {p.get("policy_id") for p in existing_policies if "policy_id" in p}
    
    created_count = 0
    skipped_count = 0
    
    for policy_data in POLICIES:
        policy_id_str = policy_data["policy_id"]
        
        # Check if policy already exists
        if policy_id_str in existing_ids:
            print(f"  ⏭️  Skipping {policy_id_str} (already exists)")
            skipped_count += 1
            continue
        
        # Create policy record compatible with file storage
        # Use policy_id as the storage key, but generate UUID for id field
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
                "policy_levers": policy_data["policy_levers"],
                "expected_behavioral_response": policy_data["expected_behavioral_response"],
                "analytics_expectations": policy_data["analytics_expectations"],
                "ui_hints": policy_data["ui_hints"],
            },
            "logic": {},  # Empty for now, can be populated via Policy Builder
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Store using policy_id as key for easy lookup
        policy_storage.create(policy_uuid, policy_record)
        print(f"  ✅ Created {policy_id_str}: {policy_data['policy_name']}")
        created_count += 1
    
    print(f"\n✅ Seeding complete!")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(POLICIES)}")
    
    return created_count, skipped_count


if __name__ == "__main__":
    seed_policies()

