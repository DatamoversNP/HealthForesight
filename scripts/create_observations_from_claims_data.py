#!/usr/bin/env python3
"""Script to create observations from actual claims data by running impact analyses"""

import sys
import requests
import json
from pathlib import Path
from uuid import UUID
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": "Bearer dev-token-123",
    "Content-Type": "application/json"
}

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
POLICY_EFFECTIVE_DATE = datetime(2024, 12, 1)


def check_api():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        # Connection error - API might not be running or network blocked
        # Try to proceed anyway - will fail with better error message if API is down
        print("⚠️  Could not verify API health endpoint, but proceeding anyway...")
        return True  # Proceed and let actual API calls fail with better errors
    except:
        return False


def get_policies():
    """Get list of policies"""
    try:
        # Try with auth header
        response = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            # Try without auth (might use demo user)
            print("  ⚠️  Auth failed, trying without auth header...")
            response = requests.get(f"{API_BASE_URL}/policies", timeout=10)
            if response.status_code == 200:
                return response.json()
        response.raise_for_status()
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print(f"   Make sure API is running on http://localhost:8000")
        print(f"   Check with: curl http://localhost:8000/health")
        return []
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        print(f"   Response status: {getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'}")
        return []


def run_impact_analysis(policy_id: str, policy_name: str):
    """Run impact analysis for a policy"""
    print(f"\n  Running impact analysis for: {policy_name} ({policy_id[:8]}...)")
    
    # Build treatment filters (default - should come from policy scope)
    treatment_filters = {
        "lob": ["COMMERCIAL", "MA", "MEDICAID"],
        "markets": ["BOS", "DFW", "NYC"],
        "in_network_only": True,
    }
    
    # Calculate date windows
    pre_window_months = 6
    post_window_months = 1  # Start with 1 month post-policy
    
    payload = {
        "policy_id": policy_id,
        "treatment_filters": treatment_filters,
        "control_filters": None,
        "pre_window_months": pre_window_months,
        "post_window_months": post_window_months,
    }
    
    try:
        # The endpoint should process synchronously and return COMPLETED status
        # If it returns PENDING, it means worker is needed (but we'll wait for it)
        response = requests.post(
            f"{API_BASE_URL}/analyses/impact",
            headers=HEADERS,
            json=payload,
            timeout=300,  # 5 minutes timeout
        )
        response.raise_for_status()
        result = response.json()
        
        analysis_id = result.get("id")
        status = result.get("status")
        
        print(f"    ✅ Impact analysis created: {analysis_id}, Status: {status}")
        
        # If status is COMPLETED, we can use it immediately
        if status == "COMPLETED":
            print(f"    ✅ Analysis completed immediately!")
            return analysis_id, result
        
        # If status is PENDING or PROCESSING, wait and check
        if status in ["PENDING", "PROCESSING"]:
            print(f"    ⏳ Analysis is {status}, waiting for completion...")
            import time
            max_wait = 60  # Wait up to 60 seconds
            waited = 0
            while waited < max_wait:
                time.sleep(2)
                waited += 2
                # Check analysis status
                try:
                    check_response = requests.get(
                        f"{API_BASE_URL}/analyses/{analysis_id}",
                        headers=HEADERS,
                        timeout=10
                    )
                    if check_response.status_code == 200:
                        check_result = check_response.json()
                        new_status = check_result.get("status")
                        if new_status == "COMPLETED":
                            print(f"    ✅ Analysis completed after {waited}s")
                            return analysis_id, check_result
                        elif new_status == "FAILED":
                            print(f"    ❌ Analysis failed")
                            return None, None
                except:
                    pass
            
            print(f"    ⚠️  Analysis still {status} after {max_wait}s, proceeding anyway...")
        
        return analysis_id, result
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error running impact analysis: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"       Error detail: {error_detail}")
            except:
                print(f"       Status code: {e.response.status_code}")
        return None, None


def check_analysis_has_data(analysis_id: str):
    """Check if analysis has treatment_post data"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses/{analysis_id}",
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        analysis = response.json()
        
        # Check multiple possible locations for result data
        result_data = None
        
        # Try result_data_json (database storage)
        if analysis.get("result_data_json"):
            result_data = analysis.get("result_data_json")
        # Try result (file storage or direct response)
        elif analysis.get("result"):
            result_data = analysis.get("result")
        # Try result field directly
        elif "result" in analysis and isinstance(analysis["result"], dict):
            result_data = analysis["result"]
        
        if result_data:
            metrics = result_data.get("metrics", {})
            treatment_post = metrics.get("treatment_post", {})
            
            if treatment_post and treatment_post.get("utilization_per_1k", 0) > 0:
                return True, treatment_post
            else:
                # Debug: print what we found
                print(f"    Debug: metrics keys: {list(metrics.keys())}")
                if "treatment_post" in metrics:
                    print(f"    Debug: treatment_post keys: {list(metrics['treatment_post'].keys())}")
                return False, None
        
        # Debug: print analysis structure
        print(f"    Debug: Analysis keys: {list(analysis.keys())}")
        print(f"    Debug: Analysis status: {analysis.get('status')}")
        
        return False, None
    except Exception as e:
        print(f"    ⚠️  Error checking analysis: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def create_observation_from_analysis(policy_id: str, analysis_id: str):
    """Create observation from analysis"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=60
        )
        response.raise_for_status()
        observation = response.json()
        
        obs_id = observation.get("observation_id")
        metrics = observation.get("metrics", {})
        utilization = metrics.get("utilization_per_1k", 0)
        cost = metrics.get("cost_pmpm") or metrics.get("cost_per_member", 0)
        
        print(f"    ✅ Observation created: {obs_id[:8]}...")
        print(f"       Utilization: {utilization:.2f}, Cost PMPM: {cost:.2f}")
        
        return observation
    except Exception as e:
        print(f"    ❌ Error creating observation: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"       Error detail: {error_detail}")
            except:
                print(f"       Status code: {e.response.status_code}")
        return None


def main():
    print("="*80)
    print("CREATE OBSERVATIONS FROM CLAIMS DATA")
    print("="*80)
    
    # Check API
    print("\n1. Checking API...")
    if not check_api():
        print("❌ API is not running!")
        print("   Please start the API server first:")
        print("   cd apps/api/src")
        print("   export PYTHONPATH=\"$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH\"")
        print("   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload")
        return 1
    
    print("✅ API is running")
    
    # Get policies
    print("\n2. Fetching policies...")
    policies = get_policies()
    if not policies:
        print("❌ No policies found")
        return 1
    
    print(f"✅ Found {len(policies)} policies")
    
    # Process each policy
    print("\n3. Processing policies...")
    successful_observations = 0
    failed_observations = 0
    
    for policy in policies[:5]:  # Process first 5 policies
        policy_id = policy.get("id") or policy.get("policy_id")
        policy_name = policy.get("name") or policy.get("policy_name") or "Unknown"
        
        print(f"\n📋 Policy: {policy_name}")
        
        # Run impact analysis
        analysis_id, analysis_result = run_impact_analysis(policy_id, policy_name)
        if not analysis_id:
            print(f"   ⚠️  Skipping - analysis failed")
            failed_observations += 1
            continue
        
        # Check if analysis has data
        has_data, treatment_post = check_analysis_has_data(analysis_id)
        if not has_data:
            print(f"   ⚠️  Analysis doesn't have treatment_post data yet")
            print(f"   ⚠️  This might be because:")
            print(f"      - Analysis is still processing")
            print(f"      - Claims data doesn't exist for this policy")
            print(f"      - Analysis didn't load claims correctly")
            failed_observations += 1
            continue
        
        print(f"   ✅ Analysis has data:")
        print(f"      Utilization: {treatment_post.get('utilization_per_1k', 0):.2f}")
        print(f"      Cost PMPM: {treatment_post.get('allowed_pmpm', treatment_post.get('paid_pmpm', 0)):.2f}")
        
        # Create observation
        observation = create_observation_from_analysis(policy_id, analysis_id)
        if observation:
            successful_observations += 1
        else:
            failed_observations += 1
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Successful observations: {successful_observations}")
    print(f"❌ Failed observations: {failed_observations}")
    
    if successful_observations > 0:
        print("\n✅ Observations created! Check the UI to see observed values.")
    else:
        print("\n⚠️  No observations were created. Check:")
        print("   1. API is running and accessible")
        print("   2. Claims data exists in apps/data/target_data_model/")
        print("   3. Impact analyses are loading claims correctly")
        print("   4. Analysis results have treatment_post metrics")
    
    return 0 if successful_observations > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
