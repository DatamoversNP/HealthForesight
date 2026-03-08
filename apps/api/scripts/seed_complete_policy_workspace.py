#!/usr/bin/env python3
"""
Seed complete policy workspace data for all predefined policies
Creates: Assumptions, Guardrails, Versions, Changelog, Decisions, Risk Registers
Links to: Predicted Impact, Baselines, What-If Scenarios
"""
import sys
import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import hashlib

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_policies import list_policies, get_policy
from uepi_api.storage_policy_assumptions import create_assumption
from uepi_api.storage_policy_guardrails import create_guardrail
from uepi_api.storage_policy_versions import create_policy_version
from uepi_api.storage_policy_changelog import create_changelog_entry
from uepi_api.storage_decisions import create_decision
from uepi_api.storage_risks import create_or_update_risk_register
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_api.storage_baselines import get_latest_baseline
from uepi_api.storage_scenarios import list_scenarios


def convert_policy_id_to_uuid(policy_id: str, tenant_id: UUID) -> UUID:
    """Convert string policy ID to UUID"""
    try:
        return UUID(policy_id)
    except ValueError:
        # Generate deterministic UUID from string ID
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())


def create_assumptions_for_policy(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create realistic assumptions for a policy"""
    policy_type = policy_data.get('policy_type', '').upper()
    assumptions = []
    
    # Common assumptions for all policies
    assumptions.append({
        "assumption_type": "ELASTICITY",
        "description": f"Price elasticity of demand for {policy_data.get('name', 'policy')}",
        "value": -0.3,  # Moderate elasticity
        "range": {
            "min_value": -0.5,
            "max_value": -0.1,
            "best_estimate": -0.3
        },
        "source": "Historical claims analysis",
        "confidence": 0.75
    })
    
    assumptions.append({
        "assumption_type": "SUBSTITUTION_RATE",
        "description": "Expected substitution to alternative services",
        "value": 0.15,  # 15% substitution
        "range": {
            "min_value": 0.05,
            "max_value": 0.25,
            "best_estimate": 0.15
        },
        "source": "Provider behavior modeling",
        "confidence": 0.70
    })
    
    assumptions.append({
        "assumption_type": "LAG_DAYS",
        "description": "Expected lag before policy impact is observed",
        "value": 60,  # 60 days
        "range": {
            "min_value": 30,
            "max_value": 90,
            "best_estimate": 60
        },
        "source": "Policy implementation timeline",
        "confidence": 0.80
    })
    
    # Policy-type specific assumptions
    if "PRIOR_AUTH" in policy_type:
        assumptions.append({
            "assumption_type": "PA_APPROVAL_RATE",
            "description": "Expected prior authorization approval rate",
            "value": 0.65,  # 65% approval
            "range": {
                "min_value": 0.50,
                "max_value": 0.80,
                "best_estimate": 0.65
            },
            "source": "Historical PA data",
            "confidence": 0.75
        })
    
    if "STEP_THERAPY" in policy_type:
        assumptions.append({
            "assumption_type": "TRIAL_SUCCESS_RATE",
            "description": "Expected success rate of required trials",
            "value": 0.40,  # 40% success
            "range": {
                "min_value": 0.30,
                "max_value": 0.50,
                "best_estimate": 0.40
            },
            "source": "Clinical trial data",
            "confidence": 0.70
        })
    
    if "QUANTITY_LIMIT" in policy_type:
        assumptions.append({
            "assumption_type": "COMPLIANCE_RATE",
            "description": "Expected provider compliance rate",
            "value": 0.85,  # 85% compliance
            "range": {
                "min_value": 0.75,
                "max_value": 0.95,
                "best_estimate": 0.85
            },
            "source": "Provider audit data",
            "confidence": 0.80
        })
    
    # Create assumptions
    for assumption_data in assumptions:
        try:
            create_assumption(tenant_id, policy_id, assumption_data)
            print(f"  ✓ Created assumption: {assumption_data['assumption_type']}")
        except Exception as e:
            print(f"  ✗ Failed to create assumption {assumption_data['assumption_type']}: {e}")


def create_guardrails_for_policy(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create realistic guardrails for a policy"""
    policy_type = policy_data.get('policy_type', '').upper()
    guardrails = []
    
    # Common guardrails
    guardrails.append({
        "metric_name": "UTILIZATION_INCREASE",
        "threshold_type": "max",
        "threshold_value": 0.20,  # 20% increase triggers alert
        "action": "alert",
        "description": "Alert if utilization increases more than 20% above baseline"
    })
    
    guardrails.append({
        "metric_name": "COST_INCREASE",
        "threshold_type": "max",
        "threshold_value": 0.15,  # 15% cost increase
        "action": "alert",
        "description": "Alert if cost per member per month increases more than 15%"
    })
    
    guardrails.append({
        "metric_name": "ER_UTILIZATION",
        "threshold_type": "max",
        "threshold_value": 0.10,  # 10% increase in ER visits
        "action": "alert",
        "description": "Alert if ER utilization increases more than 10% (potential substitution effect)"
    })
    
    # Policy-type specific guardrails
    if "PRIOR_AUTH" in policy_type:
        guardrails.append({
            "metric_name": "PA_DENIAL_RATE",
            "threshold_type": "max",
            "threshold_value": 0.50,  # 50% denial rate
            "action": "review",
            "description": "Review if PA denial rate exceeds 50%"
        })
    
    if "STEP_THERAPY" in policy_type:
        guardrails.append({
            "metric_name": "TRIAL_FAILURE_RATE",
            "threshold_type": "max",
            "threshold_value": 0.70,  # 70% failure rate
            "action": "review",
            "description": "Review if trial failure rate exceeds 70%"
        })
    
    # Create guardrails
    for guardrail_data in guardrails:
        try:
            create_guardrail(tenant_id, policy_id, guardrail_data)
            print(f"  ✓ Created guardrail: {guardrail_data['metric_name']}")
        except Exception as e:
            print(f"  ✗ Failed to create guardrail {guardrail_data['metric_name']}: {e}")


def create_versions_for_policy(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create initial version for a policy"""
    effective_start = policy_data.get('effective_period', {}).get('start_date')
    if not effective_start:
        effective_start = (datetime.utcnow() - timedelta(days=180)).isoformat()
    
    version_data = {
        "effective_start_date": effective_start,
        "effective_end_date": None,
        "state": policy_data.get('status', 'ACTIVE'),
        "change_summary": "Initial policy version",
        "change_details": {
            "policy_type": policy_data.get('policy_type'),
            "scope": policy_data.get('scope', {}),
            "enforcement": policy_data.get('enforcement', {})
        },
        "created_by": str(uuid4()),  # System user
        "created_at": effective_start
    }
    
    try:
        version = create_policy_version(tenant_id, policy_id, version_data)
        print(f"  ✓ Created version: v{version.version_number}")
        return version
    except Exception as e:
        print(f"  ✗ Failed to create version: {e}")
        return None


def create_changelog_for_policy(tenant_id: UUID, policy_id: UUID, policy_data: dict, version_number: int = 1):
    """Create initial changelog entries for a policy"""
    changelog_entries = [
        {
            "version_number": version_number,
            "changed_by": str(uuid4()),  # System user
            "change_type": "created",
            "field_name": "policy",
            "new_value": policy_data.get('name', 'Policy'),
            "reason": "Policy created"
        },
        {
            "version_number": version_number,
            "changed_by": str(uuid4()),
            "change_type": "updated",
            "field_name": "status",
            "old_value": "DRAFT",
            "new_value": policy_data.get('status', 'ACTIVE'),
            "reason": "Policy activated"
        }
    ]
    
    # Add changelog for scope if exists
    if policy_data.get('scope'):
        changelog_entries.append({
            "version_number": version_number,
            "changed_by": str(uuid4()),
            "change_type": "updated",
            "field_name": "scope",
            "new_value": policy_data.get('scope'),
            "reason": "Scope configured"
        })
    
    # Create changelog entries
    for entry_data in changelog_entries:
        try:
            entry_data["changed_at"] = datetime.utcnow().isoformat()
            create_changelog_entry(tenant_id, policy_id, entry_data)
        except Exception as e:
            print(f"  ✗ Failed to create changelog entry: {e}")
    
    print(f"  ✓ Created {len(changelog_entries)} changelog entries")


def create_decisions_for_policy(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create sample decisions for a policy"""
    decisions = [
        {
            "title": f"Initial Approval Decision for {policy_data.get('name', 'Policy')}",
            "recommendation": "APPROVE",
            "rationale": f"Policy {policy_data.get('name', '')} meets all criteria for implementation. Expected cost savings of 5-10% with minimal patient impact.",
            "confidence_score": 0.80,
            "status": "FINALIZED",
            "policy_id": str(policy_id),
            "created_by": str(uuid4()),
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Create decisions
    for decision_data in decisions:
        try:
            decision = create_decision(tenant_id, decision_data)
            print(f"  ✓ Created decision: {decision.title}")
        except Exception as e:
            print(f"  ✗ Failed to create decision: {e}")


def create_risk_register_for_policy(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create risk register for a policy"""
    risk_drivers = [
        {
            "driver_name": "Provider Non-Compliance",
            "impact_score": 0.6,
            "uncertainty_contribution": 0.3,
            "mitigation_action": "Provider education and monitoring",
            "owner": None
        },
        {
            "driver_name": "Substitution Effects",
            "impact_score": 0.5,
            "uncertainty_contribution": 0.4,
            "mitigation_action": "Monitor ER utilization and alternative service use",
            "owner": None
        },
        {
            "driver_name": "Patient Access Issues",
            "impact_score": 0.4,
            "uncertainty_contribution": 0.2,
            "mitigation_action": "Exception process and appeals workflow",
            "owner": None
        }
    ]
    
    risk_data = {
        "policy_id": str(policy_id),
        "top_drivers": risk_drivers,
        "overall_risk_score": 0.5,  # Moderate risk
        "last_updated": datetime.utcnow().isoformat()
    }
    
    try:
        risk_register = create_or_update_risk_register(tenant_id, risk_data)
        print(f"  ✓ Created risk register with {len(risk_drivers)} risk drivers")
    except Exception as e:
        print(f"  ✗ Failed to create risk register: {e}")


def link_to_baseline(tenant_id: UUID, policy_id: UUID):
    """Link policy to latest baseline if available"""
    try:
        baseline = get_latest_baseline(tenant_id)
        if baseline:
            print(f"  ✓ Baseline available: {baseline.get('baseline_id', 'N/A')}")
            return True
        else:
            print(f"  ⚠ No baseline available")
            return False
    except Exception as e:
        print(f"  ⚠ Could not check baseline: {e}")
        return False


def link_to_scenarios(tenant_id: UUID, policy_id: UUID):
    """Link policy to what-if scenarios if available"""
    try:
        scenarios = list_scenarios(tenant_id, policy_id=policy_id)
        if scenarios:
            print(f"  ✓ Found {len(scenarios)} scenarios linked to policy")
            return True
        else:
            print(f"  ⚠ No scenarios linked to policy")
            return False
    except Exception as e:
        print(f"  ⚠ Could not check scenarios: {e}")
        return False


def main():
    """Seed complete workspace data for all policies"""
    tenant_id = DEFAULT_TENANT_ID
    print(f"🌱 Seeding complete policy workspace data for tenant: {tenant_id}")
    print("=" * 80)
    
    # Get all policies
    try:
        policies = list_policies(tenant_id)
        print(f"\n📋 Found {len(policies)} policies to seed\n")
    except Exception as e:
        print(f"❌ Failed to load policies: {e}")
        return
    
    # Process each policy
    for policy in policies:
        policy_id_str = policy.get('policy_id') or policy.get('id')
        policy_name = policy.get('name') or policy.get('policy_name', 'Unknown')
        
        print(f"\n📌 Processing: {policy_name} ({policy_id_str})")
        print("-" * 80)
        
        # Convert policy ID to UUID
        try:
            policy_uuid = convert_policy_id_to_uuid(str(policy_id_str), tenant_id)
        except Exception as e:
            print(f"  ✗ Failed to convert policy ID: {e}")
            continue
        
        # Create assumptions
        print("  Creating assumptions...")
        create_assumptions_for_policy(tenant_id, policy_uuid, policy)
        
        # Create guardrails
        print("  Creating guardrails...")
        create_guardrails_for_policy(tenant_id, policy_uuid, policy)
        
        # Create versions
        print("  Creating versions...")
        version = create_versions_for_policy(tenant_id, policy_uuid, policy)
        version_number = version.version_number if version else 1
        
        # Create changelog
        print("  Creating changelog...")
        create_changelog_for_policy(tenant_id, policy_uuid, policy, version_number)
        
        # Create decisions
        print("  Creating decisions...")
        create_decisions_for_policy(tenant_id, policy_uuid, policy)
        
        # Create risk register
        print("  Creating risk register...")
        create_risk_register_for_policy(tenant_id, policy_uuid, policy)
        
        # Link to baseline
        print("  Checking baseline link...")
        link_to_baseline(tenant_id, policy_uuid)
        
        # Link to scenarios
        print("  Checking scenario links...")
        link_to_scenarios(tenant_id, policy_uuid)
        
        print(f"  ✅ Completed: {policy_name}")
    
    print("\n" + "=" * 80)
    print("🎉 Seeding complete!")
    print(f"   Processed {len(policies)} policies")
    print("=" * 80)


if __name__ == "__main__":
    main()

