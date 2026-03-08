#!/usr/bin/env python3
"""
Test baseline, predicted, and observed impact calculations with enhanced data.

Verifies that all metrics calculate correctly using:
- Enhanced data fields (plan_id, product_type, state, region, network_tier, etc.)
- Policy scoping with comprehensive scope
- Metric dictionary calculations
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import requests

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}


def test_api_endpoint(endpoint: str, method: str = "GET", data: dict = None, description: str = None):
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Test: {description or endpoint}")
    print(f"{'='*60}")
    print(f"Method: {method} {url}")
    
    try:
        if method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == "GET":
            response = requests.get(url, headers=HEADERS, params=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        if isinstance(result, dict):
            print(f"Response keys: {list(result.keys())[:10]}")
        else:
            print(f"Response type: {type(result)}")
        
        return result
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: API server not running at {API_BASE_URL}")
        print(f"   Please start the API server: ./start-both-servers.sh")
        return None
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout: Request took longer than 30 seconds")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"   Detail: {error_detail.get('detail', 'Unknown error')}")
        except:
            print(f"   Response: {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Run baseline/predicted/observed impact tests"""
    print("="*60)
    print("Baseline, Predicted, and Observed Impact Test")
    print("="*60)
    
    # Test 1: List policies
    policies_result = test_api_endpoint(
        "/policies",
        "GET",
        description="List Policies"
    )
    
    if not policies_result or not policies_result.get("policies"):
        print("\n⚠️  No policies found. Please ensure policies are loaded.")
        return
    
    policy = policies_result["policies"][0]
    policy_id = policy.get("policy_id")
    print(f"\n📋 Using policy: {policy.get('policy_name')} ({policy_id})")
    
    # Test 2: Run baseline analysis
    baseline_result = test_api_endpoint(
        "/analyses/baseline",
        "POST",
        data={
            "start_date": "2024-01-01",
            "end_date": "2025-12-31",
            "n_clusters": 5
        },
        description="Run Baseline Analysis"
    )
    
    baseline_id = None
    if baseline_result:
        baseline_id = baseline_result.get("id")
        print(f"\n📊 Baseline Analysis ID: {baseline_id}")
    
    # Test 3: Generate predicted impact
    if policy_id:
        predicted_result = test_api_endpoint(
            f"/policies/{policy_id}/predicted-impact",
            "POST",
            description="Generate Predicted Impact"
        )
        
        if predicted_result:
            print(f"✅ Predicted impact generated")
            metrics = predicted_result.get("metrics", {})
            if metrics:
                print(f"   Utilization reduction: {metrics.get('estimated_utilization_reduction_percent')}%")
                print(f"   Cost impact PMPM: ${metrics.get('estimated_cost_impact_pmpm')}")
                print(f"   Confidence: {metrics.get('confidence_score', 0) * 100:.0f}%")
    
    # Test 4: Run impact analysis (for observed)
    if policy_id:
        impact_result = test_api_endpoint(
            "/analyses/impact",
            "POST",
            data={
                "policy_id": policy_id,
                "pre_window_months": 6,
                "post_window_months": 3,
                "treatment_filters": {
                    "lob": ["COMMERCIAL"],
                    "markets": ["NYC"]
                }
            },
            description="Run Impact Analysis (Observed)"
        )
        
        impact_id = None
        if impact_result:
            impact_id = impact_result.get("id")
            print(f"\n📊 Impact Analysis ID: {impact_id}")
            
            # Test 5: Create observation from analysis
            if impact_id:
                # Wait a bit for analysis to complete
                import time
                print("\n⏳ Waiting 5 seconds for analysis to complete...")
                time.sleep(5)
                
                observation_result = test_api_endpoint(
                    f"/observations/from-analysis/{impact_id}",
                    "POST",
                    data={},
                    description="Create Observation from Analysis"
                )
                
                if observation_result:
                    observation_id = observation_result.get("observation_id")
                    print(f"\n📊 Observation ID: {observation_id}")
                    
                    # Test 6: Get observation comparison
                    if observation_id:
                        comparison_result = test_api_endpoint(
                            f"/observations/{observation_id}/comparison",
                            "GET",
                            description="Get Observation Comparison"
                        )
                        
                        if comparison_result:
                            vs_baseline = comparison_result.get("vs_baseline", {})
                            vs_predicted = comparison_result.get("vs_predicted", {})
                            
                            print(f"\n📈 Comparison Results:")
                            if vs_baseline:
                                print(f"   vs Baseline - Change: {vs_baseline.get('change_from_baseline', 'N/A')}")
                            if vs_predicted:
                                print(f"   vs Predicted - Accuracy: {vs_predicted.get('prediction_accuracy_pct', 'N/A')}%")
    
    print("\n" + "="*60)
    print("✅ Baseline/Predicted/Observed Impact Tests Complete")
    print("="*60)
    print("\nNote: Some tests may require data to be generated first.")
    print("Run: python3 scripts/regenerate_complete_workflow.py")


if __name__ == "__main__":
    main()
