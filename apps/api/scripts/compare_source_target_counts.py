#!/usr/bin/env python3
"""
Compare source and target record counts
Shows before/after pipeline execution
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

SOURCE_COUNTS_FILE = project_root / "data" / "source_record_counts.json"
TARGET_COUNTS_FILE = project_root / "data" / "target_record_counts.json"

def compare_counts():
    """Compare source and target record counts"""
    print("=" * 80)
    print("SOURCE vs TARGET RECORD COUNT COMPARISON")
    print("=" * 80)
    print()
    
    # Load source counts
    source_counts = {}
    if SOURCE_COUNTS_FILE.exists():
        with open(SOURCE_COUNTS_FILE, 'r') as f:
            source_data = json.load(f)
            source_counts = source_data.get("counts", {})
            print(f"📊 Source Data Timestamp: {source_data.get('timestamp', 'Unknown')}")
    else:
        print("⚠️  Source counts file not found. Run count_source_records.py first.")
        print()
    
    # Load target counts
    target_counts = {}
    if TARGET_COUNTS_FILE.exists():
        with open(TARGET_COUNTS_FILE, 'r') as f:
            target_data = json.load(f)
            target_counts = target_data.get("counts", {})
            print(f"📊 Target Data Timestamp: {target_data.get('timestamp', 'Unknown')}")
    else:
        print("⚠️  Target counts file not found. Run count_target_records.py first.")
        print()
    
    if not source_counts and not target_counts:
        print("❌ No count data available. Run count_source_records.py and count_target_records.py first.")
        return
    
    print()
    print("=" * 80)
    print("RECORD COUNT COMPARISON")
    print("=" * 80)
    print(f"{'Dataset':<40} {'Source':>12} {'Target':>12} {'Difference':>12} {'Status':>10}")
    print("-" * 80)
    
    all_datasets = set(source_counts.keys()) | set(target_counts.keys())
    total_source = 0
    total_target = 0
    
    for dataset in sorted(all_datasets):
        source_count = source_counts.get(dataset, 0)
        target_count = target_counts.get(dataset, 0)
        diff = target_count - source_count
        total_source += source_count
        total_target += target_count
        
        if source_count == 0:
            status = "N/A"
        elif target_count == 0:
            status = "⚠️  Not Run"
        elif diff == 0:
            status = "✅ Match"
        elif diff < 0:
            status = "⚠️  Less"
        else:
            status = "ℹ️  More"
        
        print(f"{dataset:<40} {source_count:>12,} {target_count:>12,} {diff:>+12,} {status:>10}")
    
    print("-" * 80)
    total_diff = total_target - total_source
    print(f"{'TOTAL':<40} {total_source:>12,} {total_target:>12,} {total_diff:>+12,}")
    print()
    
    # Deduplication analysis
    if total_source > 0 and total_target > 0:
        dedup_rate = ((total_source - total_target) / total_source * 100) if total_source > total_target else 0
        print("=" * 80)
        print("DEDUPLICATION ANALYSIS")
        print("=" * 80)
        if total_target < total_source:
            print(f"📉 Duplicates Removed: {total_source - total_target:,} records")
            print(f"📊 Deduplication Rate: {dedup_rate:.2f}%")
            print(f"✅ Pipelines successfully handled duplicate records")
        elif total_target == total_source:
            print(f"✅ No duplicates found - all source records ingested")
        else:
            print(f"ℹ️  Target has more records than source (may be from multiple runs)")
        print()

if __name__ == "__main__":
    compare_counts()

