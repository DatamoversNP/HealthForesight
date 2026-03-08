#!/usr/bin/env python3
"""Diagnose all modules to check if data is loading correctly"""

import sys
import requests
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": "Bearer dev-token-123",
    "Content-Type": "application/json"
}

def check_endpoint(name, endpoint, method="GET", data=None):
    """Check if an endpoint is working"""
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=HEADERS, timeout=10)
        elif method == "POST":
            response = requests.post(f"{API_BASE_URL}{endpoint}", headers=HEADERS, json=data, timeout=10)
        else:
            return {"status": "error", "message": f"Unknown method: {method}"}
        
        if response.status_code == 200:
            result = response.json()
            count = len(result) if isinstance(result, list) else 1
            return {"status": "ok", "count": count, "status_code": response.status_code}
        else:
            return {"status": "error", "status_code": response.status_code, "message": response.text[:200]}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "API not running"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}

def main():
    print("="*80)
    print("DIAGNOSTIC: ALL MODULES DATA LOADING")
    print("="*80)
    print()
    
    # Check API is running
    print("Step 1: Checking API connection...")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"⚠️  API health check returned: {response.status_code}")
    except:
        print("❌ API is not running or not accessible")
        print("   Start API: cd apps/api/src && python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload")
        return 1
    
    print("\nStep 2: Checking all modules...")
    print()
    
    modules = [
        ("Policies", "/policies"),
        ("Observations", "/observations"),
        ("Analyses", "/analyses"),
        ("Pipelines", "/pipelines"),
        ("Baselines", "/baselines"),
        ("Ingestions", "/ingestions"),
        ("Datasets", "/datasets"),
        ("Cohorts", "/cohorts"),
        ("Scorecards", "/scorecards"),
        ("Data Periods", "/periods"),
        ("Policy Versions", "/policies/00000000-0000-0000-0000-000000000001/versions"),  # Sample policy
        ("Dashboard Summary", "/dashboard/summary"),
        ("Policy Performance", "/dashboard/policy-performance?limit=10"),
    ]
    
    results = {}
    for name, endpoint in modules:
        print(f"  Checking {name}...", end=" ")
        result = check_endpoint(name, endpoint)
        results[name] = result
        
        if result["status"] == "ok":
            count = result.get("count", "N/A")
            print(f"✅ OK ({count} items)")
        else:
            status_code = result.get("status_code", "N/A")
            message = result.get("message", "Unknown error")
            print(f"❌ FAILED (Status: {status_code}, Error: {message[:50]})")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    working = [name for name, r in results.items() if r["status"] == "ok"]
    failed = [name for name, r in results.items() if r["status"] != "ok"]
    
    print(f"\n✅ Working modules ({len(working)}):")
    for name in working:
        count = results[name].get("count", "N/A")
        print(f"   - {name}: {count} items")
    
    print(f"\n❌ Failed modules ({len(failed)}):")
    for name in failed:
        result = results[name]
        status_code = result.get("status_code", "N/A")
        message = result.get("message", "Unknown error")
        print(f"   - {name}: Status {status_code} - {message[:60]}")
    
    # Root cause analysis
    print("\n" + "="*80)
    print("ROOT CAUSE ANALYSIS")
    print("="*80)
    
    if len(failed) > len(working):
        print("\n⚠️  Most modules are failing. Likely causes:")
        print("   1. Database connection is failing (password authentication error)")
        print("   2. All routers are using database storage (no file fallback)")
        print("   3. Data was migrated to database but database is not accessible")
        print("\n💡 Solution:")
        print("   - Fix database connection (password: uepi123 per docker-compose)")
        print("   - OR enable file-based storage fallback for routers")
        print("   - OR restore data from backup files")
    
    return 0 if len(working) > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
