#!/usr/bin/env python3
"""
Generate predicted impact for all policies
Uses the batch endpoint /policies/generate-predicted-impact
"""
import sys
from pathlib import Path
import json

# Try to use httpx (already in FastAPI dependencies) or fallback to basic approach
try:
    import httpx
    USE_HTTPX = True
except ImportError:
    USE_HTTPX = False
    try:
        import urllib.request
        import urllib.parse
        USE_URLLIB = True
    except ImportError:
        USE_URLLIB = False

API_BASE_URL = "http://localhost:8000/api/v1"
AUTH_TOKEN = "dev-token-123"

def generate_all_predicted_impact():
    """Generate predicted impact for all policies using batch endpoint"""
    print("="*60)
    print("Generating Predicted Impact for All Policies")
    print("="*60)
    print()
    
    url = f"{API_BASE_URL}/policies/generate-predicted-impact"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }
    
    if USE_HTTPX:
        print(f"POST {url}")
        try:
            with httpx.Client(timeout=300.0) as client:
                response = client.post(url, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ Success!")
                print(f"Generated for {result.get('generated', 0)} policies")
                if result.get('skipped', 0) > 0:
                    print(f"Skipped {result.get('skipped', 0)} policies (already had predicted impact)")
                if result.get('errors', 0) > 0:
                    print(f"Errors for {result.get('errors', 0)} policies")
                
                if result.get('details'):
                    print("\nDetails:")
                    for detail in result['details']:
                        status_icon = "✅" if detail.get('status') == 'generated' else "⏭️ " if detail.get('status') == 'skipped' else "❌"
                        print(f"  {status_icon} {detail.get('policy_name', 'Unknown')}: {detail.get('status', 'unknown')}")
                        if detail.get('error'):
                            print(f"     Error: {detail.get('error')}")
                
                return result
        except httpx.RequestError as e:
            print(f"❌ Connection error: {e}")
            print("\nMake sure the API server is running:")
            print("  ./start-both-servers.sh")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
            return None
    
    elif USE_URLLIB:
        print(f"POST {url} (using urllib)")
        try:
            req = urllib.request.Request(url, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=300) as response:
                data = response.read()
                result = json.loads(data.decode('utf-8'))
                
                print(f"✅ Success!")
                print(f"Generated for {result.get('generated', 0)} policies")
                return result
        except urllib.error.URLError as e:
            print(f"❌ Connection error: {e}")
            print("\nMake sure the API server is running:")
            print("  ./start-both-servers.sh")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    else:
        print("❌ No HTTP library available. Please install httpx:")
        print("  pip install httpx")
        print("\nOr run this via the UI:")
        print("  1. Go to http://localhost:3050/policies")
        print("  2. Click 'Generate Predicted Impact' button")
        return None

if __name__ == "__main__":
    result = generate_all_predicted_impact()
    
    if result:
        print()
        print("="*60)
        print("✅ Predicted Impact Generation Complete!")
        print("="*60)
        print()
        print("Next steps:")
        print("  1. View predicted impact in UI: http://localhost:3050/policies")
        print("  2. Click on a policy to view its predicted impact")
        print("  3. Run observation analysis to compare predicted vs observed")
        print()
