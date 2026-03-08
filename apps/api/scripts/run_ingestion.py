#!/usr/bin/env python3
"""Run ingestion pipeline for synthetic data"""
import sys
import json
from pathlib import Path
from uuid import UUID
from datetime import datetime, timezone

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "common" / "src"))

from uepi_api.storage_ingestions import create_ingestion, update_ingestion
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# Synthetic data directory (adjust path as needed)
SYNTH_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "demo"


def create_manifest_for_type(dataset_type: str, data_dir: Path) -> dict:
    """Create manifest for a dataset type"""
    manifest = {
        "dataset_type": dataset_type,
        "files": [],
        "source": "synthetic_data_generator",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if dataset_type == "CLAIMS_LINES":
        # Find all claims CSV files
        for csv_file in sorted(data_dir.glob("claims_lines_*.csv")):
            manifest["files"].append({
                "path": str(csv_file),
                "format": "csv",
                "size": csv_file.stat().st_size,
            })
    elif dataset_type == "ENROLLMENT":
        # Find enrollment CSV files
        for csv_file in sorted(data_dir.glob("enrollment_*.csv")):
            manifest["files"].append({
                "path": str(csv_file),
                "format": "csv",
                "size": csv_file.stat().st_size,
            })
    elif dataset_type == "PROVIDERS":
        # Find provider CSV file
        provider_file = data_dir / "providers.csv"
        if provider_file.exists():
            manifest["files"].append({
                "path": str(provider_file),
                "format": "csv",
                "size": provider_file.stat().st_size,
            })
    
    return manifest


def run_ingestion(dataset_type: str = "ALL"):
    """Run ingestion for synthetic data"""
    print(f"Running ingestion for dataset type: {dataset_type}")
    
    if not SYNTH_DATA_DIR.exists():
        print(f"❌ Synthetic data directory not found: {SYNTH_DATA_DIR}")
        print("   Please run the synthetic data generator first:")
        print("   python scripts/synth/generate.py --out data/demo")
        return
    
    types_to_ingest = []
    if dataset_type == "ALL":
        types_to_ingest = ["CLAIMS_LINES", "ENROLLMENT", "PROVIDERS"]
    else:
        types_to_ingest = [dataset_type]
    
    ingestion_type_map = {
        "CLAIMS_LINES": "CLAIMS",
        "ENROLLMENT": "ENROLLMENT",
        "PROVIDERS": "PROVIDERS",
    }
    
    for dt in types_to_ingest:
        print(f"\n📦 Processing {dt}...")
        
        # Create manifest
        manifest = create_manifest_for_type(dt, SYNTH_DATA_DIR)
        
        if not manifest["files"]:
            print(f"   ⚠️  No files found for {dt}")
            continue
        
        # Create ingestion record
        ingestion_data = {
            "ingestion_type": ingestion_type_map.get(dt, "CLAIMS"),
            "manifest_uri": f"file://{SYNTH_DATA_DIR}",
            "status": "PROCESSING",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "manifest": manifest,
                "file_count": len(manifest["files"]),
                "total_size": sum(f["size"] for f in manifest["files"]),
            },
        }
        
        ingestion = create_ingestion(DEFAULT_TENANT_ID, ingestion_data)
        print(f"   ✅ Created ingestion: {ingestion['id']}")
        print(f"      Files: {len(manifest['files'])}")
        print(f"      Total size: {sum(f['size'] for f in manifest['files']):,} bytes")
        
        # Simulate processing completion
        # In a real implementation, this would trigger the worker
        updated_data = {
            "status": "COMPLETED",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                **ingestion_data["metadata"],
                "records_processed": 1000,  # Placeholder
            },
        }
        
        update_ingestion(UUID(ingestion['id']), DEFAULT_TENANT_ID, updated_data)
        print(f"   ✅ Completed ingestion: {ingestion['id']}")
    
    print(f"\n✅ Ingestion complete!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run ingestion pipeline")
    parser.add_argument("--type", type=str, default="ALL", choices=["ALL", "CLAIMS_LINES", "ENROLLMENT", "PROVIDERS"],
                        help="Dataset type to ingest")
    args = parser.parse_args()
    
    run_ingestion(args.type)

