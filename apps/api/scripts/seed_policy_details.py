#!/usr/bin/env python3
"""Seed policy assumptions and guardrails for seeded policies"""
import sys
import json
from pathlib import Path
from uuid import UUID
from datetime import datetime, timezone

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))

from uepi_api.storage_policy_assumptions import create_assumption, get_assumptions
from uepi_api.storage_policy_guardrails import create_guardrail, get_guardrails
from uepi_api.storage_policies import list_policies
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_api.storage_file import policy_storage

# Policy-specific assumptions and guardrails
POLICY_DETAILS = {
    "ST_BIOLOGIC_006": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "Patients failing conventional DMARDs will have similar response rates to biologics as treatment-naive patients",
                "rationale": "Based on clinical trials showing comparable efficacy in DMARD-failure populations",
                "evidence_level": "HIGH",
                "review_date": "2025-09-01"
            },
            {
                "assumption_type": "BEHAVIORAL",
                "description": "90-day trial period is sufficient to assess DMARD effectiveness before biologic approval",
                "rationale": "Clinical guidelines recommend 3-month trial period for DMARD assessment",
                "evidence_level": "MEDIUM",
                "review_date": "2025-09-01"
            },
            {
                "assumption_type": "FINANCIAL",
                "description": "Step therapy will reduce biologic utilization by 30-40% while maintaining clinical outcomes",
                "rationale": "Industry benchmarks show step therapy reduces specialty drug utilization",
                "evidence_level": "MEDIUM",
                "review_date": "2025-09-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "biologic_utilization_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.15,
                "action": "REVIEW_POLICY",
                "description": "If biologic utilization exceeds 15% of eligible population, review policy effectiveness"
            },
            {
                "metric_name": "dmard_trial_completion_rate",
                "threshold_type": "MIN",
                "threshold_value": 0.70,
                "action": "ALERT",
                "description": "If less than 70% complete DMARD trial, investigate barriers"
            }
        ]
    },
    "QL_OPIOID_007": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "90 MME daily limit is safe for most chronic non-cancer pain patients",
                "rationale": "CDC guidelines recommend 90 MME as maximum for chronic pain",
                "evidence_level": "HIGH",
                "review_date": "2025-03-01"
            },
            {
                "assumption_type": "BEHAVIORAL",
                "description": "Quantity limits will reduce opioid volume without increasing emergency department visits",
                "rationale": "Studies show quantity limits reduce opioid prescribing without increasing acute care",
                "evidence_level": "MEDIUM",
                "review_date": "2025-03-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "overdose_risk_score",
                "threshold_type": "MAX",
                "threshold_value": 0.05,
                "action": "IMMEDIATE_REVIEW",
                "description": "If overdose risk score exceeds 5%, immediately review policy"
            },
            {
                "metric_name": "er_visit_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.10,
                "action": "ALERT",
                "description": "If ER visits increase more than 10%, investigate policy impact"
            }
        ]
    },
    "PA_CARDIAC_CT_008": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "AUC compliance will ensure appropriate use of cardiac CT angiography",
                "rationale": "AUC guidelines are evidence-based and reduce inappropriate imaging",
                "evidence_level": "HIGH",
                "review_date": "2025-02-01"
            },
            {
                "assumption_type": "BEHAVIORAL",
                "description": "Prior authorization will reduce inappropriate cardiac CT by 25-35%",
                "rationale": "Industry data shows PA reduces inappropriate advanced imaging",
                "evidence_level": "MEDIUM",
                "review_date": "2025-02-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "auc_compliance_rate",
                "threshold_type": "MIN",
                "threshold_value": 0.85,
                "action": "REVIEW_POLICY",
                "description": "If AUC compliance falls below 85%, review approval criteria"
            },
            {
                "metric_name": "denial_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.30,
                "action": "ALERT",
                "description": "If denial rate exceeds 30%, review criteria for potential over-restriction"
            }
        ]
    },
    "ST_DIABETES_012": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "Metformin and SGLT2 inhibitors provide adequate glucose control before GLP-1 therapy",
                "rationale": "Clinical guidelines recommend stepwise approach to diabetes management",
                "evidence_level": "HIGH",
                "review_date": "2025-05-01"
            },
            {
                "assumption_type": "FINANCIAL",
                "description": "Step therapy will defer GLP-1 costs by average of 6 months per patient",
                "rationale": "Based on average time to step therapy completion",
                "evidence_level": "MEDIUM",
                "review_date": "2025-05-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "a1c_above_7_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.25,
                "action": "REVIEW_POLICY",
                "description": "If more than 25% of patients have A1C above 7 after step therapy, review criteria"
            }
        ]
    },
    "PA_SPINE_018": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "90-day conservative treatment trial is sufficient to determine if surgery is needed",
                "rationale": "Clinical guidelines recommend 3-month conservative trial before spine surgery",
                "evidence_level": "HIGH",
                "review_date": "2025-10-01"
            },
            {
                "assumption_type": "BEHAVIORAL",
                "description": "Conservative treatment requirement will reduce spine surgery rate by 20-30%",
                "rationale": "Studies show conservative treatment trials reduce unnecessary surgeries",
                "evidence_level": "MEDIUM",
                "review_date": "2025-10-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "surgery_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.08,
                "action": "REVIEW_POLICY",
                "description": "If spine surgery rate exceeds 8% of eligible population, review approval criteria"
            },
            {
                "metric_name": "readmission_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.15,
                "action": "ALERT",
                "description": "If readmission rate exceeds 15%, investigate policy impact on outcomes"
            }
        ]
    },
    "SOC_SURGERY_009": {
        "assumptions": [
            {
                "assumption_type": "FINANCIAL",
                "description": "ASC procedures cost 15-30% less than hospital outpatient for same procedures",
                "rationale": "Industry benchmarks show ASC cost savings",
                "evidence_level": "HIGH",
                "review_date": "2025-11-01"
            },
            {
                "assumption_type": "CLINICAL",
                "description": "ASC quality outcomes are equivalent to hospital outpatient for eligible procedures",
                "rationale": "Studies show comparable outcomes for low-risk procedures in ASCs",
                "evidence_level": "MEDIUM",
                "review_date": "2025-11-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "asc_migration_rate",
                "threshold_type": "MIN",
                "threshold_value": 0.40,
                "action": "REVIEW_POLICY",
                "description": "If less than 40% migrate to ASC, review barriers"
            },
            {
                "metric_name": "quality_score",
                "threshold_type": "MIN",
                "threshold_value": 4.0,
                "action": "ALERT",
                "description": "If ASC quality score falls below 4.0, review site selection"
            }
        ]
    },
    "CS_TELEHEALTH_010": {
        "assumptions": [
            {
                "assumption_type": "BEHAVIORAL",
                "description": "Cost parity will maintain telehealth utilization at current levels",
                "rationale": "Patient preference for telehealth when cost is equivalent",
                "evidence_level": "MEDIUM",
                "review_date": "2025-12-31"
            },
            {
                "assumption_type": "CLINICAL",
                "description": "Telehealth provides equivalent outcomes for appropriate conditions",
                "rationale": "Studies show telehealth effectiveness for routine care",
                "evidence_level": "HIGH",
                "review_date": "2025-12-31"
            }
        ],
        "guardrails": [
            {
                "metric_name": "telehealth_utilization_rate",
                "threshold_type": "MIN",
                "threshold_value": 0.15,
                "action": "REVIEW_POLICY",
                "description": "If telehealth utilization falls below 15%, review barriers"
            }
        ]
    },
    "PA_PSYCH_013": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "Prior authorization will ensure appropriate level of care for psychiatric admissions",
                "rationale": "PA process evaluates acuity and appropriateness",
                "evidence_level": "MEDIUM",
                "review_date": "2025-12-01"
            },
            {
                "assumption_type": "BEHAVIORAL",
                "description": "PA requirement will reduce average length of stay by 1-2 days",
                "rationale": "Proactive care management reduces unnecessary inpatient days",
                "evidence_level": "MEDIUM",
                "review_date": "2025-12-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "average_length_of_stay",
                "threshold_type": "MAX",
                "threshold_value": 7.0,
                "action": "REVIEW_POLICY",
                "description": "If average LOS exceeds 7 days, review discharge planning"
            },
            {
                "metric_name": "readmission_rate_30d",
                "threshold_type": "MAX",
                "threshold_value": 0.20,
                "action": "ALERT",
                "description": "If 30-day readmission rate exceeds 20%, review discharge criteria"
            }
        ]
    },
    "QL_DME_014": {
        "assumptions": [
            {
                "assumption_type": "FINANCIAL",
                "description": "DME replacement limits will reduce costs by 15-20% without impacting patient care",
                "rationale": "Prevents premature replacement while maintaining necessary equipment",
                "evidence_level": "MEDIUM",
                "review_date": "2025-01-15"
            },
            {
                "assumption_type": "BEHAVIORAL",
                "description": "Replacement intervals align with expected equipment lifespan",
                "rationale": "Based on manufacturer specifications and clinical guidelines",
                "evidence_level": "HIGH",
                "review_date": "2025-01-15"
            }
        ],
        "guardrails": [
            {
                "metric_name": "early_replacement_rate",
                "threshold_type": "MAX",
                "threshold_value": 0.10,
                "action": "REVIEW_POLICY",
                "description": "If more than 10% request early replacement, review intervals"
            },
            {
                "metric_name": "patient_satisfaction_score",
                "threshold_type": "MIN",
                "threshold_value": 3.5,
                "action": "ALERT",
                "description": "If patient satisfaction falls below 3.5, investigate access issues"
            }
        ]
    },
    "SOC_HOME_015": {
        "assumptions": [
            {
                "assumption_type": "CLINICAL",
                "description": "Home health provides equivalent outcomes to SNF for appropriate patients",
                "rationale": "Studies show home health outcomes comparable to SNF",
                "evidence_level": "MEDIUM",
                "review_date": "2025-08-01"
            },
            {
                "assumption_type": "FINANCIAL",
                "description": "Home health costs 20-30% less than SNF for equivalent care",
                "rationale": "Industry benchmarks show home health cost savings",
                "evidence_level": "HIGH",
                "review_date": "2025-08-01"
            }
        ],
        "guardrails": [
            {
                "metric_name": "home_health_utilization_rate",
                "threshold_type": "MIN",
                "threshold_value": 0.50,
                "action": "REVIEW_POLICY",
                "description": "If less than 50% use home health when eligible, review barriers"
            },
            {
                "metric_name": "readmission_rate_30d",
                "threshold_type": "MAX",
                "threshold_value": 0.15,
                "action": "ALERT",
                "description": "If 30-day readmission rate exceeds 15%, review home health criteria"
            }
        ]
    }
}


def seed_policy_details():
    """Seed assumptions and guardrails for policies"""
    print(f"Seeding policy details for tenant: {DEFAULT_TENANT_ID}")
    
    # Get all policies - also check individual files in data/policies/
    all_policies = list_policies(DEFAULT_TENANT_ID)
    
    # Also load from FileStorage directly (individual policy files)
    from pathlib import Path
    import json
    from uuid import UUID
    
    # Load from FileStorage index
    try:
        index_file = Path(policy_storage.base_path) / "index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                policy_ids = json.load(f)
            loaded_from_storage = 0
            for policy_id_str in policy_ids:
                try:
                    policy_uuid = UUID(policy_id_str)
                    policy = policy_storage.get(policy_uuid)
                    if policy and policy.get("tenant_id") == str(DEFAULT_TENANT_ID):
                        all_policies.append(policy)
                        loaded_from_storage += 1
                except Exception as e:
                    pass  # Skip invalid UUIDs
            print(f"  📋 Loaded {loaded_from_storage} additional policies from FileStorage")
    except Exception as e:
        print(f"Warning: Failed to load from FileStorage index: {e}")
    
    print(f"  📋 Loaded {len(all_policies)} total policies")
    
    policy_map = {}
    name_map = {}
    
    for policy in all_policies:
        policy_id_str = policy.get("policy_id")
        policy_name = policy.get("name") or policy.get("policy_name", "")
        
        if policy_id_str:
            policy_map[policy_id_str] = policy
        if policy_name:
            name_map[policy_name.lower()] = policy
    
    print(f"  📋 Policy map has {len(policy_map)} entries by policy_id")
    print(f"  📋 Name map has {len(name_map)} entries by name")
    print(f"  📋 Sample policy_ids in map: {list(policy_map.keys())[:5]}")
    
    created_assumptions = 0
    created_guardrails = 0
    
    # Map policy IDs to policy names for lookup
    policy_id_to_name = {
        "ST_BIOLOGIC_006": "Biologic Step Therapy for Rheumatoid Arthritis",
        "QL_OPIOID_007": "Opioid Quantity Limit - Chronic Pain",
        "PA_CARDIAC_CT_008": "Cardiac CT Angiography Prior Authorization",
        "ST_DIABETES_012": "GLP-1 Step Therapy for Type 2 Diabetes",
        "PA_SPINE_018": "Spine Surgery Prior Authorization",
        "SOC_SURGERY_009": "Ambulatory Surgery Center Preference",
        "CS_TELEHEALTH_010": "Telehealth Cost Sharing Parity",
        "PA_PSYCH_013": "Psychiatric Inpatient Prior Authorization",
        "QL_DME_014": "Durable Medical Equipment Quantity Limits",
        "SOC_HOME_015": "Home Health Care Preference",
    }
    
    for policy_id_str, details in POLICY_DETAILS.items():
        policy = None
        
        # Try to find by policy_id first
        if policy_id_str in policy_map:
            policy = policy_map[policy_id_str]
        # Try to find by name
        elif policy_id_str in policy_id_to_name:
            policy_name = policy_id_to_name[policy_id_str]
            # Try exact match first
            policy = name_map.get(policy_name.lower())
            # If not found, try partial match
            if not policy:
                for p in all_policies:
                    p_name = (p.get("name") or p.get("policy_name", "")).lower()
                    if policy_name.lower() in p_name or p_name in policy_name.lower():
                        policy = p
                        break
        
        if not policy:
            print(f"  ⚠️  Policy {policy_id_str} not found, skipping")
            continue
        
        # Get policy UUID - try multiple fields
        policy_id_value = policy.get("id") or policy.get("policy_id")
        if not policy_id_value:
            print(f"  ⚠️  Policy {policy_id_str} has no ID, skipping")
            continue
        
        try:
            # Handle both UUID strings and UUID objects
            if isinstance(policy_id_value, str):
                if len(policy_id_value) == 36 and policy_id_value.count('-') == 4:
                    policy_uuid = UUID(policy_id_value)
                else:
                    # Not a UUID format, skip
                    print(f"  ⚠️  Policy {policy_id_str} ID is not UUID format: {policy_id_value}, skipping")
                    continue
            else:
                policy_uuid = UUID(str(policy_id_value))
        except (ValueError, AttributeError) as e:
            # If it's not a UUID, we can't create assumptions/guardrails
            print(f"  ⚠️  Policy {policy_id_str} has invalid ID format: {e}, skipping")
            continue
        
        # Create assumptions
        for assumption_data in details.get("assumptions", []):
            try:
                assumption_data["policy_id"] = str(policy_uuid)
                assumption_data["created_at"] = datetime.now(timezone.utc).isoformat()
                create_assumption(DEFAULT_TENANT_ID, policy_uuid, assumption_data)
                created_assumptions += 1
            except Exception as e:
                print(f"  ❌ Failed to create assumption for {policy_id_str}: {e}")
        
        # Create guardrails
        for guardrail_data in details.get("guardrails", []):
            try:
                guardrail_data["policy_id"] = str(policy_uuid)
                guardrail_data["created_at"] = datetime.now(timezone.utc).isoformat()
                create_guardrail(DEFAULT_TENANT_ID, policy_uuid, guardrail_data)
                created_guardrails += 1
            except Exception as e:
                print(f"  ❌ Failed to create guardrail for {policy_id_str}: {e}")
        
        print(f"  ✅ Added details for {policy_id_str}: {policy.get('name', 'Unknown')}")
    
    print(f"\n✅ Seeding complete!")
    print(f"   Assumptions created: {created_assumptions}")
    print(f"   Guardrails created: {created_guardrails}")
    print(f"   Policies processed: {len(POLICY_DETAILS)}")
    
    return created_assumptions, created_guardrails


if __name__ == "__main__":
    seed_policy_details()

