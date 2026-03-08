#!/usr/bin/env python3
"""
Complete script to:
1. Update all pipelines with correct field mappings
2. Run all pipelines to ingest source data
3. Verify results
"""
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def main():
    print("=" * 80)
    print("COMPLETE PIPELINE FIX AND RUN")
    print("=" * 80)
    print()
    
    # Step 1: Update pipelines
    print("STEP 1: Updating pipeline field mappings...")
    print("-" * 80)
    try:
        from apps.api.scripts.update_pipelines_field_mappings import update_pipelines
        update_pipelines()
    except Exception as e:
        print(f"❌ Error updating pipelines: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 2: Validate
    print("STEP 2: Validating pipelines...")
    print("-" * 80)
    try:
        from apps.api.scripts.validate_target_data_model import validate_pipelines
        validate_pipelines()
    except Exception as e:
        print(f"⚠️  Validation warning: {e}")
    
    print()
    
    # Step 3: Run pipelines
    print("STEP 3: Running all pipelines...")
    print("-" * 80)
    try:
        from apps.api.scripts.run_all_pipelines_direct import run_all_pipelines
        run_all_pipelines()
    except Exception as e:
        print(f"❌ Error running pipelines: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 4: Count and compare
    print("STEP 4: Counting and comparing records...")
    print("-" * 80)
    try:
        from apps.api.scripts.count_target_records import count_target_records
        count_target_records()
    except Exception as e:
        print(f"⚠️  Error counting target records: {e}")
    
    try:
        from apps.api.scripts.compare_source_target_counts import compare_counts
        compare_counts()
    except Exception as e:
        print(f"⚠️  Error comparing counts: {e}")
    
    print()
    print("=" * 80)
    print("✅ COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()

