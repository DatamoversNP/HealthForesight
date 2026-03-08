#!/usr/bin/env python3
"""
Example: Using HealthcareDataModel for Analytics and ML
Shows how to load data and perform common analytical tasks
"""
from pathlib import Path
from datetime import date
import polars as pl
from uepi_common.data.data_model import create_data_model

# Initialize data model (local file storage)
data_dir = Path("data/synthetic")
data_model = create_data_model(storage_path=data_dir)

# ========================================================================
# Example 1: Load claims and get summary
# ========================================================================
print("Example 1: Claims Summary")
print("-" * 50)

claims_summary = data_model.get_claims_summary(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    group_by=["lob", "service_category"],
)

print(claims_summary.head(10))
print()

# ========================================================================
# Example 2: Utilization timeseries
# ========================================================================
print("Example 2: Utilization Timeseries")
print("-" * 50)

timeseries = data_model.get_utilization_timeseries(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    group_by="service_category",
    frequency="month",
)

print(timeseries.head(20))
print()

# ========================================================================
# Example 3: Provider performance
# ========================================================================
print("Example 3: Provider Performance")
print("-" * 50)

# Get top providers by volume
claims = data_model.load_claims(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
)

if not claims.is_empty():
    provider_perf = data_model.get_provider_performance(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )
    
    # Sort by total allowed
    top_providers = provider_perf.sort("total_allowed", descending=True).head(10)
    print(top_providers)
    print()

# ========================================================================
# Example 4: Cohort analysis
# ========================================================================
print("Example 4: Cohort Members")
print("-" * 50)

cohort = data_model.get_cohort_members(
    filters={
        "lob": "COMMERCIAL",
        "age_band": "50-64",
        "market": "NYC",
    },
    enrollment_month="2024-01",
)

print(f"Cohort size: {len(cohort)} members")
print(cohort.head(10))
print()

# ========================================================================
# Example 5: ML Features
# ========================================================================
print("Example 5: ML Features")
print("-" * 50)

ml_features = data_model.get_features_for_ml(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 3, 31),
    target_variable="allowed_amount",
)

print(f"Features shape: {ml_features.shape}")
print(f"Feature columns: {list(ml_features.columns[:10])}")
print()

# ========================================================================
# Example 6: Custom query with Polars
# ========================================================================
print("Example 6: Custom Polars Query")
print("-" * 50)

claims = data_model.load_claims(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    service_category="MRI",
    lob="COMMERCIAL",
)

if not claims.is_empty():
    # Custom aggregation
    result = claims.with_columns(
        pl.col("service_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date_parsed")
    ).group_by(
        ["market", "place_of_service"]
    ).agg([
        pl.count().alias("claim_count"),
        pl.mean("allowed_amount").alias("avg_allowed"),
        pl.sum("allowed_amount").alias("total_allowed"),
    ]).sort("total_allowed", descending=True)
    
    print(result)
    print()

print("✅ Examples complete!")

