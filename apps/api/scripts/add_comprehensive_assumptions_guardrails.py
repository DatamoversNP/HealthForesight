#!/usr/bin/env python3
"""
Add comprehensive assumptions and guardrails to all policies based on standard policy definitions.
This ensures every policy has detailed, policy-specific assumptions and guardrails.
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

from uepi_api.storage_policies import list_policies
from uepi_api.storage_policy_assumptions import create_assumption, get_assumptions, delete_assumption
from uepi_api.storage_policy_guardrails import create_guardrail, get_guardrails, delete_guardrail
from uepi_api.storage_auth import DEFAULT_TENANT_ID

def parse_value_to_range_or_float(value_str):
    """Parse value string to either a range dict or float"""
    if not value_str or value_str == "TBD":
        return None, None
    
    value_str = str(value_str).strip()
    
    # Try to parse as range (e.g., "0.10-0.20")
    if "-" in value_str:
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
        clean_val = value_str.replace("%", "").replace("improvement", "").replace("reduction", "").replace("variation", "").strip()
        if clean_val:
            float_val = float(clean_val)
            return None, float_val
    except (ValueError, TypeError):
        pass
    
    return None, None

# Comprehensive assumptions and guardrails by policy type and name patterns
def get_policy_specific_assumptions_guardrails(policy_name: str, policy_type: str):
    """Get policy-specific assumptions and guardrails based on name and type"""
    name_upper = policy_name.upper()
    type_upper = policy_type.upper()
    
    assumptions = []
    guardrails = []
    
    # PRIOR_AUTH policies
    if "PRIOR_AUTH" in type_upper or "PRIOR AUTH" in type_upper:
        if "MRI" in name_upper:
            assumptions = [
                {
                    "assumption_type": "ELASTICITY",
                    "description": "10-20% reduction in MRI utilization through prior authorization",
                    "value_str": "0.10-0.20",
                    "confidence": 0.75,
                    "source": "Imaging utilization studies"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Improved appropriate use criteria compliance",
                    "value_str": "0.15-0.25",
                    "confidence": 0.70,
                    "source": "AUC guidelines"
                },
                {
                    "assumption_type": "COST",
                    "description": "15-25% cost savings through reduced inappropriate imaging",
                    "value_str": "0.15-0.25",
                    "confidence": 0.80,
                    "source": "Cost analysis"
                }
            ]
            guardrails = [
                {
                    "metric_name": "mri_utilization_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -30.0,
                    "action": "alert",
                    "description": "Alert if MRI utilization drops more than 30%"
                },
                {
                    "metric_name": "approval_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor approval rate to ensure access"
                },
                {
                    "metric_name": "auc_compliance_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.85,
                    "action": "alert",
                    "description": "Monitor AUC compliance rate"
                }
            ]
        elif "CARDIAC" in name_upper or "CT" in name_upper or "ANGIOGRAPHY" in name_upper:
            assumptions = [
                {
                    "assumption_type": "ELASTICITY",
                    "description": "12-22% reduction in cardiac imaging through prior authorization",
                    "value_str": "0.12-0.22",
                    "confidence": 0.75,
                    "source": "Cardiac imaging studies"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Improved diagnostic yield through appropriate use criteria",
                    "value_str": "0.10-0.20",
                    "confidence": 0.70,
                    "source": "Clinical guidelines"
                }
            ]
            guardrails = [
                {
                    "metric_name": "cardiac_imaging_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -25.0,
                    "action": "alert",
                    "description": "Alert if cardiac imaging drops more than 25%"
                },
                {
                    "metric_name": "diagnostic_yield",
                    "threshold_type": "min",
                    "threshold_value": 0.60,
                    "action": "alert",
                    "description": "Monitor diagnostic yield"
                }
            ]
        elif "SPINE" in name_upper or "SURGERY" in name_upper:
            assumptions = [
                {
                    "assumption_type": "ELASTICITY",
                    "description": "15-30% reduction in spine surgery through prior authorization and conservative trial",
                    "value_str": "0.15-0.30",
                    "confidence": 0.80,
                    "source": "Surgery utilization studies"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Improved outcomes through conservative treatment trial requirement",
                    "value_str": "0.20-0.30",
                    "confidence": 0.75,
                    "source": "Clinical evidence"
                }
            ]
            guardrails = [
                {
                    "metric_name": "surgery_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -35.0,
                    "action": "alert",
                    "description": "Alert if surgery rate drops more than 35%"
                },
                {
                    "metric_name": "conservative_trial_completion",
                    "threshold_type": "min",
                    "threshold_value": 0.80,
                    "action": "alert",
                    "description": "Monitor conservative trial completion rate"
                }
            ]
        elif "PSYCHIATRIC" in name_upper or "INPATIENT" in name_upper:
            assumptions = [
                {
                    "assumption_type": "ELASTICITY",
                    "description": "10-20% reduction in psychiatric inpatient admissions",
                    "value_str": "0.10-0.20",
                    "confidence": 0.70,
                    "source": "Behavioral health studies"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Increased use of outpatient and intensive outpatient programs",
                    "value_str": "0.15-0.25",
                    "confidence": 0.65,
                    "source": "Care level analysis"
                }
            ]
            guardrails = [
                {
                    "metric_name": "inpatient_admission_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -25.0,
                    "action": "alert",
                    "description": "Alert if admission rate drops more than 25%"
                },
                {
                    "metric_name": "outpatient_utilization",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor outpatient utilization"
                }
            ]
        else:
            # Generic PRIOR_AUTH
            assumptions = [
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
            ]
            guardrails = [
                {
                    "metric_name": "approval_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor approval rate to ensure access"
                },
                {
                    "metric_name": "utilization_rate_change",
                    "threshold_type": "change_pct",
                    "threshold_value": -30.0,
                    "action": "alert",
                    "description": "Alert if utilization drops more than 30%"
                }
            ]
    
    # STEP_THERAPY policies
    elif "STEP_THERAPY" in type_upper or "STEP THERAPY" in type_upper:
        if "BIOLOGIC" in name_upper or "RA" in name_upper or "RHEUMATOID" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "20-35% reduction in biologic drug costs through step therapy",
                    "value_str": "0.20-0.35",
                    "confidence": 0.80,
                    "source": "Pharmacy benefit management"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "30-50% of members respond to conventional DMARDs",
                    "value_str": "0.30-0.50",
                    "confidence": 0.75,
                    "source": "Clinical evidence"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Maintain quality outcomes while controlling costs",
                    "value_str": None,
                    "confidence": 0.70,
                    "source": "Quality metrics"
                }
            ]
            guardrails = [
                {
                    "metric_name": "step_therapy_completion_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.65,
                    "action": "alert",
                    "description": "Monitor step therapy completion"
                },
                {
                    "metric_name": "biologic_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 180,
                    "action": "alert",
                    "description": "Alert if biologic costs exceed $180 PMPM"
                },
                {
                    "metric_name": "disease_activity_score",
                    "threshold_type": "max",
                    "threshold_value": 3.5,
                    "action": "alert",
                    "description": "Monitor disease activity scores"
                }
            ]
        elif "GLP" in name_upper or "DIABETES" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "25-40% reduction in GLP-1 costs through step therapy",
                    "value_str": "0.25-0.40",
                    "confidence": 0.85,
                    "source": "Diabetes management studies"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "40-60% of members achieve glycemic control with metformin/SGLT2",
                    "value_str": "0.40-0.60",
                    "confidence": 0.75,
                    "source": "Clinical trials"
                }
            ]
            guardrails = [
                {
                    "metric_name": "step_therapy_completion_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor step therapy completion"
                },
                {
                    "metric_name": "glp1_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 200,
                    "action": "alert",
                    "description": "Alert if GLP-1 costs exceed $200 PMPM"
                },
                {
                    "metric_name": "a1c_control_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor A1C control rates"
                }
            ]
        elif "ONCOLOGY" in name_upper or "IMMUNOTHERAPY" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "30-50% reduction in immunotherapy costs through step therapy",
                    "value_str": "0.30-0.50",
                    "confidence": 0.80,
                    "source": "Oncology cost analysis"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "20-40% of patients respond to standard chemotherapy",
                    "value_str": "0.20-0.40",
                    "confidence": 0.70,
                    "source": "Oncology studies"
                }
            ]
            guardrails = [
                {
                    "metric_name": "step_therapy_completion_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.60,
                    "action": "alert",
                    "description": "Monitor step therapy completion"
                },
                {
                    "metric_name": "immunotherapy_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 250,
                    "action": "alert",
                    "description": "Alert if immunotherapy costs exceed $250 PMPM"
                },
                {
                    "metric_name": "progression_free_survival",
                    "threshold_type": "min",
                    "threshold_value": 0.60,
                    "action": "alert",
                    "description": "Monitor progression-free survival rates"
                }
            ]
        else:
            # Generic STEP_THERAPY
            assumptions = [
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
            ]
            guardrails = [
                {
                    "metric_name": "step_therapy_completion_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.60,
                    "action": "alert",
                    "description": "Monitor step therapy completion"
                },
                {
                    "metric_name": "specialty_drug_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 200,
                    "action": "alert",
                    "description": "Alert if specialty drug costs exceed $200 PMPM"
                }
            ]
    
    # SITE_OF_CARE policies
    elif "SITE_OF_CARE" in type_upper or "SITE OF CARE" in type_upper or "PREFERENCE" in name_upper:
        if "INFUSION" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "25-45% cost savings by redirecting infusions to freestanding centers",
                    "value_str": "0.25-0.45",
                    "confidence": 0.85,
                    "source": "Site-of-care analysis"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Maintain quality outcomes at lower-cost sites",
                    "value_str": None,
                    "confidence": 0.80,
                    "source": "Quality metrics"
                }
            ]
            guardrails = [
                {
                    "metric_name": "site_of_care_redirect_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.60,
                    "action": "alert",
                    "description": "Monitor successful site redirections"
                },
                {
                    "metric_name": "infusion_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 120,
                    "action": "alert",
                    "description": "Alert if infusion costs exceed $120 PMPM"
                },
                {
                    "metric_name": "adverse_event_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.02,
                    "action": "alert",
                    "description": "Monitor adverse event rates"
                }
            ]
        elif "SURGERY" in name_upper or "ASC" in name_upper or "AMBULATORY" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "30-50% cost savings by performing surgeries in ASC vs hospital",
                    "value_str": "0.30-0.50",
                    "confidence": 0.85,
                    "source": "ASC cost analysis"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Maintain quality outcomes in ASC setting",
                    "value_str": None,
                    "confidence": 0.80,
                    "source": "Quality studies"
                }
            ]
            guardrails = [
                {
                    "metric_name": "asc_utilization_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor ASC utilization rate"
                },
                {
                    "metric_name": "surgery_cost_savings",
                    "threshold_type": "min",
                    "threshold_value": 0.25,
                    "action": "alert",
                    "description": "Monitor cost savings percentage"
                },
                {
                    "metric_name": "readmission_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.05,
                    "action": "alert",
                    "description": "Monitor readmission rates"
                }
            ]
        elif "HOME HEALTH" in name_upper or "HOME" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "20-35% cost savings through home health preference",
                    "value_str": "0.20-0.35",
                    "confidence": 0.75,
                    "source": "Home health analysis"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Improved patient satisfaction and outcomes",
                    "value_str": "0.10-0.20",
                    "confidence": 0.70,
                    "source": "Patient satisfaction surveys"
                }
            ]
            guardrails = [
                {
                    "metric_name": "home_health_utilization",
                    "threshold_type": "min",
                    "threshold_value": 0.65,
                    "action": "alert",
                    "description": "Monitor home health utilization"
                },
                {
                    "metric_name": "patient_satisfaction_score",
                    "threshold_type": "min",
                    "threshold_value": 0.85,
                    "action": "alert",
                    "description": "Monitor patient satisfaction"
                }
            ]
        else:
            # Generic SITE_OF_CARE
            assumptions = [
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
            ]
            guardrails = [
                {
                    "metric_name": "site_of_care_redirect_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.50,
                    "action": "alert",
                    "description": "Monitor successful redirections"
                },
                {
                    "metric_name": "cost_savings_pmpm",
                    "threshold_type": "min",
                    "threshold_value": 5.0,
                    "action": "alert",
                    "description": "Alert if cost savings fall below $5 PMPM"
                }
            ]
    
    # COST_SHARING policies
    elif "COST_SHARING" in type_upper or "COST SHARING" in type_upper or "COPAY" in name_upper:
        if "URGENT CARE" in name_upper:
            assumptions = [
                {
                    "assumption_type": "ELASTICITY",
                    "description": "8-18% reduction in urgent care visits due to copay increase",
                    "value_str": "0.08-0.18",
                    "confidence": 0.75,
                    "source": "Price elasticity studies"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Shift to primary care for non-urgent conditions",
                    "value_str": "0.10-0.20",
                    "confidence": 0.70,
                    "source": "Utilization patterns"
                }
            ]
            guardrails = [
                {
                    "metric_name": "urgent_care_utilization",
                    "threshold_type": "change_pct",
                    "threshold_value": -25.0,
                    "action": "alert",
                    "description": "Alert if urgent care drops more than 25%"
                },
                {
                    "metric_name": "primary_care_utilization",
                    "threshold_type": "min",
                    "threshold_value": 0.15,
                    "action": "alert",
                    "description": "Monitor primary care utilization increase"
                },
                {
                    "metric_name": "member_out_of_pocket",
                    "threshold_type": "max",
                    "threshold_value": 100,
                    "action": "alert",
                    "description": "Monitor member OOP costs"
                }
            ]
        elif "TELEHEALTH" in name_upper or "TELE" in name_upper:
            assumptions = [
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Maintain telehealth utilization through cost sharing parity",
                    "value_str": None,
                    "confidence": 0.75,
                    "source": "Telehealth studies"
                },
                {
                    "assumption_type": "ACCESS",
                    "description": "Improved access through telehealth availability",
                    "value_str": "0.15-0.25",
                    "confidence": 0.70,
                    "source": "Access metrics"
                }
            ]
            guardrails = [
                {
                    "metric_name": "telehealth_utilization_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.20,
                    "action": "alert",
                    "description": "Monitor telehealth utilization"
                },
                {
                    "metric_name": "access_score",
                    "threshold_type": "min",
                    "threshold_value": 0.80,
                    "action": "alert",
                    "description": "Monitor access scores"
                }
            ]
        elif "GENERIC" in name_upper or "TIER" in name_upper:
            assumptions = [
                {
                    "assumption_type": "ELASTICITY",
                    "description": "5-15% increase in generic drug utilization through lower copay",
                    "value_str": "0.05-0.15",
                    "confidence": 0.75,
                    "source": "Pharmacy utilization studies"
                },
                {
                    "assumption_type": "COST",
                    "description": "10-20% reduction in pharmacy costs",
                    "value_str": "0.10-0.20",
                    "confidence": 0.80,
                    "source": "Pharmacy cost analysis"
                }
            ]
            guardrails = [
                {
                    "metric_name": "generic_dispensing_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.80,
                    "action": "alert",
                    "description": "Monitor generic dispensing rate"
                },
                {
                    "metric_name": "pharmacy_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 50,
                    "action": "alert",
                    "description": "Alert if pharmacy costs exceed $50 PMPM"
                }
            ]
        else:
            # Generic COST_SHARING
            assumptions = [
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
            ]
            guardrails = [
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
    
    # QUANTITY_LIMIT policies
    elif "QUANTITY_LIMIT" in type_upper or "QUANTITY LIMIT" in type_upper or "ANNUAL LIMIT" in name_upper or "VISIT LIMIT" in name_upper:
        if "OPIOID" in name_upper:
            assumptions = [
                {
                    "assumption_type": "UTILIZATION",
                    "description": "15-25% reduction in opioid utilization through quantity limits",
                    "value_str": "0.15-0.25",
                    "confidence": 0.80,
                    "source": "Opioid management studies"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Reduced risk of opioid dependence and overdose",
                    "value_str": None,
                    "confidence": 0.85,
                    "source": "Safety studies"
                }
            ]
            guardrails = [
                {
                    "metric_name": "opioid_utilization_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -30.0,
                    "action": "alert",
                    "description": "Alert if opioid utilization drops more than 30%"
                },
                {
                    "metric_name": "average_daily_mme",
                    "threshold_type": "max",
                    "threshold_value": 90,
                    "action": "alert",
                    "description": "Monitor average daily MME"
                },
                {
                    "metric_name": "opioid_overdose_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.001,
                    "action": "alert",
                    "description": "Monitor overdose rates"
                }
            ]
        elif "THERAPY" in name_upper or "PT" in name_upper or "OT" in name_upper or "SPEECH" in name_upper:
            assumptions = [
                {
                    "assumption_type": "UTILIZATION",
                    "description": "10-20% reduction in therapy visits through visit limits",
                    "value_str": "0.10-0.20",
                    "confidence": 0.75,
                    "source": "Therapy utilization studies"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Maintain functional outcomes within visit limits",
                    "value_str": None,
                    "confidence": 0.70,
                    "source": "Outcome studies"
                }
            ]
            guardrails = [
                {
                    "metric_name": "therapy_utilization_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -25.0,
                    "action": "alert",
                    "description": "Alert if therapy utilization drops more than 25%"
                },
                {
                    "metric_name": "functional_outcome_score",
                    "threshold_type": "min",
                    "threshold_value": 0.75,
                    "action": "alert",
                    "description": "Monitor functional outcome scores"
                },
                {
                    "metric_name": "visit_limit_exceedance",
                    "threshold_type": "max",
                    "threshold_value": 0.10,
                    "action": "alert",
                    "description": "Monitor visit limit exceedance rate"
                }
            ]
        elif "DME" in name_upper or "DURABLE" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "Predictable annual DME costs capped at benefit limit",
                    "value_str": None,
                    "confidence": 0.85,
                    "source": "Benefit design"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "DME utilization within annual benefit limits",
                    "value_str": None,
                    "confidence": 0.80,
                    "source": "Utilization patterns"
                }
            ]
            guardrails = [
                {
                    "metric_name": "dme_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 50,
                    "action": "alert",
                    "description": "Alert if DME costs exceed $50 PMPM"
                },
                {
                    "metric_name": "annual_limit_exceedance",
                    "threshold_type": "max",
                    "threshold_value": 0.05,
                    "action": "alert",
                    "description": "Alert if more than 5% exceed annual limits"
                }
            ]
        else:
            # Generic QUANTITY_LIMIT
            assumptions = [
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
            ]
            guardrails = [
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
    
    # COMPOSITE policies
    elif "COMPOSITE" in type_upper or "COMPOUND" in name_upper or "COMPREHENSIVE" in name_upper or "BUNDLE" in name_upper or "ENTERPRISE" in name_upper:
        if "IMAGING" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "25-45% overall cost reduction through combined imaging controls",
                    "value_str": "0.25-0.45",
                    "confidence": 0.80,
                    "source": "Imaging policy analysis"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "30-50% reduction in inappropriate imaging utilization",
                    "value_str": "0.30-0.50",
                    "confidence": 0.75,
                    "source": "Utilization review"
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Improved diagnostic yield through comprehensive controls",
                    "value_str": "0.10-0.20",
                    "confidence": 0.70,
                    "source": "Quality metrics"
                }
            ]
            guardrails = [
                {
                    "metric_name": "imaging_utilization_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -40.0,
                    "action": "alert",
                    "description": "Alert if imaging utilization drops more than 40%"
                },
                {
                    "metric_name": "imaging_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 80,
                    "action": "alert",
                    "description": "Alert if imaging costs exceed $80 PMPM"
                },
                {
                    "metric_name": "auc_compliance_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.85,
                    "action": "alert",
                    "description": "Monitor AUC compliance"
                },
                {
                    "metric_name": "diagnostic_yield",
                    "threshold_type": "min",
                    "threshold_value": 0.60,
                    "action": "alert",
                    "description": "Monitor diagnostic yield"
                }
            ]
        elif "SURGERY" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "20-40% overall cost reduction through combined surgery controls",
                    "value_str": "0.20-0.40",
                    "confidence": 0.80,
                    "source": "Surgery policy analysis"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "25-45% reduction in elective surgeries",
                    "value_str": "0.25-0.45",
                    "confidence": 0.75,
                    "source": "Surgery utilization studies"
                }
            ]
            guardrails = [
                {
                    "metric_name": "surgery_rate",
                    "threshold_type": "change_pct",
                    "threshold_value": -40.0,
                    "action": "alert",
                    "description": "Alert if surgery rate drops more than 40%"
                },
                {
                    "metric_name": "surgery_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 150,
                    "action": "alert",
                    "description": "Alert if surgery costs exceed $150 PMPM"
                },
                {
                    "metric_name": "outcome_scores",
                    "threshold_type": "min",
                    "threshold_value": 0.85,
                    "action": "alert",
                    "description": "Monitor outcome scores"
                }
            ]
        elif "SPECIALTY" in name_upper or "DRUG" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "20-35% reduction in specialty drug costs through comprehensive management",
                    "value_str": "0.20-0.35",
                    "confidence": 0.80,
                    "source": "Specialty pharmacy analysis"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Improved appropriate use through multiple controls",
                    "value_str": "0.15-0.30",
                    "confidence": 0.75,
                    "source": "Utilization management"
                }
            ]
            guardrails = [
                {
                    "metric_name": "specialty_drug_cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 150,
                    "action": "alert",
                    "description": "Alert if specialty drug costs exceed $150 PMPM"
                },
                {
                    "metric_name": "step_therapy_completion",
                    "threshold_type": "min",
                    "threshold_value": 0.65,
                    "action": "alert",
                    "description": "Monitor step therapy completion"
                },
                {
                    "metric_name": "prior_auth_approval_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.70,
                    "action": "alert",
                    "description": "Monitor prior auth approval rate"
                }
            ]
        else:
            # Generic COMPOSITE
            assumptions = [
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
            ]
            guardrails = [
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
    
    # UTILIZATION_MANAGEMENT policies
    elif "UTILIZATION_MANAGEMENT" in type_upper or "UTILIZATION" in name_upper or "CONTROL" in name_upper:
        if "PROVIDER" in name_upper or "HIGH-COST" in name_upper:
            assumptions = [
                {
                    "assumption_type": "COST",
                    "description": "15-30% cost reduction through high-cost provider controls",
                    "value_str": "0.15-0.30",
                    "confidence": 0.80,
                    "source": "Provider cost analysis"
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Redirection to lower-cost, high-quality providers",
                    "value_str": "0.10-0.20",
                    "confidence": 0.75,
                    "source": "Network analysis"
                }
            ]
            guardrails = [
                {
                    "metric_name": "high_cost_provider_share",
                    "threshold_type": "max",
                    "threshold_value": 0.20,
                    "action": "alert",
                    "description": "Monitor high-cost provider share"
                },
                {
                    "metric_name": "cost_pmpm",
                    "threshold_type": "max",
                    "threshold_value": 100,
                    "action": "alert",
                    "description": "Alert if cost exceeds $100 PMPM"
                },
                {
                    "metric_name": "quality_score",
                    "threshold_type": "min",
                    "threshold_value": 0.85,
                    "action": "alert",
                    "description": "Monitor quality scores"
                }
            ]
        else:
            # Generic UTILIZATION_MANAGEMENT
            assumptions = [
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
            ]
            guardrails = [
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
    
    # NETWORK_RESTRICTION policies
    elif "NETWORK_RESTRICTION" in type_upper or "NETWORK" in name_upper or "TIER" in name_upper:
        assumptions = [
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
        ]
        guardrails = [
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
    
    # CLINICAL_CRITERIA policies
    elif "CLINICAL_CRITERIA" in type_upper or "CLINICAL" in name_upper or "MCG" in name_upper or "CRITERIA" in name_upper:
        assumptions = [
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
        ]
        guardrails = [
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
    
    # SEASONAL_POLICY
    elif "SEASONAL" in type_upper or "SEASONAL" in name_upper or "VARIATION" in name_upper:
        assumptions = [
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
        ]
        guardrails = [
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
    
    # BENEFIT policies
    elif "BENEFIT" in type_upper or "ANNUAL MAX" in name_upper or "MAXIMUM" in name_upper:
        assumptions = [
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
        ]
        guardrails = [
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
    
    # COVERAGE policies
    elif "COVERAGE" in type_upper or "EXCLUSION" in name_upper or "EXPERIMENTAL" in name_upper:
        assumptions = [
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
        ]
        guardrails = [
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
    
    # Default fallback
    else:
        assumptions = [
            {
                "assumption_type": "ELASTICITY",
                "description": f"Expected impact for {policy_type} policy",
                "value_str": None,
                "confidence": 0.60,
                "source": "Initial estimate"
            }
        ]
        guardrails = [
            {
                "metric_name": "utilization_rate",
                "threshold_type": "change_pct",
                "threshold_value": 20.0,
                "action": "alert",
                "description": f"Monitor utilization changes for {policy_type} policy"
            }
        ]
    
    return {"assumptions": assumptions, "guardrails": guardrails}

def main():
    """Add comprehensive assumptions and guardrails to all policies"""
    print("=" * 80)
    print("Adding Comprehensive Assumptions and Guardrails to All Policies")
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
        
        # Get policy-specific assumptions and guardrails
        defaults = get_policy_specific_assumptions_guardrails(policy_name, policy_type)
        
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
                        assumption_copy["range"] = range_dict
                        assumption_copy["value"] = None
                    elif float_val is not None:
                        assumption_copy["range"] = None
                        assumption_copy["value"] = float_val
                    else:
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

