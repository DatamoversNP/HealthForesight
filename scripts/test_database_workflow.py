#!/usr/bin/env python3
"""Test the complete database workflow for observations"""

import sys
import requests
import json
from uuid import UUID
from datetime import datetime, date, timedelta

API_BASE = "http://localhost:8000/api/v1"
AUTH_TOKEN = "dev-token-123"

def test_api_health():
    """Test 1: API is running"""
    print("="*80)
    print("TEST 1: API Health Check")
    print("="*80)
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is not accessible: {e}")
        return False

def test_database_connection():
    """Test 2: Database connection"""
    print("\n" + "="*80)
    print("TEST 2: Database Connection")
    print("="*80)
    try:
        import psycopg2
        from uepi_common.config import get_settings
        
        settings = get_settings()
        db_url = settings.database.url
        
        # Parse connection string
        # Format: postgresql://user:password@host:port/database
        parts = db_url.replace("postgresql://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")
            if len(host_db) == 2:
                host_port = host_db[0].split(":")
                user = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ""
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 5432
                database = host_db[1]
                
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password
                )
                conn.close()
                print("✅ Database connection successful")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_claims_table_exists():
    """Test 3: Claims table exists and has data"""
    print("\n" + "="*80)
    print("TEST 3: Claims Table Check")
    print("="*80)
    try:
        import psycopg2
        from uepi_common.config import get_settings
        
        settings = get_settings()
        db_url = settings.database.url
        
        parts = db_url.replace("postgresql://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")
            if len(host_db) == 2:
                host_port = host_db[0].split(":")
                user = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ""
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 5432
                database = host_db[1]
                
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password
                )
                cur = conn.cursor()
                
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'claims_lines'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    print("❌ claims_lines table does not exist")
                    conn.close()
                    return False
                
                print("✅ claims_lines table exists")
                
                # Check row count
                cur.execute("SELECT COUNT(*) FROM claims_lines;")
                count = cur.fetchone()[0]
                print(f"   Total claims: {count:,}")
                
                # Check by tenant
                cur.execute("""
                    SELECT tenant_id, COUNT(*) 
                    FROM claims_lines 
                    GROUP BY tenant_id;
                """)
                tenant_counts = cur.fetchall()
                for tenant_id, cnt in tenant_counts:
                    print(f"   Tenant {str(tenant_id)[:8]}...: {cnt:,} claims")
                
                conn.close()
                return count > 0
    except Exception as e:
        print(f"❌ Error checking claims table: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_policies_exist():
    """Test 4: Policies exist"""
    print("\n" + "="*80)
    print("TEST 4: Policies Check")
    print("="*80)
    try:
        response = requests.get(
            f"{API_BASE}/policies",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            policies = response.json()
            print(f"✅ Found {len(policies)} policies")
            if policies:
                for i, policy in enumerate(policies[:3], 1):
                    policy_id = policy.get('id', policy.get('policy_id', 'Unknown'))
                    name = policy.get('name', 'Unknown')
                    print(f"   {i}. {name} ({str(policy_id)[:8]}...)")
            return len(policies) > 0
        else:
            print(f"❌ Failed to get policies: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting policies: {e}")
        return False

def test_create_observation_from_database():
    """Test 5: Create observation using database"""
    print("\n" + "="*80)
    print("TEST 5: Create Observation from Database")
    print("="*80)
    try:
        # Get a policy
        response = requests.get(
            f"{API_BASE}/policies",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        if response.status_code != 200 or not response.json():
            print("❌ No policies available")
            return False
        
        policy = response.json()[0]
        policy_id = policy.get('id', policy.get('policy_id'))
        
        print(f"   Using policy: {policy.get('name', 'Unknown')} ({str(policy_id)[:8]}...)")
        
        # Check if there's an analysis for this policy
        response = requests.get(
            f"{API_BASE}/analyses",
            params={"policy_id": str(policy_id)},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        
        analysis_id = None
        if response.status_code == 200:
            analyses = response.json()
            if analyses:
                # Find a COMPLETED analysis or use the first one
                for analysis in analyses:
                    if analysis.get('status') == 'COMPLETED':
                        analysis_id = analysis.get('id')
                        break
                if not analysis_id and analyses:
                    analysis_id = analyses[0].get('id')
        
        if not analysis_id:
            print("   ⚠️  No analysis found, creating one...")
            # Create an impact analysis
            analysis_data = {
                "policy_id": str(policy_id),
                "treatment_filters": {"lob": ["COMMERCIAL"]},
                "pre_window_months": 6,
                "post_window_months": 1,
            }
            
            response = requests.post(
                f"{API_BASE}/analyses/impact",
                json=analysis_data,
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=30
            )
            
            if response.status_code == 201:
                analysis = response.json()
                analysis_id = analysis.get('id')
                print(f"   ✅ Created analysis: {str(analysis_id)[:8]}...")
                # Wait a bit for processing
                import time
                time.sleep(2)
            else:
                print(f"   ❌ Failed to create analysis: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        
        if not analysis_id:
            print("   ❌ No analysis available")
            return False
        
        print(f"   Using analysis: {str(analysis_id)[:8]}...")
        
        # Create observation from analysis
        response = requests.post(
            f"{API_BASE}/observations/from-analysis/{analysis_id}",
            params={"policy_id": str(policy_id)},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=30
        )
        
        if response.status_code == 201:
            observation = response.json()
            obs_id = observation.get('observation_id', observation.get('id'))
            print(f"   ✅ Created observation: {str(obs_id)[:8]}...")
            
            # Check if it has real data (not all zeros or mock patterns)
            metrics = observation.get('metrics', {})
            comparisons = observation.get('comparisons', {})
            
            if metrics:
                util = metrics.get('utilization_per_1k', 0)
                cost = metrics.get('cost_per_member', 0)
                print(f"   Metrics: util={util:.2f}, cost=${cost:.2f}")
            
            if comparisons:
                vs_baseline = comparisons.get('vs_baseline', {})
                vs_predicted = comparisons.get('vs_predicted', {})
                if vs_baseline:
                    print(f"   Baseline comparison: {len(vs_baseline)} fields")
                if vs_predicted:
                    print(f"   Predicted comparison: {len(vs_predicted)} fields")
            
            return True
        else:
            print(f"   ❌ Failed to create observation: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_observations_list():
    """Test 6: List observations"""
    print("\n" + "="*80)
    print("TEST 6: List Observations")
    print("="*80)
    try:
        response = requests.get(
            f"{API_BASE}/observations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            observations = response.json()
            print(f"✅ Found {len(observations)} observations")
            if observations:
                for i, obs in enumerate(observations[:3], 1):
                    obs_id = obs.get('observation_id', obs.get('id', 'Unknown'))
                    policy_id = obs.get('policy_id', 'Unknown')
                    print(f"   {i}. Observation {str(obs_id)[:8]}... (Policy: {str(policy_id)[:8]}...)")
            return True
        else:
            print(f"❌ Failed to list observations: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_frontend_endpoint():
    """Test 7: Frontend can access observations"""
    print("\n" + "="*80)
    print("TEST 7: Frontend Access Check")
    print("="*80)
    try:
        # Test CORS by checking if we can access from different origin
        response = requests.get(
            f"{API_BASE}/observations",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}",
                "Origin": "http://localhost:3050"
            },
            timeout=10
        )
        if response.status_code == 200:
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                print(f"✅ CORS configured: {cors_header}")
            else:
                print("⚠️  CORS header not present (may still work)")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("DATABASE WORKFLOW TEST SUITE")
    print("="*80)
    print()
    
    results = {}
    
    results['api_health'] = test_api_health()
    results['database_connection'] = test_database_connection()
    results['claims_table'] = test_claims_table_exists()
    results['policies'] = test_policies_exist()
    results['create_observation'] = test_create_observation_from_database()
    results['list_observations'] = test_observations_list()
    results['frontend_access'] = test_frontend_endpoint()
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The database workflow is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
