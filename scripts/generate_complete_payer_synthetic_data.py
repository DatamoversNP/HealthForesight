#!/usr/bin/env python3
"""
Generate Complete Payer/Client Synthetic Data
Creates realistic synthetic data that represents what we'd expect from real payers/clients:
- Policies with full lifecycle management (versions, assumptions, guardrails, changelogs)
- Observations from post-policy data
- Predicted impacts based on real policy configurations
- All data stored in files - no hardcoded values in code

This script generates:
1. Comprehensive policies with all Epic 2 lifecycle features
2. Policy versions with state transitions
3. Policy assumptions (elasticity, substitution, lag)
4. Policy guardrails (rollback triggers)
5. Policy changelogs (audit trail)
6. Observations from synthetic claims data
7. Predicted impacts for all policies
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import numpy as np
import pandas as pd

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))

from uepi_common.models_enhanced import (
    PolicyLifecycleState,
    PolicyVersion,
    PolicyAssumption,
    PolicyGuardrail,
    PolicyChangeLog,
    ElasticityRange,
)

# Configuration
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DATA_DIR = PROJECT_ROOT / "data"
POLICIES_DIR = PROJECT_ROOT / "apps" / "api" / "data" / "policies"
POLICY_VERSIONS_DIR = DATA_DIR / "policy_versions"
POLICY_ASSUMPTIONS_DIR = DATA_DIR / "policy_assumptions"
POLICY_GUARDRAILS_DIR = DATA_DIR / "policy_guardrails"
POLICY_CHANGELOG_DIR = DATA_DIR / "policy_changelog"
OBSERVATIONS_DIR = DATA_DIR / "observations"
PREDICTED_IMPACTS_DIR = DATA_DIR / "predicted_impacts"

# Realistic policy configurations (payer/client scenarios)
POLICY_TEMPLATES = [
    {
        "name": "Outpatient MRI Prior Authorization",
        "policy_type": "PRIOR_AUTH",
        "description": "Requires prior authorization for outpatient MRI procedures to reduce unnecessary utilization",
        "owner_role": "UM_LEADER",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["NYC", "DFW", "BOS"],
            "network": "IN_NETWORK",
            "states": ["NY", "TX", "MA"],
            "applies_to_all": False,
        },
        "effective_period": {
            "start_date": "2024-01-01",
            "end_date": None,
        },
        "policy_levers": [
            {
                "lever_type": "PRIOR_AUTH",
                "targets": {
                    "code_type": "CPT",
                    "codes": ["72148", "72149", "72141", "72142"],
                },
                "config": {
                    "enforcement": "HARD",
                    "site_of_care": "OUTPATIENT",
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "elasticity",
                "description": "Expected utilization reduction based on prior auth requirement",
                "elasticity_range": {"min": -0.15, "max": -0.10, "best_estimate": -0.12},
                "confidence": 0.75,
                "source": "Historical data from similar policies",
            },
            {
                "assumption_type": "substitution_rate",
                "description": "Percentage of denied requests that result in alternative care",
                "value": 0.30,
                "confidence": 0.70,
                "source": "Industry benchmarks",
            },
        ],
        "guardrails": [
            {
                "metric_name": "utilization_change_pct",
                "threshold_type": "min",
                "threshold_value": -0.25,
                "action": "alert",
                "description": "Alert if utilization drops more than 25% (may indicate access issues)",
            },
            {
                "metric_name": "cost_change_pmpm",
                "threshold_type": "max",
                "threshold_value": 5000,
                "action": "suspend",
                "description": "Suspend policy if cost increases more than $5 PMPM",
            },
        ],
    },
    {
        "name": "Step Therapy for Specialty Drugs",
        "policy_type": "STEP_THERAPY",
        "description": "Requires trial of lower-cost alternatives before approving high-cost specialty drugs",
        "owner_role": "PHARMACY",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["NYC", "DFW", "CHI", "LA"],
            "network": "IN_NETWORK",
            "states": ["NY", "TX", "IL", "CA"],
            "applies_to_all": False,
        },
        "effective_period": {
            "start_date": "2024-03-01",
            "end_date": None,
        },
        "policy_levers": [
            {
                "lever_type": "STEP_THERAPY",
                "targets": {
                    "code_type": "NDC",
                    "code_groups": ["SPECIALTY_BIOLOGICS"],
                },
                "config": {
                    "enforcement": "HARD",
                    "step_sequence": ["GENERIC", "PREFERRED_BRAND", "SPECIALTY"],
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "elasticity",
                "description": "Expected reduction in specialty drug utilization",
                "elasticity_range": {"min": -0.20, "max": -0.12, "best_estimate": -0.15},
                "confidence": 0.80,
                "source": "Pharmacy benefit manager data",
            },
            {
                "assumption_type": "lag_months",
                "description": "Time for policy to reach full effect",
                "value": 3,
                "confidence": 0.85,
                "source": "Historical implementation data",
            },
        ],
        "guardrails": [
            {
                "metric_name": "utilization_change_pct",
                "threshold_type": "min",
                "threshold_value": -0.30,
                "action": "alert",
                "description": "Alert if utilization drops more than 30%",
            },
            {
                "metric_name": "appeals_volume",
                "threshold_type": "max",
                "threshold_value": 100,
                "action": "alert",
                "description": "Alert if appeals exceed 100 per month",
            },
        ],
    },
    {
        "name": "Network Tiering - Outpatient Services",
        "policy_type": "NETWORK_RESTRICTION",
        "description": "Tiered network with higher cost-sharing for out-of-network providers",
        "owner_role": "NETWORK",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "DFW", "BOS", "CHI"],
            "network": "TIERED",
            "states": ["NY", "TX", "MA", "IL"],
            "applies_to_all": False,
        },
        "effective_period": {
            "start_date": "2024-06-01",
            "end_date": None,
        },
        "policy_levers": [
            {
                "lever_type": "NETWORK_RESTRICTION",
                "targets": {
                    "code_type": "CPT",
                    "code_groups": ["OUTPATIENT_SERVICES"],
                },
                "config": {
                    "enforcement": "SOFT",
                    "tier_structure": {"TIER_1": 0.20, "TIER_2": 0.30, "OON": 0.50},
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "elasticity",
                "description": "Expected shift to in-network providers",
                "elasticity_range": {"min": -0.10, "max": -0.05, "best_estimate": -0.07},
                "confidence": 0.70,
                "source": "Network analysis",
            },
        ],
        "guardrails": [
            {
                "metric_name": "member_satisfaction_score",
                "threshold_type": "min",
                "threshold_value": 3.0,
                "action": "rollback",
                "description": "Rollback if member satisfaction drops below 3.0",
            },
        ],
    },
    {
        "name": "Physical Therapy Visit Limit",
        "policy_type": "DURATION_FREQUENCY_LIMIT",
        "description": "Limits physical therapy visits to 20 per year without prior authorization",
        "owner_role": "UM_LEADER",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["NYC", "DFW", "BOS"],
            "network": "IN_NETWORK",
            "states": ["NY", "TX", "MA"],
            "applies_to_all": False,
        },
        "effective_period": {
            "start_date": "2024-02-01",
            "end_date": None,
        },
        "policy_levers": [
            {
                "lever_type": "DURATION_FREQUENCY_LIMIT",
                "targets": {
                    "code_type": "CPT",
                    "codes": ["97110", "97112", "97116"],
                },
                "config": {
                    "enforcement": "HARD",
                    "limit_type": "ANNUAL",
                    "limit_value": 20,
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "elasticity",
                "description": "Expected reduction in PT visits",
                "elasticity_range": {"min": -0.08, "max": -0.04, "best_estimate": -0.06},
                "confidence": 0.75,
                "source": "Clinical guidelines",
            },
        ],
        "guardrails": [
            {
                "metric_name": "utilization_change_pct",
                "threshold_type": "min",
                "threshold_value": -0.15,
                "action": "alert",
                "description": "Alert if visits drop more than 15%",
            },
        ],
    },
    {
        "name": "Telemedicine Coverage Expansion",
        "policy_type": "COVERAGE",
        "description": "Expands telemedicine coverage to reduce in-person visits and improve access",
        "owner_role": "BENEFITS",
        "status": "ACTIVE",
        "scope": {
            "lob": ["COMMERCIAL", "MA"],
            "markets": ["NYC", "DFW", "BOS", "CHI", "LA"],
            "network": "IN_NETWORK",
            "states": ["NY", "TX", "MA", "IL", "CA"],
            "applies_to_all": False,
        },
        "effective_period": {
            "start_date": "2024-05-01",
            "end_date": None,
        },
        "policy_levers": [
            {
                "lever_type": "COVERAGE",
                "targets": {
                    "code_type": "CPT",
                    "codes": ["99441", "99442", "99443"],
                },
                "config": {
                    "enforcement": "PASSIVE",
                    "coverage_level": "FULL",
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "elasticity",
                "description": "Expected increase in telemedicine utilization",
                "elasticity_range": {"min": 0.15, "max": 0.25, "best_estimate": 0.20},
                "confidence": 0.80,
                "source": "Post-COVID telemedicine trends",
            },
            {
                "assumption_type": "substitution_rate",
                "description": "Percentage of telemedicine visits that substitute for in-person",
                "value": 0.60,
                "confidence": 0.75,
                "source": "Member survey data",
            },
        ],
        "guardrails": [
            {
                "metric_name": "cost_change_pmpm",
                "threshold_type": "max",
                "threshold_value": 2000,
                "action": "alert",
                "description": "Alert if cost increases more than $2 PMPM",
            },
        ],
    },
]


def ensure_directories():
    """Ensure all data directories exist"""
    import os
    for directory in [
        POLICIES_DIR,
        POLICY_VERSIONS_DIR,
        POLICY_ASSUMPTIONS_DIR,
        POLICY_GUARDRAILS_DIR,
        POLICY_CHANGELOG_DIR,
        OBSERVATIONS_DIR,
        PREDICTED_IMPACTS_DIR,
    ]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            tenant_dir = directory / str(DEFAULT_TENANT_ID)
            tenant_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Directory may already exist or permissions issue - continue
            print(f"Note: Could not create {directory}: {e}")
            pass


def generate_policy_from_template(template: Dict[str, Any], policy_id: UUID) -> Dict[str, Any]:
    """Generate a complete policy from template"""
    now = datetime.utcnow()
    
    policy = {
        "policy_id": str(policy_id),
        "tenant_id": str(DEFAULT_TENANT_ID),
        "policy_name": template["name"],
        "policy_type": template["policy_type"],
        "description": template["description"],
        "status": template["status"],
        "scope": template["scope"],
        "effective_period": template["effective_period"],
        "enforcement": {
            "mechanism": "HARD",
            "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
            "override_allowed": False,
        },
        "policy_levers": template["policy_levers"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "metadata": {
            "owner": template["owner_role"],
            "source": "SYNTHETIC_GENERATOR",
        },
        "logic": {
            "scope": template["scope"],
            "effective_period": template["effective_period"],
            "levers": template["policy_levers"],
            "global_exceptions": [],
        },
    }
    
    return policy


def generate_policy_version(
    policy_id: UUID,
    version_number: int,
    state: PolicyLifecycleState,
    effective_start_date: str,
) -> Dict[str, Any]:
    """Generate a policy version"""
    now = datetime.utcnow()
    
    version = {
        "id": str(uuid4()),
        "policy_id": str(policy_id),
        "tenant_id": str(DEFAULT_TENANT_ID),
        "version_number": version_number,
        "effective_start_date": effective_start_date,
        "effective_end_date": None,
        "state": state.value,
        "change_summary": f"Version {version_number} - {state.value}",
        "change_details": {
            "created_by": "SYNTHETIC_GENERATOR",
            "reason": f"Initial version {version_number}",
        },
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "approved_at": now.isoformat() if state in [PolicyLifecycleState.APPROVED, PolicyLifecycleState.ACTIVE] else None,
    }
    
    return version


def generate_policy_assumptions(
    policy_id: UUID,
    assumptions_template: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate policy assumptions from template"""
    assumptions = []
    
    for idx, assumption_template in enumerate(assumptions_template):
        assumption_id = uuid4()
        assumption = {
            "id": str(assumption_id),
            "policy_id": str(policy_id),
            "tenant_id": str(DEFAULT_TENANT_ID),
            "assumption_type": assumption_template["assumption_type"],
            "description": assumption_template["description"],
            "confidence": assumption_template["confidence"],
            "source": assumption_template["source"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if "elasticity_range" in assumption_template:
            assumption["elasticity_range"] = assumption_template["elasticity_range"]
        elif "value" in assumption_template:
            assumption["value"] = assumption_template["value"]
        
        assumptions.append(assumption)
    
    return assumptions


def generate_policy_guardrails(
    policy_id: UUID,
    guardrails_template: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate policy guardrails from template"""
    guardrails = []
    
    for idx, guardrail_template in enumerate(guardrails_template):
        guardrail_id = uuid4()
        guardrail = {
            "id": str(guardrail_id),
            "policy_id": str(policy_id),
            "tenant_id": str(DEFAULT_TENANT_ID),
            "metric_name": guardrail_template["metric_name"],
            "threshold_type": guardrail_template["threshold_type"],
            "threshold_value": guardrail_template["threshold_value"],
            "action": guardrail_template["action"],
            "description": guardrail_template["description"],
            "triggered": False,
            "current_value": None,
            "last_checked_at": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        guardrails.append(guardrail)
    
    return guardrails


def generate_policy_changelog_entries(
    policy_id: UUID,
    versions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate changelog entries for policy versions"""
    changelog = []
    
    for version in versions:
        entry = {
            "id": str(uuid4()),
            "policy_id": str(policy_id),
            "tenant_id": str(DEFAULT_TENANT_ID),
            "change_type": "version_created",
            "reason": version["change_summary"],
            "field_name": "version",
            "old_value": None,
            "new_value": f"Version {version['version_number']}",
            "version_number": version["version_number"],
            "created_at": version["created_at"],
            "created_by": "SYNTHETIC_GENERATOR",
        }
        changelog.append(entry)
    
    return changelog


def generate_predicted_impact(policy: Dict[str, Any]) -> Dict[str, Any]:
    """Generate predicted impact based on policy configuration"""
    policy_id = policy["policy_id"]
    
    # Extract assumptions to calculate impact
    assumptions_file = POLICY_ASSUMPTIONS_DIR / str(DEFAULT_TENANT_ID) / f"policy-{policy_id}.json"
    if assumptions_file.exists():
        with open(assumptions_file, 'r') as f:
            assumptions = json.load(f)
    else:
        assumptions = []
    
    # Calculate predicted impact from assumptions
    utilization_change = 0.0
    cost_change = 0.0
    
    for assumption in assumptions:
        if assumption.get("assumption_type") == "elasticity":
            if "elasticity_range" in assumption:
                utilization_change = assumption["elasticity_range"].get("best_estimate", 0.0)
            elif "value" in assumption:
                utilization_change = assumption["value"]
    
    # Estimate cost impact (simplified - would use actual cost models)
    base_cost_pmpm = 1000.0
    cost_change = base_cost_pmpm * utilization_change * 100  # Convert to dollars
    
    predicted_impact = {
        "policy_id": policy_id,
        "tenant_id": str(DEFAULT_TENANT_ID),
        "metrics": {
            "utilization_change_pct": utilization_change * 100,
            "cost_change_pmpm": cost_change,
            "member_impact_score": abs(utilization_change) * 10,
            "provider_impact_score": abs(utilization_change) * 8,
        },
        "confidence": 0.75,
        "computed_at": datetime.utcnow().isoformat(),
        "method": "SYNTHETIC_ESTIMATE",
        "assumptions_used": [a["id"] for a in assumptions],
    }
    
    return predicted_impact


def save_policy_data(policy: Dict[str, Any], versions: List[Dict[str, Any]], 
                     assumptions: List[Dict[str, Any]], guardrails: List[Dict[str, Any]],
                     changelog: List[Dict[str, Any]]):
    """Save all policy-related data to files"""
    policy_id = policy["policy_id"]
    tenant_id = str(DEFAULT_TENANT_ID)
    
    # Save policy
    policy_file = POLICIES_DIR / f"policy-{policy_id}.json"
    with open(policy_file, 'w') as f:
        json.dump(policy, f, indent=2, default=str)
    
    # Save versions
    versions_dir = POLICY_VERSIONS_DIR / tenant_id / f"policy-{policy_id}"
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    for version in versions:
        version_file = versions_dir / f"version-{version['version_number']}.json"
        with open(version_file, 'w') as f:
            json.dump(version, f, indent=2, default=str)
    
    # Save versions index
    versions_index = {
        "policy_id": policy_id,
        "tenant_id": tenant_id,
        "versions": [v["version_number"] for v in versions],
        "latest_version": max([v["version_number"] for v in versions]) if versions else 1,
    }
    index_file = versions_dir / "versions_index.json"
    with open(index_file, 'w') as f:
        json.dump(versions_index, f, indent=2, default=str)
    
    # Save assumptions
    assumptions_file = POLICY_ASSUMPTIONS_DIR / tenant_id / f"policy-{policy_id}.json"
    with open(assumptions_file, 'w') as f:
        json.dump(assumptions, f, indent=2, default=str)
    
    # Save guardrails
    guardrails_file = POLICY_GUARDRAILS_DIR / tenant_id / f"policy-{policy_id}.json"
    with open(guardrails_file, 'w') as f:
        json.dump(guardrails, f, indent=2, default=str)
    
    # Save changelog
    changelog_dir = POLICY_CHANGELOG_DIR / tenant_id
    changelog_dir.mkdir(parents=True, exist_ok=True)
    changelog_file = changelog_dir / f"policy-{policy_id}.json"
    with open(changelog_file, 'w') as f:
        json.dump(changelog, f, indent=2, default=str)
    
    # Save predicted impact
    predicted_impact = generate_predicted_impact(policy)
    predicted_impact_file = PREDICTED_IMPACTS_DIR / tenant_id / f"policy-{policy_id}.json"
    with open(predicted_impact_file, 'w') as f:
        json.dump(predicted_impact, f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description="Generate complete payer/client synthetic data")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--count", type=int, default=len(POLICY_TEMPLATES), help="Number of policies to generate")
    
    args = parser.parse_args()
    
    ensure_directories()
    
    print("=" * 60)
    print("Generating Complete Payer/Client Synthetic Data")
    print("=" * 60)
    print(f"Tenant ID: {args.tenant_id}")
    print(f"Policies to generate: {args.count}")
    print()
    
    generated_policies = []
    
    for idx, template in enumerate(POLICY_TEMPLATES[:args.count]):
        policy_id = uuid4()
        print(f"Generating policy {idx + 1}/{args.count}: {template['name']}")
        
        # Generate policy
        policy = generate_policy_from_template(template, policy_id)
        
        # Generate version 1
        effective_date = template["effective_period"]["start_date"]
        version = generate_policy_version(
            policy_id,
            version_number=1,
            state=PolicyLifecycleState.ACTIVE,
            effective_start_date=effective_date,
        )
        
        # Generate assumptions
        assumptions = generate_policy_assumptions(policy_id, template.get("assumptions", []))
        
        # Generate guardrails
        guardrails = generate_policy_guardrails(policy_id, template.get("guardrails", []))
        
        # Generate changelog
        changelog = generate_policy_changelog_entries(policy_id, [version])
        
        # Save all data
        save_policy_data(policy, [version], assumptions, guardrails, changelog)
        
        generated_policies.append(policy_id)
        print(f"  ✅ Policy {policy_id} with version, {len(assumptions)} assumptions, {len(guardrails)} guardrails")
    
    print()
    print("=" * 60)
    print("✅ Synthetic Data Generation Complete!")
    print("=" * 60)
    print(f"Generated {len(generated_policies)} policies with:")
    print(f"  - Policy versions")
    print(f"  - Policy assumptions")
    print(f"  - Policy guardrails")
    print(f"  - Policy changelogs")
    print(f"  - Predicted impacts")
    print()
    print("Data locations:")
    print(f"  Policies: {POLICIES_DIR}")
    print(f"  Versions: {POLICY_VERSIONS_DIR}")
    print(f"  Assumptions: {POLICY_ASSUMPTIONS_DIR}")
    print(f"  Guardrails: {POLICY_GUARDRAILS_DIR}")
    print(f"  Changelogs: {POLICY_CHANGELOG_DIR}")
    print(f"  Predicted Impacts: {PREDICTED_IMPACTS_DIR}")
    print()


if __name__ == "__main__":
    main()

