#!/usr/bin/env python3
"""
Seed all 32 comprehensive policies with full details:
- policy name, description, scope, levers, assumptions, guardrails, inputs, outputs, versioning, status, timestamps

This script extends the existing 20 policies in seed_policies.py to 32 policies,
adding assumptions, guardrails, inputs, outputs, and versioning to all policies.
"""
import sys
import importlib.util
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_policies import create_policy, list_policies
from uepi_api.storage_policy_assumptions import create_assumption
from uepi_api.storage_policy_guardrails import create_guardrail
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# Load existing 20 policies from seed_policies.py
policies_file = current_dir / "scripts" / "seed_policies.py"
spec = importlib.util.spec_from_file_location("seed_policies", policies_file)
seed_policies_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_policies_module)
EXISTING_POLICIES = seed_policies_module.POLICIES

# Additional 12 policies to reach 32 total
ADDITIONAL_POLICIES = [
    {
        "policy_id": "CC_MCG_021",
        "policy_name": "MCG Clinical Criteria for Inpatient Admissions",
        "policy_type": "CLINICAL_CRITERIA",
        "description": "Apply MCG (Milliman Care Guidelines) clinical criteria for inpatient admission medical necessity determination.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"], "network": ["IN"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": True},
        "policy_levers": [{"lever_type": "CLINICAL_CRITERIA", "parameters": {"guideline_source": "MCG", "requires_criteria_match": True}}],
        "expected_behavioral_response": ["REDUCED_INAPPROPRIATE_ADMISSIONS", "INCREASED_OBSERVATION_USE"],
        "analytics_expectations": {"primary_metrics": ["INPATIENT_ADMISSION_RATE", "OBSERVATION_RATE"], "lag_days": [30, 90]},
        "ui_hints": {"show_criteria_tool": True},
        "assumptions": [{"assumption_type": "ELASTICITY", "description": "10-15% reduction in inpatient admissions", "value": "0.10-0.15", "confidence": 0.7}],
        "guardrails": [{"metric_name": "inpatient_admission_rate", "threshold_type": "change_pct", "threshold_value": -20.0, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "prior_auth"], "required_fields": ["diagnosis", "acuity_score"]},
        "outputs": {"metrics": ["admission_rate", "observation_rate"], "reports": ["monthly_utilization"]},
        "version": 1
    },
    {
        "policy_id": "NR_TIERED_022",
        "policy_name": "Tiered Network Restriction for High-Cost Procedures",
        "policy_type": "NETWORK_RESTRICTION",
        "description": "Restrict high-cost procedures to Tier 1 providers only, requiring prior authorization for Tier 2.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-03-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL"], "markets": ["NYC", "CHICAGO"], "network": ["TIER1", "TIER2"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": False},
        "policy_levers": [{"lever_type": "NETWORK_RESTRICTION", "parameters": {"allowed_tiers": ["TIER1"], "tier2_requires_pa": True, "codes": ["27447", "29881"]}}],
        "expected_behavioral_response": ["TIER1_MIGRATION", "COST_REDUCTION"],
        "analytics_expectations": {"primary_metrics": ["TIER_DISTRIBUTION", "COST_PMPM"], "lag_days": [60]},
        "ui_hints": {"show_tier_comparison": True},
        "assumptions": [{"assumption_type": "UTILIZATION", "description": "5-10% shift to Tier 1 providers", "value": "0.05-0.10", "confidence": 0.65}],
        "guardrails": [{"metric_name": "tier1_share", "threshold_type": "min", "threshold_value": 0.60, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "network_config"], "required_fields": ["provider_tier", "procedure_code"]},
        "outputs": {"metrics": ["tier_distribution", "cost_savings"], "reports": ["quarterly_network_performance"]},
        "version": 1
    },
    {
        "policy_id": "PE_SPECIALTY_023",
        "policy_name": "Specialist Provider Eligibility for Specialty Services",
        "policy_type": "PROVIDER_ELIGIBILITY",
        "description": "Require board-certified specialists for certain high-complexity procedures.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-09-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"], "network": ["IN"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": True},
        "policy_levers": [{"lever_type": "PROVIDER_ELIGIBILITY", "parameters": {"requires_board_certification": True, "specialty_requirements": ["CARDIOLOGY", "ONCOLOGY"], "codes": ["92920", "96413"]}}],
        "expected_behavioral_response": ["QUALITY_IMPROVEMENT", "SPECIALIST_CONCENTRATION"],
        "analytics_expectations": {"primary_metrics": ["SPECIALIST_UTIL", "QUALITY_SCORES"], "lag_days": [90, 180]},
        "ui_hints": {"show_specialty_requirements": True},
        "assumptions": [{"assumption_type": "QUALITY", "description": "Improved outcomes with specialist care", "value": "10-15% improvement", "confidence": 0.75}],
        "guardrails": [{"metric_name": "specialist_share", "threshold_type": "min", "threshold_value": 0.80, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "provider_master"], "required_fields": ["provider_specialty", "board_certification"]},
        "outputs": {"metrics": ["specialist_utilization", "outcome_metrics"], "reports": ["annual_quality_report"]},
        "version": 1
    },
    {
        "policy_id": "RR_PCP_024",
        "policy_name": "PCP Referral Requirement for Specialist Visits",
        "policy_type": "REFERRAL_REQUIREMENT",
        "description": "Require PCP referral before specialist visits for non-emergent care.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-02-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL"], "markets": ["ALL"], "network": ["IN"]},
        "enforcement": {"mechanism": "SOFT", "touchpoint": ["CLAIM_EDIT"], "override_allowed": True},
        "policy_levers": [{"lever_type": "REFERRAL_REQUIREMENT", "parameters": {"requires_pcp_referral": True, "exceptions": ["EMERGENCY", "OBSTETRICS"], "specialty_codes": ["ALL"]}}],
        "expected_behavioral_response": ["INCREASED_PCP_UTIL", "COORDINATED_CARE"],
        "analytics_expectations": {"primary_metrics": ["SPECIALIST_UTIL", "PCP_UTIL"], "lag_days": [60]},
        "ui_hints": {"show_referral_tracking": True},
        "assumptions": [{"assumption_type": "UTILIZATION", "description": "5-8% reduction in direct specialist visits", "value": "0.05-0.08", "confidence": 0.70}],
        "guardrails": [{"metric_name": "referral_compliance_rate", "threshold_type": "min", "threshold_value": 0.85, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "referrals"], "required_fields": ["referral_id", "specialist_type"]},
        "outputs": {"metrics": ["referral_rate", "care_coordination_score"], "reports": ["monthly_referral_analysis"]},
        "version": 1
    },
    {
        "policy_id": "PP_BUNDLE_025",
        "policy_name": "Bundled Payment for Joint Replacement",
        "policy_type": "PAYMENT_POLICY",
        "description": "Implement bundled payment model for total joint replacement procedures.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-06-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["NYC", "DFW"], "network": ["IN"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["CLAIM_EDIT"], "override_allowed": False},
        "policy_levers": [{"lever_type": "PAYMENT_POLICY", "parameters": {"payment_model": "BUNDLED", "episode_duration_days": 90, "codes": ["27447", "27130"], "target_price": 25000}}],
        "expected_behavioral_response": ["COST_REDUCTION", "QUALITY_IMPROVEMENT", "CARE_COORDINATION"],
        "analytics_expectations": {"primary_metrics": ["EPISODE_COST", "READMISSION_RATE"], "lag_days": [90, 180]},
        "ui_hints": {"show_bundle_tracking": True},
        "assumptions": [{"assumption_type": "COST", "description": "15-20% cost reduction per episode", "value": "0.15-0.20", "confidence": 0.80}],
        "guardrails": [{"metric_name": "episode_cost", "threshold_type": "max", "threshold_value": 30000, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "episodes"], "required_fields": ["episode_id", "total_cost"]},
        "outputs": {"metrics": ["episode_cost", "quality_scores"], "reports": ["quarterly_bundle_performance"]},
        "version": 1
    },
    {
        "policy_id": "AR_DOC_026",
        "policy_name": "Documentation Requirement for High-Cost Services",
        "policy_type": "ADMINISTRATIVE_REQUIREMENT",
        "description": "Require comprehensive clinical documentation before approving high-cost services.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-04-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"], "network": ["IN"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": False},
        "policy_levers": [{"lever_type": "ADMINISTRATIVE_REQUIREMENT", "parameters": {"requires_documentation": True, "documentation_types": ["CLINICAL_NOTES", "IMAGING_REPORTS"], "codes": ["70551", "75574"]}}],
        "expected_behavioral_response": ["IMPROVED_DOCUMENTATION", "APPROPRIATE_USE"],
        "analytics_expectations": {"primary_metrics": ["DOCUMENTATION_COMPLETENESS", "APPROVAL_RATE"], "lag_days": [30]},
        "ui_hints": {"show_documentation_checklist": True},
        "assumptions": [{"assumption_type": "UTILIZATION", "description": "10-15% reduction in inappropriate approvals", "value": "0.10-0.15", "confidence": 0.65}],
        "guardrails": [{"metric_name": "documentation_completeness", "threshold_type": "min", "threshold_value": 0.90, "action": "alert"}],
        "inputs": {"data_sources": ["prior_auth", "documentation"], "required_fields": ["documentation_status", "clinical_notes"]},
        "outputs": {"metrics": ["documentation_rate", "approval_quality"], "reports": ["monthly_documentation_report"]},
        "version": 1
    },
    {
        "policy_id": "AAR_WAIT_027",
        "policy_name": "Maximum Wait Time for Specialist Appointments",
        "policy_type": "ACCESS_AVAILABILITY_RULE",
        "description": "Enforce maximum wait times for specialist appointments to ensure timely access.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-05-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"], "network": ["IN"]},
        "enforcement": {"mechanism": "SOFT", "touchpoint": ["AUTHORIZATION"], "override_allowed": True},
        "policy_levers": [{"lever_type": "ACCESS_AVAILABILITY_RULE", "parameters": {"max_wait_days": 14, "specialty_types": ["CARDIOLOGY", "DERMATOLOGY"], "monitoring_frequency": "MONTHLY"}}],
        "expected_behavioral_response": ["IMPROVED_ACCESS", "NETWORK_EXPANSION"],
        "analytics_expectations": {"primary_metrics": ["AVERAGE_WAIT_TIME", "ACCESS_SCORES"], "lag_days": [30, 60]},
        "ui_hints": {"show_wait_time_dashboard": True},
        "assumptions": [{"assumption_type": "ACCESS", "description": "Improved member satisfaction with timely access", "value": "15-20% improvement", "confidence": 0.70}],
        "guardrails": [{"metric_name": "average_wait_time", "threshold_type": "max", "threshold_value": 21, "action": "alert"}],
        "inputs": {"data_sources": ["appointments", "network"], "required_fields": ["appointment_date", "request_date"]},
        "outputs": {"metrics": ["wait_time", "access_scores"], "reports": ["monthly_access_report"]},
        "version": 1
    },
    {
        "policy_id": "COMPOUND_SPECIALTY_028",
        "policy_name": "Specialty Drug Comprehensive Management",
        "policy_type": "COMPOSITE",
        "description": "Combined step therapy, prior auth, quantity limits, and clinical criteria for specialty drugs.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"], "network": ["IN", "OON"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": True},
        "policy_levers": [
            {"lever_type": "STEP_THERAPY", "parameters": {"target_codes": ["J0135"], "required_trials": ["CONVENTIONAL_DMARD"]}},
            {"lever_type": "PRIOR_AUTH", "parameters": {"codes": ["J0135"], "requires_clinical_criteria": True}},
            {"lever_type": "QUANTITY_LIMIT", "parameters": {"codes": ["J0135"], "max_units_per_month": 4}},
            {"lever_type": "CLINICAL_CRITERIA", "parameters": {"requires_diagnosis_confirmation": True}}
        ],
        "expected_behavioral_response": ["COST_CONTROL", "APPROPRIATE_USE", "QUALITY_IMPROVEMENT"],
        "analytics_expectations": {"primary_metrics": ["SPECIALTY_DRUG_UTIL", "COST_PMPM"], "lag_days": [90, 180]},
        "ui_hints": {"show_compound_policy": True, "require_warning_ack": True},
        "assumptions": [{"assumption_type": "COST", "description": "20-25% reduction in specialty drug costs", "value": "0.20-0.25", "confidence": 0.75}],
        "guardrails": [{"metric_name": "specialty_drug_cost_pmpm", "threshold_type": "max", "threshold_value": 150, "action": "alert"}],
        "inputs": {"data_sources": ["pharmacy_claims", "prior_auth"], "required_fields": ["ndc", "diagnosis", "prior_therapy"]},
        "outputs": {"metrics": ["specialty_util", "cost_savings"], "reports": ["quarterly_specialty_report"]},
        "version": 1
    },
    {
        "policy_id": "COV_EXPERIMENTAL_029",
        "policy_name": "Experimental Treatment Coverage Exclusion",
        "policy_type": "COVERAGE",
        "description": "Exclude experimental and investigational treatments from coverage unless part of approved clinical trial.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2023-01-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA", "MEDICAID"], "markets": ["ALL"], "network": ["ALL"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["CLAIM_EDIT"], "override_allowed": False},
        "policy_levers": [{"lever_type": "COVERAGE", "parameters": {"excluded_codes": ["EXPERIMENTAL"], "clinical_trial_exception": True}}],
        "expected_behavioral_response": ["COST_CONTROL", "EVIDENCE_BASED_CARE"],
        "analytics_expectations": {"primary_metrics": ["EXPERIMENTAL_CLAIMS", "COST_AVOIDANCE"], "lag_days": [30]},
        "ui_hints": {"show_coverage_rules": True},
        "assumptions": [{"assumption_type": "COST", "description": "Prevents high-cost experimental claims", "value": "Cost avoidance", "confidence": 0.90}],
        "guardrails": [{"metric_name": "experimental_claim_count", "threshold_type": "max", "threshold_value": 10, "action": "alert"}],
        "inputs": {"data_sources": ["claims"], "required_fields": ["treatment_type", "clinical_trial_flag"]},
        "outputs": {"metrics": ["excluded_claims", "cost_avoidance"], "reports": ["annual_coverage_report"]},
        "version": 1
    },
    {
        "policy_id": "BEN_ANNUAL_MAX_030",
        "policy_name": "Annual Maximum Benefit for Durable Medical Equipment",
        "policy_type": "BENEFIT",
        "description": "Set annual maximum benefit limit for DME purchases per member.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-01-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MEDICAID"], "markets": ["ALL"], "network": ["ALL"], "applies_to_all": True},
        "enforcement": {"mechanism": "PASSIVE", "touchpoint": ["BENEFIT_ACCUMULATOR"], "override_allowed": False},
        "policy_levers": [{"lever_type": "BENEFIT", "parameters": {"annual_maximum": 5000, "dme_category": "ALL", "reset_period": "CALENDAR_YEAR"}}],
        "expected_behavioral_response": ["COST_CAPPING", "BUDGET_PREDICTABILITY"],
        "analytics_expectations": {"primary_metrics": ["DME_COST_PMPM", "ANNUAL_UTIL"], "lag_days": [90]},
        "ui_hints": {"show_accumulator": True},
        "assumptions": [{"assumption_type": "COST", "description": "Predictable annual DME costs capped at $5K per member", "value": "5000", "confidence": 0.85}],
        "guardrails": [{"metric_name": "dme_cost_pmpm", "threshold_type": "max", "threshold_value": 50, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "accumulators"], "required_fields": ["dme_category", "annual_spend"]},
        "outputs": {"metrics": ["dme_utilization", "cost_trends"], "reports": ["annual_benefit_report"]},
        "version": 1
    },
    {
        "policy_id": "COMPOUND_IMAGING_031",
        "policy_name": "Advanced Imaging Comprehensive Control",
        "policy_type": "COMPOSITE",
        "description": "Combined prior auth, frequency limits, site of care, and clinical criteria for advanced imaging.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-03-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL"], "markets": ["NYC", "DFW", "CHICAGO"], "network": ["IN"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"], "override_allowed": False},
        "policy_levers": [
            {"lever_type": "PRIOR_AUTH", "parameters": {"codes": ["70551", "75574"], "requires_auc": True}},
            {"lever_type": "DURATION_FREQUENCY_LIMIT", "parameters": {"codes": ["70551", "75574"], "max_visits": 2, "time_period": "YEAR"}},
            {"lever_type": "SITE_OF_CARE", "parameters": {"preferred_sites": ["FREESTANDING"], "disallowed_sites": ["HOSPITAL_OP"]}},
            {"lever_type": "CLINICAL_CRITERIA", "parameters": {"requires_appropriate_use_criteria": True}}
        ],
        "expected_behavioral_response": ["STRONG_UTIL_REDUCTION", "COST_OPTIMIZATION", "APPROPRIATE_USE"],
        "analytics_expectations": {"primary_metrics": ["IMAGING_UTIL", "AUC_COMPLIANCE", "COST_PMPM"], "lag_days": [90, 180]},
        "ui_hints": {"show_compound_policy": True, "show_auc_tool": True, "require_warning_ack": True},
        "assumptions": [{"assumption_type": "ELASTICITY", "description": "15-20% reduction in advanced imaging utilization", "value": "0.15-0.20", "confidence": 0.80}],
        "guardrails": [{"metric_name": "imaging_util_per_1k", "threshold_type": "max", "threshold_value": 150, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "prior_auth", "imaging_reports"], "required_fields": ["imaging_type", "auc_score", "site_of_care"]},
        "outputs": {"metrics": ["imaging_util", "auc_compliance", "cost_savings"], "reports": ["quarterly_imaging_report"]},
        "version": 1
    },
    {
        "policy_id": "COMPOUND_SURGERY_032",
        "policy_name": "Elective Surgery Comprehensive Management",
        "policy_type": "COMPOSITE",
        "description": "Combined prior auth, conservative treatment trial, site of care, and network restrictions for elective surgeries.",
        "status": "ACTIVE",
        "effective_period": {"start_date": "2024-04-01", "end_date": None},
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"], "network": ["IN"]},
        "enforcement": {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": True},
        "policy_levers": [
            {"lever_type": "PRIOR_AUTH", "parameters": {"codes": ["22551", "27447"], "requires_conservative_trial": True, "trial_duration_days": 90}},
            {"lever_type": "SITE_OF_CARE", "parameters": {"preferred_sites": ["ASC"], "disallowed_sites": ["HOSPITAL_OP"]}},
            {"lever_type": "NETWORK_RESTRICTION", "parameters": {"requires_high_volume_center": True, "min_annual_volume": 50}},
            {"lever_type": "CLINICAL_CRITERIA", "parameters": {"requires_functional_assessment": True}}
        ],
        "expected_behavioral_response": ["REDUCED_SURGERY_RATE", "IMPROVED_OUTCOMES", "COST_SAVINGS"],
        "analytics_expectations": {"primary_metrics": ["SURGERY_RATE", "OUTCOMES", "COST_PMPM"], "lag_days": [90, 180, 365]},
        "ui_hints": {"show_compound_policy": True, "show_conservative_trial_tracking": True, "require_warning_ack": True},
        "assumptions": [{"assumption_type": "UTILIZATION", "description": "10-15% reduction in elective surgeries", "value": "0.10-0.15", "confidence": 0.75}],
        "guardrails": [{"metric_name": "surgery_rate_per_1k", "threshold_type": "max", "threshold_value": 25, "action": "alert"}],
        "inputs": {"data_sources": ["claims", "prior_auth", "outcomes"], "required_fields": ["surgery_type", "conservative_trial_status", "outcomes"]},
        "outputs": {"metrics": ["surgery_rate", "outcome_metrics", "cost_savings"], "reports": ["annual_surgery_report"]},
        "version": 1
    }
]

def enhance_policy_with_metadata(policy_data):
    """Add assumptions, guardrails, inputs, outputs, and versioning to existing policies"""
    enhanced = policy_data.copy()
    
    # Add default assumptions if not present
    if "assumptions" not in enhanced:
        enhanced["assumptions"] = [{
            "assumption_type": "ELASTICITY",
            "description": f"Expected impact for {enhanced.get('policy_name', 'policy')}",
            "value": "TBD",
            "confidence": 0.5,
            "source": "Initial estimate"
        }]
    
    # Add default guardrails if not present
    if "guardrails" not in enhanced:
        enhanced["guardrails"] = [{
            "metric_name": "utilization_rate",
            "threshold_type": "change_pct",
            "threshold_value": 20.0,
            "action": "alert",
            "description": f"Monitor utilization changes for {enhanced.get('policy_name', 'policy')}"
        }]
    
    # Add default inputs if not present
    if "inputs" not in enhanced:
        enhanced["inputs"] = {
            "data_sources": ["claims"],
            "required_fields": ["member_id", "service_date"]
        }
    
    # Add default outputs if not present
    if "outputs" not in enhanced:
        enhanced["outputs"] = {
            "metrics": ["utilization_rate", "cost_pmpm"],
            "reports": ["monthly_utilization_report"]
        }
    
    # Add version if not present
    if "version" not in enhanced:
        enhanced["version"] = 1
    
    return enhanced

def main():
    """Seed all 32 policies with complete metadata"""
    print("=" * 80)
    print("Seeding All 32 Comprehensive Policies")
    print("=" * 80)
    
    # Enhance existing 20 policies
    all_policies = []
    for policy in EXISTING_POLICIES:
        enhanced = enhance_policy_with_metadata(policy)
        all_policies.append(enhanced)
    
    # Add 12 additional policies
    all_policies.extend(ADDITIONAL_POLICIES)
    
    print(f"📋 Total policies to seed: {len(all_policies)}")
    
    # Check existing policies
    existing_policies = list_policies(DEFAULT_TENANT_ID)
    # Filter out None values and ensure all items are dictionaries
    existing_policies = [p for p in existing_policies if p is not None and isinstance(p, dict)]
    existing_policy_ids = {p.get('policy_id') for p in existing_policies if p and p.get('policy_id')}
    print(f"📊 Found {len(existing_policies)} existing policies in database")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for policy_data in all_policies:
        policy_id = policy_data.get('policy_id')
        policy_name = policy_data.get('policy_name', 'Unknown')
        
        # Check if policy already exists (by name or policy_id in metadata)
        exists = False
        for existing in existing_policies:
            if existing and isinstance(existing, dict):
                if (existing.get('name') == policy_name or 
                    (existing.get('metadata', {}).get('policy_id') == policy_id)):
                    exists = True
                    break
        
        if exists:
            print(f"⏭️  Skipping existing policy: {policy_name} ({policy_id})")
            skipped_count += 1
            continue
        
        try:
            print(f"📝 Creating policy: {policy_name} ({policy_id})")
            
            # Convert to format expected by create_policy
            policy_dict = {
                'name': policy_name,
                'policy_type': policy_data.get('policy_type', 'PRIOR_AUTH'),
                'description': policy_data.get('description', ''),
                'status': policy_data.get('status', 'ACTIVE'),
                'scope': policy_data.get('scope', {}),
                'effective_period': policy_data.get('effective_period', {}),
                'enforcement': policy_data.get('enforcement', {}),
                'policy_levers': policy_data.get('policy_levers', []),
                'expected_behavioral_response': policy_data.get('expected_behavioral_response', []),
                'analytics_expectations': policy_data.get('analytics_expectations', {}),
                'ui_hints': policy_data.get('ui_hints', {}),
                'metadata': {
                    'policy_id': policy_id,
                    'assumptions': policy_data.get('assumptions', []),
                    'guardrails': policy_data.get('guardrails', []),
                    'inputs': policy_data.get('inputs', {}),
                    'outputs': policy_data.get('outputs', {}),
                    'version': policy_data.get('version', 1),
                }
            }
            
            created = create_policy(DEFAULT_TENANT_ID, policy_dict)
            if created:
                policy_uuid = UUID(created.get('id')) if isinstance(created.get('id'), str) else created.get('id')
                
                # Create assumptions
                for assumption_data in policy_data.get('assumptions', []):
                    try:
                        create_assumption(DEFAULT_TENANT_ID, policy_uuid, assumption_data)
                    except Exception as e:
                        print(f"  ⚠️  Warning: Failed to create assumption: {e}")
                
                # Create guardrails
                for guardrail_data in policy_data.get('guardrails', []):
                    try:
                        create_guardrail(DEFAULT_TENANT_ID, policy_uuid, guardrail_data)
                    except Exception as e:
                        print(f"  ⚠️  Warning: Failed to create guardrail: {e}")
                
                print(f"✅ Created policy: {policy_name}")
                created_count += 1
            else:
                print(f"❌ Failed to create policy: {policy_name}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error creating policy {policy_name}: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print("=" * 80)
    print(f"✅ Policy seeding complete: {created_count} created, {skipped_count} skipped, {error_count} errors")
    print(f"   Total policies in system: {len(existing_policies) + created_count}")
    print("=" * 80)
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

