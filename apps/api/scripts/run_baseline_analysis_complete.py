#!/usr/bin/env python3
"""
Run baseline analysis across all available source data and persist results
"""
import sys
import requests
import json
from pathlib import Path
from datetime import datetime

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_auth import DEFAULT_TENANT_ID

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dev-token-123"
}

def check_api_health():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_baseline_analysis():
    """Run baseline analysis with comprehensive date range"""
    print("=" * 80)
    print("Running Baseline Analysis")
    print("=" * 80)
    
    if not check_api_health():
        print("❌ API server is not running. Please start the API server first.")
        print("   Run: ./start_api.sh or python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000")
        return 1
    
    url = f"{API_BASE_URL}/analyses/baseline"
    payload = {
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "n_clusters": 5
    }
    
    print(f"📊 Requesting baseline analysis...")
    print(f"   Date range: {payload['start_date']} to {payload['end_date']}")
    print(f"   Provider clusters: {payload['n_clusters']}")
    print(f"   API endpoint: {url}")
    print()
    
    try:
        print("⏳ Running analysis (this may take several minutes)...")
        response = requests.post(url, json=payload, headers=HEADERS, timeout=600)  # 10 minute timeout
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Baseline analysis completed successfully!")
            print(f"   Analysis ID: {result.get('id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            
            # Check if baseline record was created
            if result.get('result'):
                print(f"   ✅ Baseline metrics computed and persisted")
                print(f"   ✅ Results stored in database")
            
            return 0
        else:
            print(f"❌ Baseline analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_BASE_URL}")
        print(f"   Make sure the API server is running")
        return 1
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out. Analysis may still be running.")
        print(f"   Check API server logs for progress")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_baseline_analysis())

