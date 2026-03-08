#!/usr/bin/env python3
"""
Generate predicted impact for all policies
"""
import sys
import json
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))

# Try to use httpx if available, otherwise use urllib
try:
    import httpx
    USE_HTTPX = True
except ImportError:
    try:
        import urllib.request
        import urllib.parse
        USE_HTTPX = False
    except ImportError:
        print("Error: Need either 'httpx' or 'urllib' to make HTTP requests")
        print("Install with: pip install httpx")
        sys.exit(1)

API_BASE_URL = "http://localhost:8000/api/v1"

def generate_all_predicted_impact():
    """Generate predicted impact for all policies using bulk endpoint"""
    url = f"{API_BASE_URL}/policies/generate-predicted-impact"
    
    print("\n" + "="*60)
    print("Generating Predicted Impact for All Policies")
    print("="*60)
    print(f"Calling: POST {url}")
    print()
    
    try:
        if USE_HTTPX:
            with httpx.Client(timeout=300.0) as client:
                response = client.post(url, json={})
                response.raise_for_status()
                result = response.json()
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps({}).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode('utf-8'))
        
        print("✅ Success!")
        print()
        print(f"Total policies: {result.get('total_policies', 0)}")
        print(f"Generated: {result.get('generated', 0)}")
        print(f"Skipped: {result.get('skipped', 0)}")
        print(f"Errors: {result.get('errors', 0)}")
        
        # Show details
        if 'details' in result:
            details = result.get('details', [])
            generated_items = [d for d in details if d.get('status') == 'generated']
            skipped_items = [d for d in details if d.get('status') == 'skipped']
            error_items = [d for d in details if d.get('status') == 'error']
            
            if generated_items:
                print(f"\n✅ Generated ({len(generated_items)}):")
                for item in generated_items[:10]:
                    name = item.get('policy_name', 'Unknown')
                    policy_id = item.get('policy_id', 'Unknown')
                    conf = item.get('confidence_score', 'N/A')
                    print(f"   - {name} ({policy_id[:8]}...) - Confidence: {conf}")
                if len(generated_items) > 10:
                    print(f"   ... and {len(generated_items) - 10} more")
            
            if skipped_items:
                print(f"\n⏭️  Skipped ({len(skipped_items)}):")
                for item in skipped_items[:5]:
                    name = item.get('policy_name', 'Unknown')
                    reason = item.get('reason', 'Unknown reason')
                    print(f"   - {name}: {reason}")
                if len(skipped_items) > 5:
                    print(f"   ... and {len(skipped_items) - 5} more")
            
            if error_items:
                print(f"\n❌ Errors ({len(error_items)}):")
                for item in error_items[:5]:
                    name = item.get('policy_name', 'Unknown')
                    error = item.get('error', 'Unknown error')
                    print(f"   - {name}: {error[:100]}")
                if len(error_items) > 5:
                    print(f"   ... and {len(error_items) - 5} more")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure:")
        print("  1. API server is running: http://localhost:8000")
        print("  2. Check API logs: tail -f api-server.log")
        return None

def main():
    result = generate_all_predicted_impact()
    
    if result:
        print()
        print("="*60)
        print("✅ Complete!")
        print("="*60)
        print()
        print("Next steps:")
        print("  1. View predicted impact in UI: http://localhost:3050/policies")
        print("  2. Run observation analysis to compare predicted vs observed")
        print()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
