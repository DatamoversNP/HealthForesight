"""Provider segmentation module"""
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import boto3
import polars as pl
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from uepi_worker.config import get_settings
from uepi_worker.analytics import load_claims_data, get_s3_client

settings = get_settings()


def compute_provider_features(
    tenant_id: UUID,
    policy_effective_date: datetime,
    affected_codes: list[str],
    treatment_filters: dict[str, Any],
    pre_months: int = 6,
    post_months: int = 6,
) -> pl.DataFrame:
    """Compute provider-level features for segmentation"""
    # Load pre and post period data
    pre_start = policy_effective_date - timedelta(days=pre_months * 30)
    pre_end = policy_effective_date
    post_start = policy_effective_date
    post_end = policy_effective_date + timedelta(days=post_months * 30)
    
    # Load all claims
    all_filters = treatment_filters.copy()
    all_df = load_claims_data(tenant_id, all_filters, pre_start, post_end)
    
    if all_df.is_empty():
        return pl.DataFrame()
    
    # Parse dates
    all_df = all_df.with_columns(
        pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
    )
    
    # Filter to affected codes
    affected_df = all_df.filter(pl.col("cpt_hcpcs").is_in(affected_codes))
    
    # Split pre/post
    pre_df = affected_df.filter(
        (pl.col("service_date") >= pre_start.date()) & (pl.col("service_date") < pre_end.date())
    )
    post_df = affected_df.filter(
        (pl.col("service_date") >= post_start.date()) & (pl.col("service_date") < post_end.date())
    )
    
    # Compute provider-level metrics
    pre_provider = (
        pre_df.group_by("rendering_npi")
        .agg([
            pl.sum("allowed_amount").alias("pre_total_allowed"),
            pl.sum("units").alias("pre_total_units"),
            pl.count().alias("pre_claim_count"),
            pl.mean("allowed_amount").alias("pre_avg_allowed"),
            pl.col("place_of_service").mode().first().alias("pre_primary_pos"),
        ])
    )
    
    post_provider = (
        post_df.group_by("rendering_npi")
        .agg([
            pl.sum("allowed_amount").alias("post_total_allowed"),
            pl.sum("units").alias("post_total_units"),
            pl.count().alias("post_claim_count"),
            pl.mean("allowed_amount").alias("post_avg_allowed"),
            pl.col("place_of_service").mode().first().alias("post_primary_pos"),
        ])
    )
    
    # Join and compute deltas
    provider_features = (
        pre_provider.join(
            post_provider,
            on="rendering_npi",
            how="outer",
        )
        .with_columns([
            (pl.col("post_total_allowed").fill_null(0) - pl.col("pre_total_allowed").fill_null(0)).alias("allowed_delta"),
            (pl.col("post_claim_count").fill_null(0) - pl.col("pre_claim_count").fill_null(0)).alias("claim_count_delta"),
            ((pl.col("post_avg_allowed").fill_null(0) - pl.col("pre_avg_allowed").fill_null(0)) / 
             pl.col("pre_avg_allowed").fill_null(1) * 100).alias("avg_allowed_pct_change"),
            # POS shift indicator
            (pl.col("post_primary_pos") != pl.col("pre_primary_pos")).alias("pos_shift"),
        ])
        .filter(
            (pl.col("pre_claim_count").fill_null(0) > 0) | (pl.col("post_claim_count").fill_null(0) > 0)
        )
    )
    
    return provider_features


def segment_providers(
    provider_features: pl.DataFrame,
    n_clusters: int = 4,
) -> dict[str, Any]:
    """Segment providers using clustering"""
    if provider_features.is_empty() or len(provider_features) < n_clusters:
        return {
            "archetypes": [],
            "warnings": ["Insufficient data for provider segmentation"],
        }
    
    # Select features for clustering
    feature_cols = [
        "allowed_delta",
        "claim_count_delta",
        "avg_allowed_pct_change",
        "pos_shift",
    ]
    
    # Convert to numpy for sklearn
    X = provider_features.select(feature_cols).to_numpy()
    
    # Handle NaN values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Cluster
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Compute cluster characteristics
    provider_features = provider_features.with_columns([
        pl.Series("archetype", labels).alias("archetype"),
    ])
    
    archetypes = []
    for cluster_id in range(n_clusters):
        cluster_df = provider_features.filter(pl.col("archetype") == cluster_id)
        
        if cluster_df.is_empty():
            continue
        
        # Compute cluster statistics
        archetypes.append({
            "archetype_id": cluster_id,
            "archetype_label": _label_archetype(cluster_df),
            "provider_count": len(cluster_df),
            "avg_allowed_delta": float(cluster_df["allowed_delta"].mean()),
            "avg_claim_count_delta": float(cluster_df["claim_count_delta"].mean()),
            "avg_allowed_pct_change": float(cluster_df["avg_allowed_pct_change"].mean()),
            "pos_shift_rate": float(cluster_df["pos_shift"].mean()),
            "top_features": _get_top_features(cluster_df, feature_cols),
        })
    
    # Add provider assignments
    provider_assignments = []
    for row in provider_features.iter_rows(named=True):
        provider_assignments.append({
            "npi": row["rendering_npi"],
            "archetype_id": row["archetype"],
            "archetype_label": next(
                (a["archetype_label"] for a in archetypes if a["archetype_id"] == row["archetype"]),
                "UNKNOWN"
            ),
            "allowed_delta": row["allowed_delta"],
            "claim_count_delta": row["claim_count_delta"],
            "confidence_score": _compute_confidence_score(row),
        })
    
    return {
        "archetypes": archetypes,
        "provider_assignments": provider_assignments[:100],  # Top 100
        "total_providers": len(provider_features),
    }


def _label_archetype(cluster_df: pl.DataFrame) -> str:
    """Label archetype based on cluster characteristics"""
    avg_delta = cluster_df["allowed_delta"].mean()
    avg_claim_delta = cluster_df["claim_count_delta"].mean()
    pos_shift_rate = cluster_df["pos_shift"].mean()
    
    if avg_delta < -1000 and avg_claim_delta < -5:
        return "COMPLIERS"
    elif avg_delta > 1000 and pos_shift_rate > 0.5:
        return "CIRCUMVENTERS"
    elif avg_delta > 500:
        return "SUBSTITUTORS"
    else:
        return "NEUTRAL"


def _get_top_features(cluster_df: pl.DataFrame, feature_cols: list[str]) -> list[dict[str, Any]]:
    """Get top contributing features for cluster"""
    features = []
    for col in feature_cols:
        mean_val = cluster_df[col].mean()
        features.append({
            "feature": col,
            "mean_value": float(mean_val),
            "importance": abs(float(mean_val)),
        })
    
    features.sort(key=lambda x: x["importance"], reverse=True)
    return features[:3]


def _compute_confidence_score(row: dict[str, Any]) -> int:
    """Compute confidence score for provider assignment"""
    score = 50  # Base
    
    if abs(row["allowed_delta"]) > 1000:
        score += 20
    if abs(row["claim_count_delta"]) > 10:
        score += 20
    if row.get("pos_shift", False):
        score += 10
    
    return min(100, score)


def run_provider_segmentation(
    tenant_id: UUID,
    analysis_id: UUID,
    policy_id: UUID,
    policy_effective_date: datetime,
    treatment_filters: dict[str, Any],
    pre_months: int = 6,
    post_months: int = 6,
) -> dict[str, Any]:
    """Run complete provider segmentation analysis"""
    # Get affected codes from policy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from uepi_api.models.policy import PolicyCodeSet, PolicyVersion
    
    engine = create_engine(settings.database.url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get latest policy version
        version = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.tenant_id == tenant_id,
        ).order_by(PolicyVersion.version_number.desc()).first()
        
        if not version:
            return {
                "archetypes": [],
                "provider_assignments": [],
                "warnings": ["Policy version not found"],
            }
        
        # Get code sets for this version
        code_sets = db.query(PolicyCodeSet).filter(
            PolicyCodeSet.version_id == version.id,
            PolicyCodeSet.tenant_id == tenant_id,
        ).all()
        
        affected_codes = [cs.code for cs in code_sets]
    finally:
        db.close()
    
    # Compute provider features
    provider_features = compute_provider_features(
        tenant_id,
        policy_effective_date,
        affected_codes,
        treatment_filters,
        pre_months,
        post_months,
    )
    
    if provider_features.is_empty():
        return {
            "archetypes": [],
            "provider_assignments": [],
            "warnings": ["No provider data available"],
        }
    
    # Segment providers
    result = segment_providers(provider_features, n_clusters=4)
    
    # Add metadata
    result["policy_id"] = str(policy_id)
    result["analysis_id"] = str(analysis_id)
    result["affected_codes"] = affected_codes
    
    return result

