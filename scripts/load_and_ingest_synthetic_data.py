#!/usr/bin/env python3
"""
Load synthetic data and ingest into platform
This script generates synthetic data and loads it via the ingestion pipeline
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from scripts.generate_synthetic_datasets import main as generate_main
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_common.ingestion.flexible_processor import FlexibleIngestionProcessor
from uepi_common.data_contracts.manifest import DatasetType


def ingest_synthetic_data(data_dir: Path, tenant_id: UUID):
    """Ingest generated synthetic data into the platform"""
    print(f"\n📥 Ingesting synthetic data from {data_dir}...")
    
    # 1. Ingest enrollment
    print("\n1. Ingesting enrollment data...")
    enrollment_file = data_dir / "enrollment_monthly.csv"
    if enrollment_file.exists():
        processor = FlexibleIngestionProcessor(tenant_id, DatasetType.ENROLLMENT)
        result = processor.process_file(str(enrollment_file), auto_detect_schema=True)
        print(f"   ✅ Enrollment: {result['records_valid']} valid records")
    else:
        print(f"   ⚠️  Enrollment file not found: {enrollment_file}")
    
    # 2. Ingest providers
    print("\n2. Ingesting provider directory...")
    providers_file = data_dir / "providers.csv"
    if providers_file.exists():
        processor = FlexibleIngestionProcessor(tenant_id, DatasetType.PROVIDERS)
        result = processor.process_file(str(providers_file), auto_detect_schema=True)
        print(f"   ✅ Providers: {result['records_valid']} valid records")
    else:
        print(f"   ⚠️  Providers file not found: {providers_file}")
    
    # 3. Ingest claims (partitioned by month)
    print("\n3. Ingesting claims data...")
    claims_dir = data_dir / "claims"
    if claims_dir.exists():
        total_claims = 0
        for year_dir in sorted(claims_dir.iterdir()):
            if not year_dir.is_dir():
                continue
            
            for month_file in sorted(year_dir.glob("*.parquet")):
                # Convert parquet to CSV for ingestion (or enhance processor to handle parquet)
                # For now, convert
                import pandas as pd
                df = pd.read_parquet(month_file)
                csv_file = month_file.with_suffix(".csv")
                df.to_csv(csv_file, index=False)
                
                processor = FlexibleIngestionProcessor(tenant_id, DatasetType.CLAIMS_LINES)
                result = processor.process_file(str(csv_file), auto_detect_schema=True)
                total_claims += result.get("records_valid", 0)
                print(f"   ✅ {month_file.name}: {result.get('records_valid', 0)} claims")
        
        print(f"   ✅ Total claims ingested: {total_claims:,}")
    else:
        print(f"   ⚠️  Claims directory not found: {claims_dir}")
    
    print("\n✅ Synthetic data ingestion complete!")


def main():
    parser = argparse.ArgumentParser(description="Generate and ingest synthetic healthcare data")
    parser.add_argument("--data-dir", type=str, default="data/synthetic", help="Data directory")
    parser.add_argument("--generate-only", action="store_true", help="Only generate, don't ingest")
    parser.add_argument("--ingest-only", action="store_true", help="Only ingest, don't generate")
    parser.add_argument("--members", type=int, default=100000, help="Number of members")
    parser.add_argument("--providers", type=int, default=10000, help="Number of providers")
    parser.add_argument("--months", type=int, default=36, help="Number of months")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    
    # Generate synthetic data
    if not args.ingest_only:
        print("📊 Generating synthetic datasets...")
        # Modify generate script to accept args
        import sys
        sys.argv = [
            "generate_synthetic_datasets.py",
            "--out", str(data_dir),
            "--members", str(args.members),
            "--providers", str(args.providers),
            "--months", str(args.months),
        ]
        generate_main()
    
    # Ingest into platform
    if not args.generate_only:
        ingest_synthetic_data(data_dir, DEFAULT_TENANT_ID)


if __name__ == "__main__":
    main()

