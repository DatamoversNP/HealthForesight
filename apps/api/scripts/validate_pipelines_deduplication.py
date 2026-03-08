#!/usr/bin/env python3
"""
Validate that all pipelines have proper deduplication configured
"""
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import list_pipelines

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def validate_deduplication():
    """Validate all pipelines have deduplication configured"""
    print("=" * 80)
    print("PIPELINE DEDUPLICATION VALIDATION")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print()
    
    pipelines = list_pipelines(DEFAULT_TENANT_ID)
    
    if not pipelines:
        print("❌ No pipelines found in database.")
        return
    
    print(f"📊 Validating {len(pipelines)} pipelines...\n")
    
    issues = []
    valid_count = 0
    
    for pipeline in pipelines:
        name = pipeline.get("pipeline_name") or pipeline.get("name") or "Unknown"
        dedup = pipeline.get("deduplication", {})
        strategy = dedup.get("strategy") if isinstance(dedup, dict) else None
        
        if not strategy or strategy == "NONE":
            issues.append({
                "pipeline": name,
                "issue": "No deduplication strategy configured",
                "recommendation": "Add KEY_FIELDS or HASH strategy"
            })
        elif strategy == "KEY_FIELDS":
            key_fields = dedup.get("key_fields", [])
            if not key_fields:
                issues.append({
                    "pipeline": name,
                    "issue": "KEY_FIELDS strategy but no key_fields specified",
                    "recommendation": "Add key_fields to deduplication config"
                })
            else:
                valid_count += 1
                print(f"✅ {name}")
                print(f"   Strategy: {strategy}")
                print(f"   Key Fields: {', '.join(key_fields)}")
        elif strategy == "HASH":
            valid_count += 1
            print(f"✅ {name}")
            print(f"   Strategy: {strategy} (uses record_hash)")
        else:
            valid_count += 1
            print(f"✅ {name}")
            print(f"   Strategy: {strategy}")
        print()
    
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Valid pipelines: {valid_count}")
    print(f"⚠️  Issues found: {len(issues)}")
    print()
    
    if issues:
        print("ISSUES TO FIX:")
        print("-" * 80)
        for issue in issues:
            print(f"Pipeline: {issue['pipeline']}")
            print(f"  Issue: {issue['issue']}")
            print(f"  Recommendation: {issue['recommendation']}")
            print()
    else:
        print("🎉 All pipelines have proper deduplication configured!")
        print()
        print("Deduplication strategies:")
        print("  - KEY_FIELDS: Uses specified key fields to identify duplicates")
        print("  - HASH: Uses record_hash to identify duplicates")
        print("  - SOURCE_ID: Uses source record ID to identify duplicates")
        print()
        print("Pipelines will automatically handle duplicate records during ingestion.")

if __name__ == "__main__":
    validate_deduplication()

