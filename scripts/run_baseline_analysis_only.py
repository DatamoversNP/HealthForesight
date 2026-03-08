#!/usr/bin/env python3
"""Run baseline analysis to compute all metrics from metric dictionary"""
import requests
import json
import sys
from pathlib import Path

# Add project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from uepi_api.storage_auth import DEFAULT_TENANT_ID

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}


def run_baseline_analysis():
    """Run baseline analysis with comprehensive date range"""
    print("\n" + "="*60)
    print("Running Baseline Analysis")
    print("="*60)
    
    url = f"{API_BASE_URL}/analyses/baseline"
    payload = {
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "n_clusters": 5
    }
    
    print(f"📊 Requesting baseline analysis...")
    print(f"   Date range: {payload['start_date']} to {payload['end_date']}")
    print(f"   Provider clusters: {payload['n_clusters']}")
    print()
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=600)  # 10 minute timeout
        response.raise_for_status()
        result = response.json()
        
        analysis_id = result.get('id')
        status = result.get('status')
        
        print(f"✅ Baseline analysis initiated successfully!")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Status: {status}")
        print()
        
        if result.get('baseline_created'):
            print("✅ Baseline record created with computed metrics")
        
        # Show metrics if available in result
        if 'result' in result:
            result_data = result['result']
            if 'benchmarks' in result_data:
                print(f"   Benchmarks computed: {len(result_data['benchmarks'])}")
            if 'time_series' in result_data:
                print(f"   Time series points: {len(result_data['time_series'])}")
            if 'provider_archetypes' in result_data:
                print(f"   Provider archetypes: {len(result_data['provider_archetypes'])}")
        
        print()
        print("📋 Next steps:")
        print("   1. Check baseline metrics in UI: http://localhost:3050/baseline-analysis")
        print("   2. Baseline metrics will be used for policy-scoped baselines")
        print("   3. Run predicted impact generation for policies")
        
        return analysis_id
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error running baseline analysis: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                print(f"   Error Detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Response Text: {e.response.text[:500]}")
        print()
        print("Troubleshooting:")
        print("   1. Ensure API server is running: ./restart-api-server.sh")
        print("   2. Check API logs: tail -f api-server.log")
        print("   3. Verify claims data exists in: apps/data/target_data_model/{tenant_id}/CLAIMS_LINES/")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point"""
    print("="*60)
    print("Baseline Analysis Runner")
    print("="*60)
    print()
    print("This will compute comprehensive baseline metrics including:")
    print("  ✓ Utilization rates (total and policy-scoped)")
    print("  ✓ Cost metrics (PMPM, annualized)")
    print("  ✓ Mix metrics (SOC shares, network, provider concentration)")
    print("  ✓ OON leakage rates")
    print("  ✓ Provider HHI (concentration index)")
    print()
    
    analysis_id = run_baseline_analysis()
    
    if analysis_id:
        print("\n" + "="*60)
        print("✅ Baseline analysis completed!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Baseline analysis failed")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
