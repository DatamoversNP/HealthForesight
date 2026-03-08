#!/usr/bin/env python3
"""Script to check analysis files and recreate observations with proper data extraction"""

import sys
import json
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def check_analysis_file(analysis_file: Path):
    """Check if analysis file has treatment_post data"""
    try:
        with open(analysis_file) as f:
            data = json.load(f)
        
        has_metrics = "metrics" in data
        has_treatment_post = False
        treatment_post_data = None
        
        if has_metrics:
            metrics = data.get("metrics", {})
            has_treatment_post = "treatment_post" in metrics
            if has_treatment_post:
                treatment_post_data = metrics["treatment_post"]
        
        # Also check for alternative structures
        has_post_period = "post_period" in data
        has_impact_estimate = "impact_estimate" in data or "did_result" in data
        
        return {
            "file": analysis_file.name,
            "has_metrics": has_metrics,
            "has_treatment_post": has_treatment_post,
            "treatment_post": treatment_post_data,
            "has_post_period": has_post_period,
            "has_impact_estimate": has_impact_estimate,
            "keys": list(data.keys())[:15],
            "metrics_keys": list(data.get("metrics", {}).keys()) if has_metrics else [],
        }
    except Exception as e:
        return {
            "file": analysis_file.name,
            "error": str(e)
        }


def main():
    print("="*80)
    print("ANALYSIS FILES CHECK")
    print("="*80)
    
    analyses_dir = project_root / "apps" / "api" / "src" / "data" / "analyses"
    if not analyses_dir.exists():
        print(f"❌ Analyses directory not found: {analyses_dir}")
        return
    
    analysis_files = list(analyses_dir.glob("*.json"))
    print(f"Found {len(analysis_files)} analysis files\n")
    
    analyses_with_data = []
    analyses_without_data = []
    
    for analysis_file in analysis_files[:10]:  # Check first 10
        result = check_analysis_file(analysis_file)
        
        print(f"File: {result['file']}")
        if "error" in result:
            print(f"  ❌ Error: {result['error']}\n")
            continue
        
        if result.get("has_treatment_post"):
            tp = result.get("treatment_post", {})
            print(f"  ✅ Has treatment_post data:")
            print(f"     Utilization: {tp.get('utilization_per_1k', 'N/A')}")
            print(f"     Cost PMPM: {tp.get('allowed_pmpm', tp.get('paid_pmpm', 'N/A'))}")
            print(f"     Total Claims: {tp.get('total_claims', 'N/A')}")
            analyses_with_data.append(result)
        else:
            print(f"  ❌ No treatment_post data")
            print(f"     Has metrics: {result.get('has_metrics')}")
            print(f"     Metrics keys: {result.get('metrics_keys', [])}")
            print(f"     Top-level keys: {result.get('keys', [])}")
            analyses_without_data.append(result)
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Analyses with treatment_post data: {len(analyses_with_data)}")
    print(f"Analyses without treatment_post data: {len(analyses_with_data)}")
    
    if analyses_with_data:
        print("\n✅ Some analyses have data - observations can be created from these")
        print("   Next step: Start API and create observations from these analyses")
    else:
        print("\n❌ No analyses have treatment_post data")
        print("   Next step: Run impact analyses with actual claims data")
        print("   The analyses need to load claims and compute treatment_post metrics")


if __name__ == "__main__":
    main()
