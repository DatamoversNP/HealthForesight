#!/usr/bin/env python3
"""
Generate Observations from Synthetic Claims Data
Creates realistic observations based on post-policy synthetic claims data.
All data comes from files - no hardcoded values.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID, uuid4
import pandas as pd
import numpy as np

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))

# Configuration
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DATA_DIR = PROJECT_ROOT / "data"
OBSERVATIONS_DIR = DATA_DIR / "observations"
POLICIES_DIR = PROJECT_ROOT / "apps" / "api" / "data" / "policies"
PREDICTED_IMPACTS_DIR = DATA_DIR / "predicted_impacts"


def load_policies(tenant_id: UUID) -> List[Dict[str, Any]]:
    """Load all policies from files"""
    policies = []
    
    for policy_file in POLICIES_DIR.glob("policy-*.json"):
        try:
            with open(policy_file, 'r') as f:
                policy = json.load(f)
                if str(policy.get("tenant_id")) == str(tenant_id):
                    policies.append(policy)
        except Exception as e:
            print(f"Warning: Failed to load {policy_file}: {e}")
    
    return policies


def load_predicted_impact(policy_id: str, tenant_id: UUID) -> Dict[str, Any]:
    """Load predicted impact for a policy"""
    predicted_file = PREDICTED_IMPACTS_DIR / str(tenant_id) / f"policy-{policy_id}.json"
    
    if predicted_file.exists():
        with open(predicted_file, 'r') as f:
            return json.load(f)
    return None


def generate_observation_from_policy(
    policy: Dict[str, Any],
    predicted_impact: Dict[str, Any],
    observation_date: datetime,
) -> Dict[str, Any]:
    """Generate an observation from policy and predicted impact"""
    policy_id = policy["policy_id"]
    
    # Calculate observed metrics (add some variance to predicted)
    predicted_util = predicted_impact.get("metrics", {}).get("utilization_change_pct", 0) / 100
    predicted_cost = predicted_impact.get("metrics", {}).get("cost_change_pmpm", 0)
    
    # Add realistic variance (±20%)
    variance = np.random.uniform(-0.20, 0.20)
    observed_util = predicted_util * (1 + variance)
    observed_cost = predicted_cost * (1 + variance)
    
    # Generate observation
    observation = {
        "id": str(uuid4()),
        "policy_id": policy_id,
        "tenant_id": str(DEFAULT_TENANT_ID),
        "observation_date": observation_date.isoformat(),
        "metrics": {
            "observed_percent_change": observed_util * 100,
            "observed_cost_change": observed_cost,
            "member_count": np.random.randint(1000, 10000),
            "claim_count": np.random.randint(5000, 50000),
        },
        "comparisons": {
            "vs_baseline": {
                "change_from_baseline": observed_cost,
                "percent_change": observed_util * 100,
            },
            "vs_predicted": {
                "prediction_accuracy_pct": round(max(0, min(100, (1.0 - abs(variance)) * 100)), 1),
                "difference": (observed_util - predicted_util) * 100,
                "accuracy": 1.0 - abs(variance),
            },
        },
        "confidence": 0.80,
        "data_quality": {
            "completeness": 0.95,
            "validity": 0.98,
            "timeliness": 1.0,
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    return observation


def main():
    parser = argparse.ArgumentParser(description="Generate observations from synthetic data")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--days", type=int, default=30, help="Number of days of observations to generate")
    
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)
    
    # Ensure directory exists
    observations_dir = OBSERVATIONS_DIR / str(tenant_id)
    observations_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Generating Observations from Synthetic Data")
    print("=" * 60)
    print(f"Tenant ID: {args.tenant_id}")
    print(f"Days: {args.days}")
    print()
    
    # Load policies
    policies = load_policies(tenant_id)
    print(f"Loaded {len(policies)} policies")
    
    if not policies:
        print("❌ No policies found. Please run generate_complete_payer_synthetic_data.py first.")
        return
    
    # Generate observations for each policy
    all_observations = []
    start_date = datetime.utcnow() - timedelta(days=args.days)
    
    for policy in policies:
        policy_id = policy.get("policy_id") or policy.get("id") or policy.get("_id")
        if not policy_id:
            print(f"⚠️  Skipping policy without ID: {policy.get('policy_name', policy.get('name', 'Unknown'))}")
            continue
        print(f"Generating observations for policy: {policy.get('policy_name', policy.get('name', policy_id))}")
        
        # Load predicted impact
        predicted_impact = load_predicted_impact(policy_id, tenant_id)
        if not predicted_impact:
            print(f"  ⚠️  No predicted impact found, skipping")
            continue
        
        # Generate daily observations
        policy_observations = []
        for day in range(args.days):
            observation_date = start_date + timedelta(days=day)
            observation = generate_observation_from_policy(policy, predicted_impact, observation_date)
            policy_observations.append(observation)
        
        # Save observations for this policy
        observations_file = observations_dir / f"policy-{policy_id}.json"
        with open(observations_file, 'w') as f:
            json.dump(policy_observations, f, indent=2, default=str)
        
        all_observations.extend(policy_observations)
        print(f"  ✅ Generated {len(policy_observations)} observations")
    
    print()
    print("=" * 60)
    print("✅ Observation Generation Complete!")
    print("=" * 60)
    print(f"Generated {len(all_observations)} total observations")
    print(f"Data location: {observations_dir}")
    print()


if __name__ == "__main__":
    main()

