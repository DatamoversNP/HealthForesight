#!/usr/bin/env python3
"""
Import policies from JSON files via API
This script reads the valid_policies.json file and imports each policy via API
"""
import json
import requests
import sys
from pathlib import Path
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
TOKEN = "dev-token-123"  # Mock token for dev

project_root = Path(__file__).parent.parent.parent
policies_file = project_root / "data" / "valid_policies.json"


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(
            f"{API_URL}/me",
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=5,
        )
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False


def import_policy(policy_data):
    """Import a single policy via API"""
    # Convert CanonicalPolicy to API PolicyCreate format
    api_payload = {
        "name": policy_data["policy_name"],
        "policy_type": policy_data["policy_type"],
        "description": policy_data.get("description"),
        "owner_role": "UM_LEADER",
        "status": policy_data.get("status", "ACTIVE"),
        "scope": policy_data.get("scope"),
        "effective_period": policy_data.get("effective_period"),
        "enforcement": policy_data.get("enforcement"),
        "policy_logic": policy_data.get("policy_logic"),  # Full PolicyLogic JSON
    }
    
    try:
        response = requests.post(
            f"{API_URL}/policies",
            json=api_payload,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return {
                "status": "success",
                "policy": policy_data["policy_name"],
                "id": result.get("id"),
                "api_id": result.get("id"),
            }
        else:
            error_msg = response.text
            try:
                error_json = response.json()
                error_msg = error_json.get('detail', error_msg)
            except:
                pass
            return {
                "status": "error",
                "policy": policy_data["policy_name"],
                "error": f"{response.status_code}: {error_msg}",
                "code": response.status_code,
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "policy": policy_data["policy_name"],
            "error": "Connection refused - API server not running",
        }
    except Exception as e:
        return {
            "status": "error",
            "policy": policy_data["policy_name"],
            "error": str(e),
        }


def main():
    """Import all policies from JSON file via API"""
    print("🚀 Importing policies via API...")
    print(f"   API URL: {API_URL}")
    print(f"   Policies file: {policies_file}")
    print("")
    
    # Check if API is running
    print("🔍 Checking API health...")
    if not check_api_health():
        print("❌ API server is not running!")
        print("")
        print("💡 To start the API server, run:")
        print("   cd apps/api")
        print("   uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000")
        print("")
        print("   Or use docker-compose:")
        print("   docker-compose up api")
        return 1
    
    print("✅ API server is running")
    print("")
    
    # Load policies from JSON file
    if not policies_file.exists():
        print(f"❌ Policies file not found: {policies_file}")
        print("   Run: python3 scripts/dev/create_policies_json.py first")
        return 1
    
    with open(policies_file) as f:
        data = json.load(f)
    
    policies = data.get("policies", [])
    if not policies:
        print(f"❌ No policies found in {policies_file}")
        return 1
    
    print(f"📦 Found {len(policies)} policies to import")
    print("")
    
    # Import each policy
    results = []
    for i, policy_data in enumerate(policies, 1):
        print(f"[{i}/{len(policies)}] Importing: {policy_data['policy_name']}")
        result = import_policy(policy_data)
        results.append(result)
        
        if result["status"] == "success":
            print(f"   ✅ Success - API ID: {result.get('api_id', 'N/A')}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        print("")
    
    # Summary
    print("=" * 70)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    print(f"📊 Summary: {successful}/{len(results)} policies imported successfully")
    
    if successful > 0:
        print(f"\n✅ Successfully imported policies:")
        for r in results:
            if r["status"] == "success":
                print(f"   - {r['policy']} (API ID: {r.get('api_id', 'N/A')})")
    
    if failed > 0:
        print(f"\n❌ Failed policies:")
        for r in results:
            if r["status"] == "error":
                print(f"   - {r['policy']}: {r.get('error', 'Unknown error')}")
    
    # Save import results
    results_file = project_root / "data" / "policy_import_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "imported_at": datetime.utcnow().isoformat(),
            "api_url": API_URL,
            "results": results,
        }, f, indent=2)
    print(f"\n💾 Import results saved to: {results_file}")
    
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

