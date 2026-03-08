#!/usr/bin/env python3
"""
Count target records after pipeline runs
Counts records in target data model (blob storage)
"""
import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

TARGET_DATA_DIR = project_root / "data" / "target_data_model"
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def count_target_records():
    """Count all target records"""
    print("=" * 80)
    print("TARGET DATA MODEL RECORD COUNTS")
    print("=" * 80)
    print(f"Target Directory: {TARGET_DATA_DIR}")
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tenant_dir = TARGET_DATA_DIR / str(DEFAULT_TENANT_ID)
    if not tenant_dir.exists():
        print(f"❌ Target directory not found: {tenant_dir}")
        print("   Run pipelines first to create target data.")
        return
    
    counts = {}
    total_records = 0
    
    # Count records in each dataset directory
    print("📊 Counting target dataset files...")
    for dataset_dir in sorted(tenant_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        
        dataset_name = dataset_dir.name
        dataset_total = 0
        
        # Count Parquet files in dataset directory
        for parquet_file in sorted(dataset_dir.glob("*.parquet")):
            try:
                df = pd.read_parquet(parquet_file)
                file_count = len(df)
                dataset_total += file_count
                print(f"    {parquet_file.name:50s} {file_count:>10,} records")
            except Exception as e:
                print(f"    ⚠️  Error reading {parquet_file.name}: {e}")
        
        if dataset_total > 0:
            counts[dataset_name] = dataset_total
            total_records += dataset_total
            print(f"  {dataset_name:40s} {dataset_total:>10,} records")
            print()
    
    if not counts:
        print("  No target data found. Run pipelines to ingest source data.")
        print()
    else:
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for dataset, count in sorted(counts.items()):
            print(f"{dataset:40s} {count:>10,} records")
        print("-" * 80)
        print(f"{'TOTAL':40s} {total_records:>10,} records")
        print()
        
        # Save to JSON
        output_file = project_root / "data" / "target_record_counts.json"
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "target_directory": str(tenant_dir),
            "tenant_id": str(DEFAULT_TENANT_ID),
            "counts": counts,
            "total_records": total_records
        }
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"💾 Saved counts to: {output_file}")

if __name__ == "__main__":
    count_target_records()

