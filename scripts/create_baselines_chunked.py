#!/usr/bin/env python3
"""
Chunked baseline creation - Create baselines in small batches
"""
import requests
import time
import json
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"
PROGRESS_FILE = Path("baseline_creation_progress.json")

def load_progress():
    """Load progress from file"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2, default=str)

def make_request(method, endpoint, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    timeout = kwargs.pop('timeout', 300)  # 5 minutes for baseline
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "timeout", "status_code": 408}
    except requests.exceptions.ConnectionError:
        return {"error": "connection_error", "status_code": 503}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return {"error": e.response.text, "status_code": 400}
        return {"error": str(e), "status_code": e.response.status_code}
    except Exception as e:
        return {"error": str(e), "status_code": 500}

def main():
    print("="*80)
    print("📊 CHUNKED BASELINE CREATION")
    print("="*80)
    
    # Load progress
    progress = load_progress()
    completed_policies = set(progress.get("completed_policies", []))
    general_done = progress.get("general_done", False)
    
    print(f"Progress: General={'✅' if general_done else '❌'}, Policy baselines: {len(completed_policies)} completed\n")
    
    # Check API
    health = make_request("GET", "/health", timeout=5)
    if not health or health.get("status") != "healthy":
        print("❌ API server not responding")
        return
    
    print("✅ API server connected\n")
    
    # Create general baseline first
    if not general_done:
        print("Creating general baseline...")
        result = make_request("POST", "/baselines/refresh",
                             json={"baseline_type": "ROLLING", "window_months": 12, "refresh_reason": "MANUAL"},
                             timeout=600)
        
        if result and result.get("baseline_id"):
            print(f"✅ General baseline created: {result.get('baseline_id')[:8]}...")
            general_done = True
            progress["general_done"] = True
            save_progress(progress)
        else:
            print(f"⚠️  General baseline failed: {result.get('error', 'Unknown error')[:100]}")
    
    # Get policies
    policies = make_request("GET", "/policies", timeout=10)
    if not policies:
        print("❌ No policies found")
        return
    
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
    print(f"\nFound {len(active_policies)} active policies")
    print(f"Creating policy-specific baselines in batches of 5...\n")
    
    # Process in batches
    batch_size = 5
    success_count = 0
    
    for i in range(0, len(active_policies), batch_size):
        batch = active_policies[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(active_policies) + batch_size - 1) // batch_size
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} policies)")
        
        for policy in batch:
            policy_id = policy.get("id")
            policy_name = policy.get("name", "Unknown")[:40]
            
            if not policy_id:
                continue
            
            policy_key = str(policy_id)
            if policy_key in completed_policies:
                print(f"   ⏭️  {policy_name}: Already completed")
                continue
            
            try:
                result = make_request("POST", "/baselines/refresh",
                                     json={"policy_id": policy_id, "baseline_type": "ROLLING", 
                                          "window_months": 12, "refresh_reason": "MANUAL"},
                                     timeout=600)
                
                if result and result.get("baseline_id"):
                    success_count += 1
                    completed_policies.add(policy_key)
                    print(f"   ✅ {policy_name}: Baseline created")
                elif result and result.get("status_code") == 400:
                    print(f"   ℹ️  {policy_name}: No matching data")
                    completed_policies.add(policy_key)  # Mark as done even if no data
                elif result and result.get("status_code") == 408:
                    print(f"   ⏱️  {policy_name}: Timeout (will retry next run)")
                else:
                    print(f"   ⚠️  {policy_name}: {result.get('error', 'Unknown error')[:50]}")
                    completed_policies.add(policy_key)  # Mark as done to avoid retry loop
                
                progress["completed_policies"] = list(completed_policies)
                save_progress(progress)
                
            except KeyboardInterrupt:
                print(f"\n⚠️  Interrupted! Progress saved. Run again to resume.")
                save_progress(progress)
                return
            except Exception as e:
                print(f"   ❌ {policy_name}: Error - {e}")
                completed_policies.add(policy_key)  # Mark as done to avoid retry loop
                progress["completed_policies"] = list(completed_policies)
                save_progress(progress)
            
            time.sleep(1)  # Delay between policies
        
        print(f"   Progress: {len(completed_policies)}/{len(active_policies)} policies processed")
        time.sleep(2)  # Longer pause between batches
    
    print(f"\n✅ Baseline creation complete: {success_count} policy baselines created")
    print("="*80)

if __name__ == "__main__":
    main()
