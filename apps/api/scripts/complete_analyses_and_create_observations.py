#!/usr/bin/env python3
"""Complete pending analyses with mock data and create observations - for testing"""
import requests
import json
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def get_pending_analyses():
    """Get all pending analyses"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=HEADERS,
            params={"analysis_type": "IMPACT"},
            timeout=30
        )
        response.raise_for_status()
        analyses = response.json()
        return [a for a in analyses if a.get("status") == "PENDING"]
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def get_policy_info(policy_id):
    """Get policy info"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/policies/{policy_id}",
            headers=HEADERS,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def create_mock_analysis_result(policy_id, analysis_id):
    """Create a mock analysis result for testing"""
    # This creates a basic result structure that the observation creation can use
    mock_result = {
        "impact_summary": {
            "observed_effect_size": -0.15,
            "observed_percent_change": -15.0,
            "confidence_interval_lower": -0.20,
            "confidence_interval_upper": -0.10,
            "p_value": 0.01,
        },
        "pre_period": {
            "start": "2024-06-01",
            "end": "2024-11-30",
            "utilization_per_1k": 125.5,
            "cost_per_member": 45.2,
        },
        "post_period": {
            "start": "2024-12-01",
            "end": "2024-12-31",
            "utilization_per_1k": 106.7,
            "cost_per_member": 38.4,
        },
        "method_checks": {
            "pre_trends_parallel": True,
            "control_balance": True,
            "seasonality_risk": "LOW",
        },
        "trust_panel": {
            "confidence_score": 0.85,
            "data_sufficiency": "SUFFICIENT",
        }
    }
    return mock_result

def complete_analysis_via_api(analysis_id, policy_id):
    """Complete an analysis by creating a result via direct database update"""
    # We'll use a Python script that connects to the database directly
    # But first, let's try to see if we can create the result via API
    
    # Actually, we need to update the database directly
    # Let me create a simpler approach - use the API to create observations
    # by first checking if we can manually set analysis results
    
    # For now, let's just try to create observations with a workaround
    # by creating a minimal valid result structure
    
    print(f"   ⚠️  Analysis {analysis_id} needs to be completed by worker")
    print(f"   💡 Creating observation with mock data for testing...")
    
    # Try to create observation anyway - it might work if the endpoint is flexible
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=120
        )
        
        if response.status_code == 201:
            obs = response.json()
            print(f"   ✅ Created observation: {obs.get('observation_id', 'unknown')[:8]}...")
            return True
        else:
            error = response.text[:300]
            print(f"   ❌ Failed: {response.status_code}")
            print(f"      {error}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return False

def main():
    print("\n" + "="*60)
    print("Complete Analyses & Create Observations")
    print("="*60)
    print("\n⚠️  Note: Analyses are stuck in PENDING because worker is not running.")
    print("   This script will attempt to create observations anyway.")
    print("   For production, start the worker service.\n")
    
    # Get pending analyses
    pending = get_pending_analyses()
    
    if not pending:
        print("✅ No pending analyses")
        return
    
    print(f"📊 Found {len(pending)} pending analyses\n")
    
    # Group by policy
    policies_analyses = {}
    for analysis in pending:
        policy_id = analysis.get("policy_id")
        if policy_id not in policies_analyses:
            policies_analyses[policy_id] = []
        policies_analyses[policy_id].append(analysis)
    
    print(f"📋 Processing {len(policies_analyses)} policies...\n")
    
    created = 0
    failed = 0
    
    for i, (policy_id, analyses) in enumerate(policies_analyses.items(), 1):
        # Get policy name
        policy_info = get_policy_info(policy_id)
        policy_name = policy_info.get("name", "Unknown") if policy_info else "Unknown"
        
        # Use most recent analysis
        latest_analysis = analyses[0]
        analysis_id = latest_analysis.get("id")
        
        print(f"[{i}/{len(policies_analyses)}] {policy_name[:50]}")
        print(f"   Analysis: {analysis_id[:8]}...")
        
        # Check if observation exists
        try:
            obs_response = requests.get(
                f"{API_BASE_URL}/observations",
                headers=HEADERS,
                params={"policy_id": policy_id},
                timeout=30
            )
            if obs_response.status_code == 200:
                observations = obs_response.json()
                existing = any(obs.get("analysis_id") == analysis_id for obs in observations)
                if existing:
                    print(f"   ✅ Observation already exists")
                    continue
        except:
            pass
        
        # Try to create observation (will fail if analysis not completed, but let's try)
        if complete_analysis_via_api(analysis_id, policy_id):
            created += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"✅ Created: {created}")
    print(f"❌ Failed: {failed}")
    print("="*60)
    
    if failed > 0:
        print(f"\n⚠️  {failed} observations could not be created.")
        print("   Analyses need to be completed by the worker service first.")
        print("   Start the worker, or wait for analyses to complete.")

if __name__ == "__main__":
    main()
