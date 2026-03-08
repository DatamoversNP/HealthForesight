#!/usr/bin/env python3
"""Test database workflow code directly (no API needed)"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

def test_imports():
    """Test 1: All imports work"""
    print("="*80)
    print("TEST 1: Import Check")
    print("="*80)
    try:
        from uepi_api.database_claims_loader import (
            load_claims_from_database,
            load_claims_for_observation,
            compute_metrics_from_database_claims
        )
        print("✅ database_claims_loader imports successful")
        
        from uepi_api.repositories.canonical_data import CanonicalDataRepository
        print("✅ CanonicalDataRepository import successful")
        
        from uepi_api.models.canonical_data import ClaimsLineDB
        print("✅ ClaimsLineDB model import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Test 2: Database models are correct"""
    print("\n" + "="*80)
    print("TEST 2: Database Models Check")
    print("="*80)
    try:
        from uepi_api.models.canonical_data import ClaimsLineDB
        from sqlalchemy import inspect
        
        # Check table name
        assert ClaimsLineDB.__tablename__ == "claims_lines", "Wrong table name"
        print("✅ Table name correct: claims_lines")
        
        # Check required columns exist
        required_columns = [
            'tenant_id', 'claim_id', 'claim_line_id', 'member_id', 
            'provider_id', 'service_date', 'lob', 'market',
            'service_category', 'allowed_amount', 'paid_amount'
        ]
        
        mapper = inspect(ClaimsLineDB)
        column_names = [col.name for col in mapper.columns]
        
        for col in required_columns:
            assert col in column_names, f"Missing column: {col}"
        
        print(f"✅ All required columns present ({len(required_columns)} columns)")
        return True
    except Exception as e:
        print(f"❌ Model check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_repository_methods():
    """Test 3: Repository methods exist"""
    print("\n" + "="*80)
    print("TEST 3: Repository Methods Check")
    print("="*80)
    try:
        from uepi_api.repositories.canonical_data import CanonicalDataRepository
        
        # Check required methods exist
        required_methods = [
            'get_claims_lines',
            'bulk_insert_claims_lines',
            'count_claims_lines'
        ]
        
        for method in required_methods:
            assert hasattr(CanonicalDataRepository, method), f"Missing method: {method}"
            print(f"✅ Method exists: {method}")
        
        return True
    except Exception as e:
        print(f"❌ Repository check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_claims_loader_functions():
    """Test 4: Claims loader functions exist"""
    print("\n" + "="*80)
    print("TEST 4: Claims Loader Functions Check")
    print("="*80)
    try:
        from uepi_api.database_claims_loader import (
            load_claims_from_database,
            load_claims_for_observation,
            compute_metrics_from_database_claims
        )
        
        # Check function signatures
        import inspect
        
        # Check load_claims_from_database
        sig = inspect.signature(load_claims_from_database)
        params = list(sig.parameters.keys())
        assert 'tenant_id' in params, "Missing tenant_id parameter"
        assert 'start_date' in params, "Missing start_date parameter"
        assert 'end_date' in params, "Missing end_date parameter"
        print("✅ load_claims_from_database signature correct")
        
        # Check load_claims_for_observation
        sig = inspect.signature(load_claims_for_observation)
        params = list(sig.parameters.keys())
        assert 'tenant_id' in params, "Missing tenant_id parameter"
        assert 'policy_id' in params, "Missing policy_id parameter"
        assert 'policy_effective_date' in params, "Missing policy_effective_date parameter"
        print("✅ load_claims_for_observation signature correct")
        
        # Check compute_metrics_from_database_claims
        sig = inspect.signature(compute_metrics_from_database_claims)
        params = list(sig.parameters.keys())
        assert 'claims_df' in params, "Missing claims_df parameter"
        print("✅ compute_metrics_from_database_claims signature correct")
        
        return True
    except Exception as e:
        print(f"❌ Function check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_observation_route_uses_database():
    """Test 5: Observation route imports database loader"""
    print("\n" + "="*80)
    print("TEST 5: Observation Route Database Integration")
    print("="*80)
    try:
        # Read the observations.py file
        observations_file = project_root / "apps" / "api" / "src" / "uepi_api" / "routers" / "observations.py"
        content = observations_file.read_text()
        
        # Check for database loader import
        if "database_claims_loader" in content:
            print("✅ database_claims_loader imported in observations.py")
        else:
            print("❌ database_claims_loader not found in observations.py")
            return False
        
        # Check for load_claims_for_observation usage
        if "load_claims_for_observation" in content:
            print("✅ load_claims_for_observation used in observations.py")
        else:
            print("❌ load_claims_for_observation not found in observations.py")
            return False
        
        # Check for compute_metrics_from_database_claims usage
        if "compute_metrics_from_database_claims" in content:
            print("✅ compute_metrics_from_database_claims used in observations.py")
        else:
            print("❌ compute_metrics_from_database_claims not found in observations.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Route check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("DATABASE WORKFLOW CODE TEST")
    print("="*80)
    print()
    
    results = {}
    
    results['imports'] = test_imports()
    results['models'] = test_database_models()
    results['repository'] = test_repository_methods()
    results['loader_functions'] = test_claims_loader_functions()
    results['route_integration'] = test_observation_route_uses_database()
    
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
        print("\n🎉 All code tests passed!")
        print("\nNext steps:")
        print("1. Start the API server: cd apps/api/src && python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload")
        print("2. Run manual API tests (see MANUAL_TEST_INSTRUCTIONS.md)")
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
