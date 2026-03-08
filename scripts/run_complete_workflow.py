#!/usr/bin/env python3
"""
Complete Workflow Script:
1. Run daily job to generate source data and load to target database tables
2. Create baseline analyses for all policies
3. Generate observations for all remaining policies

This script automates the complete workflow without requiring user interaction.
"""
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

# Default tenant ID (demo tenant)
TENANT_ID = "00000000-0000-0000-0000-000000000001"

def get_headers():
    """Get headers for API requests"""
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer demo-token"  # Using demo auth
    }

def get_policies() -> List[Dict[str, Any]]:
    """Get all policies"""
    print("📋 Fetching all policies...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/policies",
            headers=get_headers(),
            timeout=60
        )
        response.raise_for_status()
        policies = response.json()
        print(f"✅ Found {len(policies)} policies")
        return policies
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []

def run_daily_job(target_date: str = None) -> Dict[str, Any]:
    """Run daily job to generate data and load to database"""
    print("\n🔄 Step 1: Running daily job (generate data + load to database)...")
    
    if not target_date:
        # Default to yesterday
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime("%Y-%m-%d")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/jobs/daily-data-and-observations",
            headers=get_headers(),
            params={
                "target_date": target_date,
                "run_observations": False  # We'll create observations separately
            },
            timeout=300  # 5 minutes timeout
        )
        response.raise_for_status()
        result = response.json()
        job_id = result.get("job_id")
        print(f"✅ Daily job started: {job_id}")
        
        # Wait for job to complete
        print("⏳ Waiting for daily job to complete...")
        max_wait = 600  # 10 minutes max
        wait_time = 0
        check_interval = 5
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            status_response = requests.get(
                f"{API_BASE_URL}/jobs/daily-data-and-observations/status/{job_id}",
                headers=get_headers(),
                timeout=30
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "").upper()
                message = status_data.get("message", "")
                
                print(f"   Status: {status} - {message}")
                
                if status in ["COMPLETED", "SUCCESS"]:
                    print(f"✅ Daily job completed successfully")
                    return {"success": True, "job_id": job_id, "message": message}
                elif status in ["FAILED", "ERROR"]:
                    error_msg = status_data.get("error", message)
                    print(f"❌ Daily job failed: {error_msg}")
                    return {"success": False, "job_id": job_id, "error": error_msg}
        
        print(f"⏰ Daily job timed out after {max_wait} seconds")
        return {"success": False, "job_id": job_id, "error": "Timeout"}
        
    except Exception as e:
        print(f"❌ Error running daily job: {e}")
        return {"success": False, "error": str(e)}

def create_baseline_for_policy(policy_id: str, policy_name: str) -> Dict[str, Any]:
    """Create baseline analysis for a policy"""
    print(f"   Creating baseline for policy: {policy_name} ({policy_id})...")
    
    try:
        # Create general baseline first
        response = requests.post(
            f"{API_BASE_URL}/analyses/baseline",
            headers=get_headers(),
            json={
                "name": f"General Baseline - {policy_name}",
                "baseline_type": "GENERAL",
                "n_clusters": 5
            },
            timeout=300
        )
        
        if response.status_code == 201:
            general_result = response.json()
            general_analysis_id = general_result.get("id")
            print(f"      ✅ General baseline created: {general_analysis_id}")
        else:
            print(f"      ⚠️  General baseline creation returned {response.status_code}")
            if response.status_code != 200:
                error_detail = response.text
                print(f"      Error: {error_detail}")
        
        # Create policy-specific baseline
        response = requests.post(
            f"{API_BASE_URL}/analyses/baseline",
            headers=get_headers(),
            json={
                "name": f"Policy-Specific Baseline - {policy_name}",
                "baseline_type": "POLICY_SPECIFIC",
                "policy_id": policy_id,
                "n_clusters": 5
            },
            timeout=300
        )
        
        if response.status_code == 201:
            policy_result = response.json()
            policy_analysis_id = policy_result.get("id")
            print(f"      ✅ Policy-specific baseline created: {policy_analysis_id}")
            return {"success": True, "general_id": general_analysis_id if 'general_analysis_id' in locals() else None, "policy_id": policy_analysis_id}
        else:
            print(f"      ⚠️  Policy-specific baseline creation returned {response.status_code}")
            if response.status_code != 200:
                error_detail = response.text
                print(f"      Error: {error_detail}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"      ❌ Error creating baseline: {e}")
        return {"success": False, "error": str(e)}

def create_baselines_for_all_policies() -> Dict[str, Any]:
    """Create baseline analyses for all policies"""
    print("\n📊 Step 2: Creating baseline analyses for all policies...")
    
    policies = get_policies()
    if not policies:
        return {"success": False, "error": "No policies found"}
    
    results = {
        "total": len(policies),
        "success": 0,
        "failed": 0,
        "details": []
    }
    
    for policy in policies:
        policy_id = policy.get("id")
        policy_name = policy.get("name", "Unknown")
        
        result = create_baseline_for_policy(policy_id, policy_name)
        
        if result.get("success"):
            results["success"] += 1
        else:
            results["failed"] += 1
        
        results["details"].append({
            "policy_id": policy_id,
            "policy_name": policy_name,
            "result": result
        })
        
        # Small delay to avoid overwhelming the API
        time.sleep(1)
    
    print(f"\n✅ Baseline creation complete: {results['success']} succeeded, {results['failed']} failed out of {results['total']} policies")
    return results

def get_pending_analyses() -> List[Dict[str, Any]]:
    """Get all pending impact analyses"""
    print("\n🔍 Step 3: Finding pending analyses for observation creation...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=get_headers(),
            params={
                "analysis_type": "IMPACT",
                "limit": 1000
            },
            timeout=60
        )
        response.raise_for_status()
        analyses = response.json()
        
        # Filter for pending or completed analyses without observations
        pending = [a for a in analyses if a.get("status") == "PENDING"]
        completed = [a for a in analyses if a.get("status") == "COMPLETED"]
        
        print(f"   Found {len(pending)} pending analyses and {len(completed)} completed analyses")
        return pending + completed
        
    except Exception as e:
        print(f"❌ Error fetching analyses: {e}")
        return []

def create_observations_for_analyses() -> Dict[str, Any]:
    """Create observations for all analyses"""
    print("\n📈 Step 4: Creating observations for all policies...")
    
    # First, complete any pending analyses
    print("   Completing pending analyses...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyses/complete-all-pending",
            headers=get_headers(),
            timeout=300
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Completed {result.get('completed', 0)} pending analyses")
    except Exception as e:
        print(f"   ⚠️  Error completing pending analyses: {e}")
    
    # Get all policies
    policies = get_policies()
    if not policies:
        return {"success": False, "error": "No policies found"}
    
    # Get all analyses
    analyses = get_pending_analyses()
    
    # Group analyses by policy
    policy_analyses = {}
    for analysis in analyses:
        policy_id = analysis.get("policy_id")
        if policy_id:
            if policy_id not in policy_analyses:
                policy_analyses[policy_id] = []
            policy_analyses[policy_id].append(analysis)
    
    results = {
        "total_policies": len(policies),
        "policies_with_analyses": len(policy_analyses),
        "observations_created": 0,
        "observations_failed": 0,
        "details": []
    }
    
    # Create observations for each policy that has analyses
    for policy in policies:
        policy_id = policy.get("id")
        policy_name = policy.get("name", "Unknown")
        
        if policy_id not in policy_analyses:
            print(f"   ⏭️  Skipping {policy_name} - no analyses found")
            continue
        
        policy_analyses_list = policy_analyses[policy_id]
        print(f"   Creating observations for {policy_name} ({len(policy_analyses_list)} analyses)...")
        
        for analysis in policy_analyses_list:
            analysis_id = analysis.get("id")
            analysis_status = analysis.get("status")
            
            if analysis_status != "COMPLETED":
                print(f"      ⏭️  Skipping analysis {analysis_id} - status: {analysis_status}")
                continue
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
                    headers=get_headers(),
                    params={"policy_id": policy_id},
                    timeout=120
                )
                
                if response.status_code == 201:
                    observation = response.json()
                    obs_id = observation.get("observation_id")
                    print(f"      ✅ Created observation: {obs_id}")
                    results["observations_created"] += 1
                else:
                    error_detail = response.text
                    print(f"      ❌ Failed to create observation: HTTP {response.status_code} - {error_detail}")
                    results["observations_failed"] += 1
                    
            except Exception as e:
                print(f"      ❌ Error creating observation: {e}")
                results["observations_failed"] += 1
            
            # Small delay
            time.sleep(0.5)
        
        results["details"].append({
            "policy_id": policy_id,
            "policy_name": policy_name,
            "analyses_count": len(policy_analyses_list),
        })
    
    print(f"\n✅ Observation creation complete: {results['observations_created']} created, {results['observations_failed']} failed")
    return results

def main():
    """Run the complete workflow"""
    print("=" * 80)
    print("🚀 COMPLETE WORKFLOW AUTOMATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Step 1: Run daily job
    daily_job_result = run_daily_job()
    if not daily_job_result.get("success"):
        print("⚠️  Daily job had issues, but continuing...")
    
    # Step 2: Create baselines for all policies
    baseline_result = create_baselines_for_all_policies()
    
    # Step 3: Create observations for all policies
    observation_result = create_observations_for_analyses()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Daily Job: {'✅ Success' if daily_job_result.get('success') else '❌ Failed'}")
    print(f"Baselines Created: {baseline_result.get('success', 0)}/{baseline_result.get('total', 0)}")
    print(f"Observations Created: {observation_result.get('observations_created', 0)}")
    print(f"Observations Failed: {observation_result.get('observations_failed', 0)}")
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Workflow failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
