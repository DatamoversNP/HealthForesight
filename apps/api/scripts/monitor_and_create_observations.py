#!/usr/bin/env python3
"""Monitor analyses and automatically create observations when they complete"""
import sys
import os
import time
from pathlib import Path
from uuid import UUID
import requests
from typing import List, Dict, Any, Set

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
HEADERS = {
    "Authorization": "Bearer dev-token-123",
    "Content-Type": "application/json",
}

# Track which observations we've already created
created_observations: Set[str] = set()


def get_all_analyses() -> List[Dict[str, Any]]:
    """Get all impact analyses"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=HEADERS,
            params={"analysis_type": "IMPACT"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching analyses: {e}")
        return []


def check_existing_observation(policy_id: str, analysis_id: str) -> bool:
    """Check if observation already exists"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/observations",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=30,
        )
        if response.status_code == 200:
            observations = response.json()
            for obs in observations:
                if obs.get("analysis_id") == analysis_id:
                    return True
        return False
    except Exception:
        return False


def create_observation_from_analysis(analysis_id: str, policy_id: str) -> bool:
    """Create observation from impact analysis"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=120,
        )
        
        if response.status_code == 201:
            observation = response.json()
            obs_id = observation.get("observation_id", "unknown")
            print(f"   ✅ Created observation: {obs_id[:8]}...")
            return True
        else:
            error_detail = response.text[:500]
            print(f"   ⚠️  Failed ({response.status_code}): {error_detail[:100]}")
            return False
    except Exception as e:
        print(f"   ⚠️  Error: {str(e)[:200]}")
        return False


def process_completed_analyses(analyses: List[Dict[str, Any]]) -> int:
    """Process completed analyses and create observations"""
    created_count = 0
    
    for analysis in analyses:
        analysis_id = analysis.get("id")
        policy_id = analysis.get("policy_id")
        status = analysis.get("status")
        
        if status != "COMPLETED":
            continue
        
        # Skip if we already processed this
        key = f"{policy_id}:{analysis_id}"
        if key in created_observations:
            continue
        
        # Check if observation already exists
        if check_existing_observation(policy_id, analysis_id):
            print(f"   ⏭️  Observation already exists for analysis {analysis_id[:8]}...")
            created_observations.add(key)
            continue
        
        # Create observation
        print(f"   🚀 Creating observation for analysis {analysis_id[:8]}... (Policy: {policy_id[:8]}...)")
        if create_observation_from_analysis(analysis_id, policy_id):
            created_observations.add(key)
            created_count += 1
    
    return created_count


def main():
    print("\n" + "="*60)
    print("Monitoring Analyses and Creating Observations")
    print("="*60)
    print("This script will:")
    print("  1. Check for completed analyses every 30 seconds")
    print("  2. Automatically create observations when analyses complete")
    print("  3. Skip observations that already exist")
    print("\nPress Ctrl+C to stop\n")
    
    iteration = 0
    total_created = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n[{iteration}] Checking analyses... ({time.strftime('%H:%M:%S')})")
            
            # Get all analyses
            analyses = get_all_analyses()
            
            if not analyses:
                print("   ⚠️  No analyses found")
            else:
                # Count by status
                status_counts = {}
                for a in analyses:
                    status = a.get("status", "UNKNOWN")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"   📊 Total: {len(analyses)} analyses")
                for status, count in status_counts.items():
                    print(f"      {status}: {count}")
                
                # Process completed analyses
                completed = [a for a in analyses if a.get("status") == "COMPLETED"]
                if completed:
                    print(f"   ✅ Found {len(completed)} completed analyses")
                    created = process_completed_analyses(completed)
                    total_created += created
                    if created > 0:
                        print(f"   🎉 Created {created} new observation(s)!")
                else:
                    print(f"   ⏳ No completed analyses yet...")
            
            print(f"   💤 Waiting 30 seconds... (Total created so far: {total_created})")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("Monitoring Stopped")
        print("="*60)
        print(f"✅ Total observations created: {total_created}")
        print("="*60)


if __name__ == "__main__":
    main()
