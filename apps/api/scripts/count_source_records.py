#!/usr/bin/env python3
"""
Count source records before pipeline runs
Counts records in all source data files
"""
import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

SOURCE_DATA_DIR = project_root / "data" / "source_data" / "synthetic"

def count_file_records(file_path: Path) -> int:
    """Count records in a file (CSV or Parquet)"""
    try:
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path, nrows=0)  # Just get schema
            # Count lines (subtract header)
            with open(file_path, 'r') as f:
                return sum(1 for _ in f) - 1
        elif file_path.suffix == '.parquet':
            df = pd.read_parquet(file_path)
            return len(df)
        else:
            return 0
    except Exception as e:
        print(f"  ⚠️  Error counting {file_path.name}: {e}")
        return 0

def count_source_records():
    """Count all source records"""
    print("=" * 80)
    print("SOURCE DATA RECORD COUNTS")
    print("=" * 80)
    print(f"Source Directory: {SOURCE_DATA_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    if not SOURCE_DATA_DIR.exists():
        print(f"❌ Source directory not found: {SOURCE_DATA_DIR}")
        return
    
    counts = {}
    total_records = 0
    
    # Count main dataset files
    print("📊 Counting main dataset files...")
    main_files = list(SOURCE_DATA_DIR.glob("*.csv")) + list(SOURCE_DATA_DIR.glob("*.parquet"))
    for file_path in sorted(main_files):
        if file_path.name.startswith('claims_'):
            continue  # Skip claims files (handled separately)
        count = count_file_records(file_path)
        dataset_name = file_path.stem
        counts[dataset_name] = count
        total_records += count
        print(f"  {dataset_name:40s} {count:>10,} records")
    
    # Count claims files by year/month
    print()
    print("📊 Counting claims files by year/month...")
    claims_dir = SOURCE_DATA_DIR / "claims"
    if claims_dir.exists():
        claims_total = 0
        for year_dir in sorted(claims_dir.iterdir()):
            if not year_dir.is_dir():
                continue
            year = year_dir.name
            year_total = 0
            for month_file in sorted(year_dir.glob("*.csv")) + sorted(year_dir.glob("*.parquet")):
                count = count_file_records(month_file)
                month = month_file.stem.replace(f"claims_{year}_", "")
                year_total += count
                claims_total += count
                print(f"    {year}/{month:2s} {count:>10,} records")
            if year_total > 0:
                print(f"  {year} Total: {year_total:>10,} records")
        counts['claims_lines'] = claims_total
        total_records += claims_total
        print(f"  Claims Total: {claims_total:>10,} records")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for dataset, count in sorted(counts.items()):
        print(f"{dataset:40s} {count:>10,} records")
    print("-" * 80)
    print(f"{'TOTAL':40s} {total_records:>10,} records")
    print()
    
    # Save to JSON
    output_file = project_root / "data" / "source_record_counts.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "source_directory": str(SOURCE_DATA_DIR),
        "counts": counts,
        "total_records": total_records
    }
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"💾 Saved counts to: {output_file}")

if __name__ == "__main__":
    count_source_records()

