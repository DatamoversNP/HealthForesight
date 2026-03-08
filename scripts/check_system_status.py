#!/usr/bin/env python3
"""
Comprehensive system status check
"""
import requests
import sys
from datetime import datetime, timedelta
from collections import defaultdict

API_BASE_URL = "http://localhost:8000/api/v1"

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, "✅ API is running"
        else:
            return False, f"❌ API returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "❌ API server is not running"
    except Exception as e:
        return False, f"❌ Error checking API: {e}"

def get_database_counts():
    """Get counts from database via API"""
    counts = {}
    
    try:
        # Get claims count
        response = requests.get(f"{API_BASE_URL}/database-viewer/tables/claims_lines/count", timeout=10)
        if response.status_code == 200:
            counts['claims'] = response.json().get('row_count', 0)
        else:
            counts['claims'] = 0
    except:
        counts['claims'] = 0
    
    try:
        # Get baselines count
        response = requests.get(f"{API_BASE_URL}/baselines", timeout=10)
        if response.status_code == 200:
            baselines = response.json()
            counts['baselines'] = len(baselines) if isinstance(baselines, list) else 0
            # Count general vs policy-specific
            general = sum(1 for b in baselines if b.get('baseline_type') == 'GENERAL' or not b.get('policy_id'))
            policy_specific = sum(1 for b in baselines if b.get('policy_id'))
            counts['baselines_general'] = general
            counts['baselines_policy_specific'] = policy_specific
        else:
            counts['baselines'] = 0
            counts['baselines_general'] = 0
            counts['baselines_policy_specific'] = 0
    except:
        counts['baselines'] = 0
        counts['baselines_general'] = 0
        counts['baselines_policy_specific'] = 0
    
    try:
        # Get observations count
        response = requests.get(f"{API_BASE_URL}/observations", timeout=10)
        if response.status_code == 200:
            observations = response.json()
            counts['observations'] = len(observations) if isinstance(observations, list) else 0
        else:
            counts['observations'] = 0
    except:
        counts['observations'] = 0
    
    try:
        # Get policies count
        response = requests.get(f"{API_BASE_URL}/policies", timeout=10)
        if response.status_code == 200:
            policies = response.json()
            counts['policies'] = len(policies) if isinstance(policies, list) else 0
            active = sum(1 for p in policies if p.get('status') == 'ACTIVE')
            counts['policies_active'] = active
        else:
            counts['policies'] = 0
            counts['policies_active'] = 0
    except:
        counts['policies'] = 0
        counts['policies_active'] = 0
    
    try:
        # Get analyses count
        response = requests.get(f"{API_BASE_URL}/analyses", timeout=10)
        if response.status_code == 200:
            analyses = response.json()
            counts['analyses'] = len(analyses) if isinstance(analyses, list) else 0
            completed = sum(1 for a in analyses if a.get('status') == 'COMPLETED')
            counts['analyses_completed'] = completed
        else:
            counts['analyses'] = 0
            counts['analyses_completed'] = 0
    except:
        counts['analyses'] = 0
        counts['analyses_completed'] = 0
    
    return counts

def get_recent_data_info():
    """Get information about recent data"""
    info = {}
    
    try:
        # Get claims data for last 7 days
        response = requests.get(f"{API_BASE_URL}/database-viewer/tables/claims_lines/data", 
                               params={"page": 1, "page_size": 100}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rows = data.get('rows', [])
            if rows:
                # Check service dates
                dates = []
                for row in rows:
                    if 'service_date' in row:
                        dates.append(row['service_date'])
                if dates:
                    info['latest_claim_date'] = max(dates)
                    info['oldest_claim_date'] = min(dates)
                    info['sample_claims'] = len(rows)
    except:
        pass
    
    return info

def main():
    print("="*80)
    print("📊 SYSTEM STATUS CHECK")
    print("="*80)
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check API health
    api_ok, api_msg = check_api_health()
    print(f"API Status: {api_msg}")
    
    if not api_ok:
        print("\n❌ Cannot proceed - API server is not running")
        print("   Start it with: cd apps/api && python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print()
    
    # Get database counts
    print("📈 DATABASE COUNTS")
    print("-" * 80)
    counts = get_database_counts()
    
    print(f"   Claims:           {counts.get('claims', 0):,}")
    print(f"   Policies:        {counts.get('policies', 0)} (Active: {counts.get('policies_active', 0)})")
    print(f"   Baselines:       {counts.get('baselines', 0)}")
    print(f"     - General:     {counts.get('baselines_general', 0)}")
    print(f"     - Policy-Specific: {counts.get('baselines_policy_specific', 0)}")
    print(f"   Analyses:        {counts.get('analyses', 0)} (Completed: {counts.get('analyses_completed', 0)})")
    print(f"   Observations:    {counts.get('observations', 0)}")
    
    print()
    
    # Get recent data info
    print("📅 RECENT DATA")
    print("-" * 80)
    data_info = get_recent_data_info()
    if data_info.get('latest_claim_date'):
        print(f"   Latest Claim Date: {data_info.get('latest_claim_date')}")
        print(f"   Oldest Claim Date: {data_info.get('oldest_claim_date')}")
    else:
        print("   ⚠️  No claims data found in database")
    
    print()
    
    # Status assessment
    print("🔍 STATUS ASSESSMENT")
    print("-" * 80)
    
    issues = []
    warnings = []
    
    if counts.get('claims', 0) == 0:
        issues.append("❌ No claims data in database")
    elif counts.get('claims', 0) < 1000:
        warnings.append(f"⚠️  Low claims count ({counts.get('claims', 0):,}) - may need more data")
    
    if counts.get('policies_active', 0) == 0:
        issues.append("❌ No active policies")
    
    if counts.get('baselines', 0) == 0:
        issues.append("❌ No baselines created")
    elif counts.get('baselines_policy_specific', 0) == 0:
        warnings.append(f"⚠️  No policy-specific baselines (only {counts.get('baselines_general', 0)} general)")
    
    if counts.get('analyses_completed', 0) == 0:
        warnings.append("⚠️  No completed analyses")
    
    if counts.get('observations', 0) == 0:
        warnings.append("⚠️  No observations created")
    
    if issues:
        print("   CRITICAL ISSUES:")
        for issue in issues:
            print(f"      {issue}")
        print()
    
    if warnings:
        print("   WARNINGS:")
        for warning in warnings:
            print(f"      {warning}")
        print()
    
    if not issues and not warnings:
        print("   ✅ System appears healthy!")
        print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 80)
    
    if counts.get('claims', 0) == 0:
        print("   1. Generate claims data:")
        print("      python3 scripts/generate_data_and_create_baselines_observations.py")
    elif counts.get('baselines_policy_specific', 0) == 0 and counts.get('policies_active', 0) > 0:
        print("   1. Create policy-specific baselines:")
        print("      - Check if policy-scoped data generation is working")
        print("      - Verify policy scope matches claims data")
        print("      - Run: python3 scripts/generate_data_and_create_baselines_observations.py")
    elif counts.get('observations', 0) == 0 and counts.get('analyses_completed', 0) > 0:
        print("   1. Create observations from completed analyses:")
        print("      - Check observation creation endpoint")
        print("      - Verify analysis results are valid")
    
    print()
    print("="*80)

if __name__ == "__main__":
    main()
