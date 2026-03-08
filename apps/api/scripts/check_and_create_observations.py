#!/usr/bin/env python3
"""Simple script to check analysis status and create observations - run this anytime"""
import requests
import sys

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123"}

def main():
    print("\n" + "="*60)
    print("Check Analysis Status & Create Observations")
    print("="*60)
    
    # Get all analyses
    print("\n📊 Checking analyses...")
    try:
        response = requests.get(f"{API_BASE_URL}/analyses", headers=HEADERS, params={"analysis_type": "IMPACT"}, timeout=30)
        response.raise_for_status()
        analyses = response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Count by status
    status_counts = {}
    for a in analyses:
        status = a.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n📈 Analysis Status:")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")
    
    # Find completed analyses
    completed = [a for a in analyses if a.get("status") == "COMPLETED"]
    
    if not completed:
        print(f"\n⏳ No completed analyses yet.")
        print(f"   The analyses are being processed by the worker.")
        print(f"   Run this script again later to check status.")
        return
    
    print(f"\n✅ Found {len(completed)} completed analyses!")
    print(f"\n🚀 Creating observations...\n")
    
    # Create observations
    created = 0
    skipped = 0
    failed = 0
    
    for analysis in completed:
        analysis_id = analysis.get("id")
        policy_id = analysis.get("policy_id")
        
        # Check if observation exists
        try:
            obs_response = requests.get(
                f"{API_BASE_URL}/observations",
                headers=HEADERS,
                params={"policy_id": policy_id},
                timeout=30
            )
            existing = False
            if obs_response.status_code == 200:
                observations = obs_response.json()
                for obs in observations:
                    if obs.get("analysis_id") == analysis_id:
                        existing = True
                        break
        except:
            existing = False
        
        if existing:
            print(f"   ⏭️  Analysis {analysis_id[:8]}... - observation already exists")
            skipped += 1
            continue
        
        # Create observation
        print(f"   🚀 Creating observation for analysis {analysis_id[:8]}...")
        try:
            response = requests.post(
                f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
                headers=HEADERS,
                params={"policy_id": policy_id},
                timeout=120
            )
            
            if response.status_code == 201:
                obs = response.json()
                obs_id = obs.get("observation_id", "unknown")
                print(f"   ✅ Created: {obs_id[:8]}...")
                created += 1
            else:
                error = response.text[:200]
                print(f"   ❌ Failed ({response.status_code}): {error}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"✅ Created: {created}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}")
    print("="*60)
    
    if created > 0:
        print(f"\n🎉 Successfully created {created} observation(s)!")
    elif completed:
        print(f"\n✅ All completed analyses already have observations.")

if __name__ == "__main__":
    main()
