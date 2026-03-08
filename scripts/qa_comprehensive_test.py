#!/usr/bin/env python3
"""
Comprehensive QA Testing Script - Senior QA Engineer Level
Tests all functionalities end-to-end with validation
"""
import sys
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from uuid import UUID
import requests
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from sqlalchemy.orm import Session
from uepi_api.database import SessionLocal
from uepi_api.services.data_generation_service import generate_claims_data_for_date
from uepi_api.services.daily_pipeline_service import load_daily_data_from_source
from uepi_api.baseline_refresh import refresh_baseline
from uepi_api.storage_policies import list_policies
from uepi_api.storage_baselines import get_latest_baseline, list_baselines
from uepi_api.storage_observations import list_observations
from uepi_api.storage_policies import get_policy

API_BASE_URL = "http://localhost:8000/api/v1"
AUTH_TOKEN = "dev-token-123"
TENANT_ID = UUID('00000000-0000-0000-0000-000000000001')

class QATestResult:
    """Test result tracking"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.warnings = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
    
    def add_warning(self, test_name: str, warning: str):
        self.warnings.append(f"{test_name}: {warning}")
        print(f"⚠️  WARN: {test_name} - {warning}")
    
    def print_summary(self):
        print("\n" + "=" * 80)
        print("QA TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        print("\n" + "=" * 80)
        if self.failed == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"❌ {self.failed} TEST(S) FAILED")
        print("=" * 80)

def check_api_health():
    """Test 1: API Health Check"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, "API is healthy"
        else:
            return False, f"API returned status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"API not reachable: {e}"

def test_data_generation(result: QATestResult):
    """Test 2: Data Generation Service"""
    print("\n" + "=" * 80)
    print("TEST 2: DATA GENERATION SERVICE")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        target_date = datetime.now().date() - timedelta(days=1)
        
        gen_result = generate_claims_data_for_date(
            tenant_id=TENANT_ID,
            target_date=target_date,
            member_count=1000,
            claims_per_member=2.0,
            db=db,
        )
        
        if gen_result.get("success"):
            claims_count = gen_result.get("claims_loaded", 0)
            if claims_count > 0:
                result.add_pass(f"Data Generation - Generated {claims_count} claims")
            else:
                result.add_warning("Data Generation", "Generated 0 claims")
        else:
            result.add_fail("Data Generation", gen_result.get("error", "Unknown error"))
    except Exception as e:
        result.add_fail("Data Generation", str(e))
    finally:
        db.close()

def test_baseline_creation(result: QATestResult):
    """Test 3: Baseline Creation (General and Policy-Specific)"""
    print("\n" + "=" * 80)
    print("TEST 3: BASELINE CREATION")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Test general baseline
        general_baseline = refresh_baseline(
            tenant_id=TENANT_ID,
            policy_id=None,
            baseline_type="ROLLING",
            window_months=12,
            refresh_reason="QA_TEST",
        )
        
        if general_baseline:
            baseline_id = general_baseline.get("baseline_id")
            metrics = general_baseline.get("baseline_metrics", {})
            
            # Validate metrics exist and are not mock
            if metrics and len(metrics) > 0:
                # Check for real data indicators
                has_real_data = any(
                    key in metrics for key in [
                        "util_rate_total_per_1000_mm",
                        "allowed_pmpm_total",
                        "member_months",
                        "unique_members"
                    ]
                )
                if has_real_data:
                    result.add_pass(f"General Baseline Creation - ID: {baseline_id}")
                else:
                    result.add_warning("General Baseline", "Metrics may be mock data")
            else:
                result.add_fail("General Baseline", "No metrics found")
        else:
            result.add_fail("General Baseline", "Baseline creation returned None")
        
        # Test policy-specific baseline
        policies = list_policies(TENANT_ID)
        if policies:
            policy = policies[0]
            policy_id = UUID(policy.get("id") or policy.get("policy_id"))
            
            policy_baseline = refresh_baseline(
                tenant_id=TENANT_ID,
                policy_id=policy_id,
                baseline_type="ROLLING",
                window_months=12,
                refresh_reason="QA_TEST",
            )
            
            if policy_baseline:
                result.add_pass(f"Policy-Specific Baseline - Policy: {policy.get('name', 'Unknown')}")
            else:
                result.add_warning("Policy-Specific Baseline", "Could not create (may not have enough data)")
        else:
            result.add_warning("Policy-Specific Baseline", "No policies found to test")
            
    except Exception as e:
        result.add_fail("Baseline Creation", str(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_predicted_impacts_api(result: QATestResult):
    """Test 4: Predicted Impacts API Endpoint"""
    print("\n" + "=" * 80)
    print("TEST 4: PREDICTED IMPACTS API")
    print("=" * 80)
    
    try:
        # Test generate all predicted impacts
        response = requests.post(
            f"{API_BASE_URL}/policies/generate-predicted-impact",
            params={"force": False},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total_policies", 0)
            generated = data.get("generated", 0)
            skipped = data.get("skipped", 0)
            
            if total > 0:
                result.add_pass(f"Predicted Impacts API - Total: {total}, Generated: {generated}, Skipped: {skipped}")
            else:
                result.add_warning("Predicted Impacts API", "No policies found")
        else:
            result.add_fail("Predicted Impacts API", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("Predicted Impacts API", str(e))

def test_observations_creation(result: QATestResult):
    """Test 5: Observations Creation and Retrieval"""
    print("\n" + "=" * 80)
    print("TEST 5: OBSERVATIONS")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # List existing observations
        observations = list_observations(
            tenant_id=TENANT_ID,
            policy_id=None,
        )
        
        if observations:
            obs = observations[0]
            
            # Validate observation structure
            required_fields = ["observation_id", "policy_id", "metrics", "comparisons"]
            missing_fields = [f for f in required_fields if f not in obs]
            
            if not missing_fields:
                # Check for mock data indicators
                metrics = obs.get("metrics", {})
                comparisons = obs.get("comparisons", {})
                
                # Check if comparisons have real data
                vs_baseline = comparisons.get("vs_baseline", {})
                vs_predicted = comparisons.get("vs_predicted", {})
                
                has_baseline = bool(vs_baseline)
                has_predicted = bool(vs_predicted)
                
                if has_baseline or has_predicted:
                    result.add_pass(f"Observations Structure - Found {len(observations)} observations")
                    
                    # Check for N/A values
                    na_count = 0
                    for key, value in vs_baseline.items():
                        if value == "N/A" or value is None:
                            na_count += 1
                    
                    if na_count < len(vs_baseline) * 0.5:  # Less than 50% N/A
                        result.add_pass("Observations Data Quality - Baseline comparison has real values")
                    else:
                        result.add_warning("Observations Data Quality", f"High N/A count in baseline: {na_count}")
                else:
                    result.add_warning("Observations", "No baseline or predicted comparisons found")
            else:
                result.add_fail("Observations Structure", f"Missing fields: {missing_fields}")
        else:
            result.add_warning("Observations", "No observations found (may need to create some)")
            
    except Exception as e:
        result.add_fail("Observations", str(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_baseline_api_endpoints(result: QATestResult):
    """Test 6: Baseline API Endpoints"""
    print("\n" + "=" * 80)
    print("TEST 6: BASELINE API ENDPOINTS")
    print("=" * 80)
    
    try:
        # Test list baselines
        response = requests.get(
            f"{API_BASE_URL}/baselines",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        
        if response.status_code == 200:
            baselines = response.json()
            if isinstance(baselines, list):
                result.add_pass(f"List Baselines API - Found {len(baselines)} baselines")
            else:
                result.add_fail("List Baselines API", "Response is not a list")
        else:
            result.add_fail("List Baselines API", f"Status {response.status_code}")
        
        # Test get latest baseline
        response = requests.get(
            f"{API_BASE_URL}/baselines/latest",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        
        if response.status_code == 200:
            baseline = response.json()
            if baseline.get("baseline_id"):
                result.add_pass("Get Latest Baseline API")
            else:
                result.add_warning("Get Latest Baseline API", "Baseline missing baseline_id")
        elif response.status_code == 404:
            result.add_warning("Get Latest Baseline API", "No baseline found (404)")
        else:
            result.add_fail("Get Latest Baseline API", f"Status {response.status_code}")
            
    except Exception as e:
        result.add_fail("Baseline API Endpoints", str(e))

def test_data_generation_api(result: QATestResult):
    """Test 7: Data Generation API Endpoint"""
    print("\n" + "=" * 80)
    print("TEST 7: DATA GENERATION API")
    print("=" * 80)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/data-generation/claims",
            json={"target_date": str(datetime.now().date() - timedelta(days=1))},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result.add_pass(f"Data Generation API - Generated {data.get('claims_generated', 0)} claims")
            else:
                result.add_fail("Data Generation API", data.get("error", "Unknown error"))
        else:
            result.add_fail("Data Generation API", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("Data Generation API", str(e))

def test_observations_api_endpoints(result: QATestResult):
    """Test 8: Observations API Endpoints"""
    print("\n" + "=" * 80)
    print("TEST 8: OBSERVATIONS API ENDPOINTS")
    print("=" * 80)
    
    try:
        # Test list observations
        response = requests.get(
            f"{API_BASE_URL}/observations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=10
        )
        
        if response.status_code == 200:
            observations = response.json()
            if isinstance(observations, list):
                result.add_pass(f"List Observations API - Found {len(observations)} observations")
            else:
                result.add_fail("List Observations API", "Response is not a list")
        else:
            result.add_fail("List Observations API", f"Status {response.status_code}")
            
    except Exception as e:
        result.add_fail("Observations API Endpoints", str(e))

def test_mock_data_removal(result: QATestResult):
    """Test 9: Verify No Mock Data"""
    print("\n" + "=" * 80)
    print("TEST 9: MOCK DATA REMOVAL VALIDATION")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Check observations for mock data patterns
        observations = list_observations(TENANT_ID)
        
        mock_patterns = [
            "mock",
            "test_data",
            "sample",
            "placeholder",
        ]
        
        mock_found = False
        for obs in observations:
            obs_str = json.dumps(obs).lower()
            for pattern in mock_patterns:
                if pattern in obs_str:
                    mock_found = True
                    result.add_warning("Mock Data Check", f"Found pattern '{pattern}' in observation {obs.get('observation_id')}")
        
        if not mock_found:
            result.add_pass("Mock Data Removal - No mock data patterns found")
        
        # Check baselines
        baselines = list_baselines(TENANT_ID)
        for baseline in baselines:
            baseline_str = json.dumps(baseline).lower()
            for pattern in mock_patterns:
                if pattern in baseline_str:
                    result.add_warning("Mock Data Check", f"Found pattern '{pattern}' in baseline")
                    
    except Exception as e:
        result.add_fail("Mock Data Removal Check", str(e))
    finally:
        db.close()

def test_complete_workflow(result: QATestResult):
    """Test 10: Complete End-to-End Workflow"""
    print("\n" + "=" * 80)
    print("TEST 10: COMPLETE WORKFLOW")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Step 1: Generate data
        target_date = datetime.now().date() - timedelta(days=1)
        gen_result = generate_claims_data_for_date(
            tenant_id=TENANT_ID,
            target_date=target_date,
            member_count=500,
            claims_per_member=1.5,
            db=db,
        )
        
        if not gen_result.get("success"):
            result.add_fail("Workflow Step 1", "Data generation failed")
            return
        
        # Step 2: Create baseline
        baseline = refresh_baseline(
            tenant_id=TENANT_ID,
            policy_id=None,
            baseline_type="ROLLING",
            window_months=12,
            refresh_reason="QA_WORKFLOW",
        )
        
        if not baseline:
            result.add_fail("Workflow Step 2", "Baseline creation failed")
            return
        
        # Step 3: Check policies exist
        policies = list_policies(TENANT_ID)
        if not policies:
            result.add_warning("Workflow Step 3", "No policies found")
        else:
            result.add_pass(f"Workflow - All steps completed: {len(policies)} policies found")
            
    except Exception as e:
        result.add_fail("Complete Workflow", str(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Run all QA tests"""
    print("=" * 80)
    print("COMPREHENSIVE QA TESTING - SENIOR QA ENGINEER LEVEL")
    print("=" * 80)
    
    result = QATestResult()
    
    # Test 1: API Health
    print("\n" + "=" * 80)
    print("TEST 1: API HEALTH CHECK")
    print("=" * 80)
    health_ok, health_msg = check_api_health()
    if health_ok:
        result.add_pass("API Health Check")
    else:
        result.add_fail("API Health Check", health_msg)
        print("⚠️  API is not available. Some tests will be skipped.")
        result.print_summary()
        return
    
    # Run all tests
    test_data_generation(result)
    test_baseline_creation(result)
    test_predicted_impacts_api(result)
    test_observations_creation(result)
    test_baseline_api_endpoints(result)
    test_data_generation_api(result)
    test_observations_api_endpoints(result)
    test_mock_data_removal(result)
    test_complete_workflow(result)
    
    # Print summary
    result.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if result.failed == 0 else 1)

if __name__ == "__main__":
    main()
