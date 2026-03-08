#!/usr/bin/env python3
"""Run observation analysis only (assuming data is already loaded)"""
import sys
import requests
import time
from pathlib import Path
from uuid import UUID
from datetime import datetime

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

from uepi_api.storage_policies import list_policies
from uepi_api.storage_auth import DEFAULT_TENANT_ID

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}
POLICY_EFFECTIVE_DATE = datetime(2026, 1, 1)
tenant_id = DEFAULT_TENANT_ID


def check_api_server():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def run_impact_analysis(policy_id: UUID, policy_effective_date: datetime, tenant_id: UUID):
    """Run impact analysis for a policy"""
    treatment_filters = {
        "lob": ["COMMERCIAL", "MA", "MEDICAID"],
        "markets": ["BOS", "DFW", "NYC"],
        "in_network_only": True,
    }
    
    payload = {
        "policy_id": str(policy_id),
        "treatment_filters": treatment_filters,
        "control_filters": None,
        "matching_strategy": None,
        "pre_window_months": 6,
        "post_window_months": 1,
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyses/impact",
            headers=HEADERS,
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    ❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"       Error detail: {error_detail}")
            except:
                print(f"       Status code: {e.response.status_code}")
        return None


def create_observation(policy_id: UUID, analysis_id: UUID):
    """Create observation from impact analysis result"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": str(policy_id)},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    ❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"       Error detail: {error_detail}")
            except:
                print(f"       Status code: {e.response.status_code}")
        return None


def main():
    print("="*60)
    print("Running Impact Analysis for All Policies")
    print("="*60)
    
    # Check API server
    if not check_api_server():
        print("\n⚠️  API server is not running!")
        print("\nPlease start the API server first:")
        print("  ./start-api-server.sh")
        print("\nOr manually:")
        print("  cd '$(pwd)'")
        print("  source .venv/bin/activate")
        print("  export PYTHONPATH=\"$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH\"")
        print("  python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload")
        return 1
    
    print("✅ API server is running\n")
    
    # Get all policies
    policies = list_policies(tenant_id)
    print(f"Found {len(policies)} policies\n")
    
    results = {
        "total_policies": len(policies),
        "analyses_created": 0,
        "observations_created": 0,
        "errors": 0,
    }
    
    for policy in policies:
        policy_id = UUID(policy.get("id") or policy.get("policy_id"))
        policy_name = policy.get("name") or policy.get("policy_name", "Unknown")
        
        print(f"📋 Policy: {policy_name} ({policy_id})")
        
        # Run impact analysis
        analysis_result = run_impact_analysis(policy_id, POLICY_EFFECTIVE_DATE, tenant_id)
        
        if analysis_result:
            analysis_id = analysis_result.get("id")
            status = analysis_result.get("status")
            
            print(f"  ✅ Impact analysis created: {analysis_id}, Status: {status}")
            results["analyses_created"] += 1
            
            # Wait a bit for analysis to complete
            time.sleep(3)
            
            # Create observation from analysis
            obs_result = create_observation(policy_id, analysis_id)
            
            if obs_result:
                observation_id = obs_result.get("observation_id")
                print(f"  ✅ Observation created: {observation_id}")
                results["observations_created"] += 1
            else:
                print(f"  ⚠️  Failed to create observation")
                results["errors"] += 1
        else:
            results["errors"] += 1
        
        print()
    
    print("="*60)
    print("OBSERVATION ANALYSIS COMPLETE")
    print("="*60)
    print(f"Total policies: {results['total_policies']}")
    print(f"Analyses created: {results['analyses_created']}")
    print(f"Observations created: {results['observations_created']}")
    print(f"Errors: {results['errors']}")
    print("="*60)
    print("\nNext steps:")
    print("  1. View observations in UI: http://localhost:3050/policies")
    print("  2. Compare observed vs predicted impact")
    
    return 0 if results["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
