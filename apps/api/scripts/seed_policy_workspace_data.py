#!/usr/bin/env python3
"""
Seed complete policy workspace data - Direct JSON file creation
Creates: Assumptions, Guardrails, Versions, Changelog, Decisions, Risk Registers
This script writes JSON files directly to avoid import dependencies
"""
import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import hashlib
import os


BASE_PATH = Path(__file__).parent.parent.parent.parent / "data"
TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def convert_policy_id_to_uuid(policy_id: str) -> UUID:
    """Convert string policy ID to UUID"""
    try:
        return UUID(policy_id)
    except ValueError:
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())


def create_assumptions_file(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create assumptions JSON file"""
    policy_type = policy_data.get('policy_type', '').upper()
    assumptions = []
    
    # Common assumptions
    assumptions.append({
        "assumption_id": str(uuid4()),
        "assumption_type": "ELASTICITY",
        "description": f"Price elasticity of demand for {policy_data.get('name', 'policy')}",
        "value": -0.3,
        "range": {
            "min_value": -0.5,
            "max_value": -0.1,
            "best_estimate": -0.3
        },
        "source": "Historical claims analysis",
        "confidence": 0.75,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    assumptions.append({
        "assumption_id": str(uuid4()),
        "assumption_type": "SUBSTITUTION_RATE",
        "description": "Expected substitution to alternative services",
        "value": 0.15,
        "range": {
            "min_value": 0.05,
            "max_value": 0.25,
            "best_estimate": 0.15
        },
        "source": "Provider behavior modeling",
        "confidence": 0.70,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    assumptions.append({
        "assumption_id": str(uuid4()),
        "assumption_type": "LAG_DAYS",
        "description": "Expected lag before policy impact is observed",
        "value": 60,
        "range": {
            "min_value": 30,
            "max_value": 90,
            "best_estimate": 60
        },
        "source": "Policy implementation timeline",
        "confidence": 0.80,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    # Policy-type specific
    if "PRIOR_AUTH" in policy_type:
        assumptions.append({
            "assumption_id": str(uuid4()),
            "assumption_type": "PA_APPROVAL_RATE",
            "description": "Expected prior authorization approval rate",
            "value": 0.65,
            "range": {
                "min_value": 0.50,
                "max_value": 0.80,
                "best_estimate": 0.65
            },
            "source": "Historical PA data",
            "confidence": 0.75,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
    
    # Write file
    assumptions_dir = BASE_PATH / "policy_assumptions" / str(tenant_id)
    assumptions_dir.mkdir(parents=True, exist_ok=True)
    assumptions_file = assumptions_dir / f"policy-{policy_id}.json"
    
    with open(assumptions_file, 'w') as f:
        json.dump({"assumptions": assumptions}, f, indent=2)
    
    return len(assumptions)


def create_guardrails_file(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create guardrails JSON file"""
    policy_type = policy_data.get('policy_type', '').upper()
    guardrails = []
    
    guardrails.append({
        "guardrail_id": str(uuid4()),
        "metric_name": "UTILIZATION_INCREASE",
        "threshold_type": "max",
        "threshold_value": 0.20,
        "action": "alert",
        "description": "Alert if utilization increases more than 20% above baseline",
        "triggered": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    guardrails.append({
        "guardrail_id": str(uuid4()),
        "metric_name": "COST_INCREASE",
        "threshold_type": "max",
        "threshold_value": 0.15,
        "action": "alert",
        "description": "Alert if cost per member per month increases more than 15%",
        "triggered": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    guardrails.append({
        "guardrail_id": str(uuid4()),
        "metric_name": "ER_UTILIZATION",
        "threshold_type": "max",
        "threshold_value": 0.10,
        "action": "alert",
        "description": "Alert if ER utilization increases more than 10% (potential substitution effect)",
        "triggered": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    # Write file
    guardrails_dir = BASE_PATH / "policy_guardrails" / str(tenant_id)
    guardrails_dir.mkdir(parents=True, exist_ok=True)
    guardrails_file = guardrails_dir / f"policy-{policy_id}.json"
    
    with open(guardrails_file, 'w') as f:
        json.dump({"guardrails": guardrails}, f, indent=2)
    
    return len(guardrails)


def create_versions_file(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create versions JSON file"""
    effective_start = policy_data.get('effective_period', {}).get('start_date')
    if not effective_start:
        effective_start = (datetime.utcnow() - timedelta(days=180)).isoformat()
    
    version = {
        "version_number": 1,
        "policy_id": str(policy_id),
        "effective_start_date": effective_start,
        "effective_end_date": None,
        "state": policy_data.get('status', 'ACTIVE'),
        "change_summary": "Initial policy version",
        "change_details": {
            "policy_type": policy_data.get('policy_type'),
            "scope": policy_data.get('scope', {}),
            "enforcement": policy_data.get('enforcement', {})
        },
        "created_by": str(uuid4()),
        "created_at": effective_start,
        "approved_by": None,
        "approved_at": None
    }
    
    # Write file
    versions_dir = BASE_PATH / "policy_versions" / str(tenant_id) / f"policy-{policy_id}"
    versions_dir.mkdir(parents=True, exist_ok=True)
    version_file = versions_dir / "version-1.json"
    index_file = versions_dir / "versions_index.json"
    
    with open(version_file, 'w') as f:
        json.dump(version, f, indent=2, default=str)
    
    with open(index_file, 'w') as f:
        json.dump({
            "versions": [{
                "version_number": 1,
                "effective_start_date": effective_start,
                "effective_end_date": None,
                "state": version["state"],
                "change_summary": version["change_summary"],
                "created_at": effective_start
            }]
        }, f, indent=2)
    
    return 1


def create_changelog_file(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create changelog JSON file"""
    entries = [
        {
            "change_id": str(uuid4()),
            "policy_id": str(policy_id),
            "version_number": 1,
            "changed_by": str(uuid4()),
            "changed_at": datetime.utcnow().isoformat(),
            "change_type": "created",
            "field_name": "policy",
            "old_value": None,
            "new_value": policy_data.get('name', 'Policy'),
            "reason": "Policy created"
        },
        {
            "change_id": str(uuid4()),
            "policy_id": str(policy_id),
            "version_number": 1,
            "changed_by": str(uuid4()),
            "changed_at": datetime.utcnow().isoformat(),
            "change_type": "updated",
            "field_name": "status",
            "old_value": "DRAFT",
            "new_value": policy_data.get('status', 'ACTIVE'),
            "reason": "Policy activated"
        }
    ]
    
    # Write file
    changelog_dir = BASE_PATH / "policy_changelog" / str(tenant_id)
    changelog_dir.mkdir(parents=True, exist_ok=True)
    changelog_file = changelog_dir / f"policy-{policy_id}.json"
    
    with open(changelog_file, 'w') as f:
        json.dump({"entries": entries}, f, indent=2)
    
    return len(entries)


def create_risk_register_file(tenant_id: UUID, policy_id: UUID, policy_data: dict):
    """Create risk register JSON file"""
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
    
    risk_register = {
        "policy_id": str(policy_id),
        "top_drivers": risk_drivers,
        "overall_risk_score": 0.5,
        "last_updated": datetime.utcnow().isoformat()
    }
    
    # Write file
    risks_dir = BASE_PATH / "risks" / str(tenant_id)
    risks_dir.mkdir(parents=True, exist_ok=True)
    risk_file = risks_dir / f"risk-{policy_id}.json"
    
    with open(risk_file, 'w') as f:
        json.dump(risk_register, f, indent=2, default=str)
    
    return len(risk_drivers)


def main():
    """Seed workspace data for all policies"""
    print("🌱 Seeding complete policy workspace data")
    print("=" * 80)
    
    # Find all policy files
    policy_files = []
    policy_dir = BASE_PATH
    for pattern in ["policy_*.json", "policies/*.json"]:
        policy_files.extend(policy_dir.glob(pattern))
    
    print(f"\n📋 Found {len(policy_files)} policy files\n")
    
    for policy_file in policy_files:
        try:
            with open(policy_file, 'r') as f:
                policy_data = json.load(f)
            
            policy_id_str = policy_data.get('policy_id') or policy_data.get('id')
            policy_name = policy_data.get('name') or policy_data.get('policy_name', 'Unknown')
            
            print(f"\n📌 Processing: {policy_name} ({policy_id_str})")
            print("-" * 80)
            
            # Convert to UUID
            policy_uuid = convert_policy_id_to_uuid(str(policy_id_str))
            
            # Create all workspace data
            assumptions_count = create_assumptions_file(TENANT_ID, policy_uuid, policy_data)
            print(f"  ✓ Created {assumptions_count} assumptions")
            
            guardrails_count = create_guardrails_file(TENANT_ID, policy_uuid, policy_data)
            print(f"  ✓ Created {guardrails_count} guardrails")
            
            versions_count = create_versions_file(TENANT_ID, policy_uuid, policy_data)
            print(f"  ✓ Created {versions_count} version(s)")
            
            changelog_count = create_changelog_file(TENANT_ID, policy_uuid, policy_data)
            print(f"  ✓ Created {changelog_count} changelog entries")
            
            risk_drivers_count = create_risk_register_file(TENANT_ID, policy_uuid, policy_data)
            print(f"  ✓ Created risk register with {risk_drivers_count} drivers")
            
            print(f"  ✅ Completed: {policy_name}")
            
        except Exception as e:
            print(f"  ✗ Error processing {policy_file}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🎉 Seeding complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

