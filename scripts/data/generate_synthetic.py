#!/usr/bin/env python3
"""Runnable script to generate synthetic datasets - Phase 2 vertical slice"""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import polars as pl

from uepi_common.data_generator.generator import SyntheticDataGenerator
from uepi_common.data_generator.ground_truth import GroundTruthGenerator
from uepi_common.data_contracts.claims import ServiceCategory
from uepi_common.data_contracts.manifest import IngestionManifest, DatasetType, IngestionMode


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic UEPI datasets")
    parser.add_argument("--out", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--members", type=int, default=5000, help="Number of members")
    parser.add_argument("--providers", type=int, default=500, help="Number of providers")
    parser.add_argument("--months", type=int, default=12, help="Number of months of data")
    parser.add_argument("--tenant-id", type=str, default=None, help="Tenant ID (UUID)")
    
    args = parser.parse_args()
    
    # Set tenant ID
    tenant_id = UUID(args.tenant_id) if args.tenant_id else uuid4()
    
    # Create output directory
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔧 Generating synthetic data (seed={args.seed}, tenant={tenant_id})")
    print(f"📁 Output directory: {out_path}")
    print()
    
    # Initialize generator
    generator = SyntheticDataGenerator(seed=args.seed)
    
    # Define date range
    start_date = date(2024, 1, 1)
    end_date = start_date + timedelta(days=args.months * 30)
    
    # Define policy events for embedded behavioral patterns
    policy_events = [
        {
            "policy_id": "POL-PA-MRI",
            "effective_date": start_date + timedelta(days=180),  # 6 months in
            "service_category": ServiceCategory.IMAGING,
            "volume_multiplier": 0.75,  # 25% reduction
            "cost_multiplier": 1.0,
        },
        {
            "policy_id": "POL-SOC-INFUSION",
            "effective_date": start_date + timedelta(days=210),  # 7 months in
            "service_category": ServiceCategory.PROCEDURE,
            "volume_multiplier": 1.0,  # Volume stable
            "cost_multiplier": 0.85,  # 15% cost reduction
        },
        {
            "policy_id": "POL-LIMIT-PT",
            "effective_date": start_date + timedelta(days=240),  # 8 months in
            "service_category": ServiceCategory.REHAB,
            "volume_multiplier": 0.60,  # 40% reduction
            "cost_multiplier": 0.65,  # 35% cost reduction
        },
    ]
    
    # 1. Generate Enrollment
    print("📊 Generating enrollment data...")
    enrollment_records = generator.generate_enrollment(
        tenant_id,
        args.members,
        start_date,
        end_date,
    )
    print(f"   ✅ Generated {len(enrollment_records)} enrollment records")
    
    # Convert to DataFrame and save
    enrollment_df = pl.DataFrame([r.model_dump() for r in enrollment_records])
    enrollment_path = out_path / "enrollment.parquet"
    enrollment_df.write_parquet(enrollment_path)
    print(f"   💾 Saved to {enrollment_path}")
    print()
    
    # 2. Generate Providers
    print("🏥 Generating provider directory...")
    provider_records = generator.generate_providers(args.providers, start_date)
    print(f"   ✅ Generated {len(provider_records)} provider records")
    
    # Convert to DataFrame and save
    provider_df = pl.DataFrame([r.model_dump() for r in provider_records])
    provider_path = out_path / "providers.parquet"
    provider_df.write_parquet(provider_path)
    print(f"   💾 Saved to {provider_path}")
    print()
    
    # 3. Generate Claims Lines
    print("💰 Generating claims lines...")
    claims_records = generator.generate_claims_lines(
        tenant_id,
        enrollment_records,
        provider_records,
        start_date,
        end_date,
        policy_events=policy_events,
    )
    print(f"   ✅ Generated {len(claims_records)} claims lines")
    
    # Convert to DataFrame and save
    claims_df = pl.DataFrame([r.model_dump() for r in claims_records])
    claims_path = out_path / "claims_lines.parquet"
    claims_df.write_parquet(claims_path)
    print(f"   💾 Saved to {claims_path}")
    print()
    
    # 4. Generate Benefit Design
    print("📋 Generating benefit design...")
    benefit_records = generator.generate_benefit_design(start_date)
    print(f"   ✅ Generated {len(benefit_records)} benefit design records")
    
    # Convert to DataFrame and save
    benefit_df = pl.DataFrame([r.model_dump() for r in benefit_records])
    benefit_path = out_path / "benefit_design.parquet"
    benefit_df.write_parquet(benefit_path)
    print(f"   💾 Saved to {benefit_path}")
    print()
    
    # 5. Generate Ground Truth Outcomes
    print("🎯 Generating ground truth outcomes...")
    ground_truth = {}
    
    for event in policy_events:
        policy_id = event["policy_id"]
        
        # Determine policy type from ID
        if "PA" in policy_id:
            policy_type = "PRIOR_AUTH"
        elif "SOC" in policy_id:
            policy_type = "SITE_OF_CARE"
        elif "LIMIT" in policy_id:
            policy_type = "DURATION_FREQUENCY_LIMIT"
        else:
            policy_type = "UNKNOWN"
        
        outcomes = GroundTruthGenerator.generate_expected_outcomes(
            policy_id,
            policy_type,
            event["effective_date"],
            pre_window_months=6,
            post_window_months=6,
        )
        ground_truth[policy_id] = outcomes
    
    ground_truth_path = out_path / "ground_truth_expected_outcomes.json"
    with open(ground_truth_path, "w") as f:
        json.dump(ground_truth, f, indent=2, default=str)
    print(f"   ✅ Generated ground truth for {len(ground_truth)} policies")
    print(f"   💾 Saved to {ground_truth_path}")
    print()
    
    # 6. Generate Ingestion Manifest
    print("📦 Generating ingestion manifest...")
    manifest = IngestionManifest(
        tenant_id=tenant_id,
        dataset_type=DatasetType.CLAIMS_LINES,
        ingestion_mode=IngestionMode.MANUAL_UPLOAD,
        source_files=[
            {
                "uri": str(claims_path),
                "format": "Parquet",
                "record_count": len(claims_records),
            }
        ],
        data_start_date=start_date.isoformat(),
        data_end_date=end_date.isoformat(),
        lobs=["Commercial", "Medicare", "Medicaid"],
        markets=["CA", "TX", "NY", "FL", "IL"],
        schema_version="1.0",
        expected_record_count=len(claims_records),
        partition_by=["year", "month", "lob", "market"],
    )
    
    manifest_path = out_path / "ingestion_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest.model_dump(), f, indent=2, default=str)
    print(f"   ✅ Generated ingestion manifest")
    print(f"   💾 Saved to {manifest_path}")
    print()
    
    # Summary
    print("=" * 60)
    print("✅ Synthetic Data Generation Complete!")
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   • Enrollment records: {len(enrollment_records)}")
    print(f"   • Provider records: {len(provider_records)}")
    print(f"   • Claims lines: {len(claims_records)}")
    print(f"   • Benefit design records: {len(benefit_records)}")
    print(f"   • Ground truth policies: {len(ground_truth)}")
    print(f"   • Output directory: {out_path}")
    print()
    print("🧪 To validate, run: pytest packages/common/tests/test_synthetic_data.py")


if __name__ == "__main__":
    main()

