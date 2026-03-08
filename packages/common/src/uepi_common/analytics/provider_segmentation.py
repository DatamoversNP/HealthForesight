"""Provider segmentation - clustering + archetypes + explainers"""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

import numpy as np
import polars as pl
# Make sklearn optional - import only when needed
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    KMeans = None
    StandardScaler = None
    silhouette_score = None

from uepi_common.data.parquet_service import ParquetDataService


class ProviderArchetype:
    """Provider archetype from clustering"""
    
    def __init__(
        self,
        archetype_id: int,
        archetype_label: str,
        provider_count: int,
        avg_allowed_delta: float,
        avg_claim_count_delta: float,
        avg_allowed_pct_change: float,
        pos_shift_rate: float,
        top_features: list[dict[str, Any]],
        stability_score: float,
    ):
        """Initialize provider archetype"""
        self.archetype_id = archetype_id
        self.archetype_label = archetype_label
        self.provider_count = provider_count
        self.avg_allowed_delta = avg_allowed_delta
        self.avg_claim_count_delta = avg_claim_count_delta
        self.avg_allowed_pct_change = avg_allowed_pct_change
        self.pos_shift_rate = pos_shift_rate
        self.top_features = top_features
        self.stability_score = stability_score
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "archetype_id": self.archetype_id,
            "archetype_label": self.archetype_label,
            "provider_count": self.provider_count,
            "avg_allowed_delta": self.avg_allowed_delta,
            "avg_claim_count_delta": self.avg_claim_count_delta,
            "avg_allowed_pct_change": self.avg_allowed_pct_change,
            "pos_shift_rate": self.pos_shift_rate,
            "top_features": self.top_features,
            "stability_score": self.stability_score,
        }


class ProviderSegmentation:
    """Provider segmentation engine"""
    
    def __init__(
        self,
        tenant_id: UUID,
        parquet_service: Optional[ParquetDataService] = None,
    ):
        """Initialize provider segmentation engine"""
        self.tenant_id = tenant_id
        self.parquet_service = parquet_service or ParquetDataService()
    
    def segment_providers(
        self,
        policy_effective_date: datetime,
        affected_codes: list[str],
        treatment_filters: dict[str, Any],
        pre_months: int = 6,
        post_months: int = 6,
        n_clusters: int = 4,
    ) -> dict[str, Any]:
        """Segment providers using clustering
        
        Args:
            policy_effective_date: Policy effective date
            affected_codes: List of affected CPT/HCPCS codes
            treatment_filters: Treatment group filters
            pre_months: Pre-policy window in months
            post_months: Post-policy window in months
            n_clusters: Number of clusters (archetypes)
            
        Returns:
            Dictionary with archetypes, provider assignments, and diagnostics
        """
        # Import ImpactAnalysisEngine for data loading
        from uepi_common.analytics.impact import ImpactAnalysisEngine
        
        # Load data
        impact_engine = ImpactAnalysisEngine(tenant_id=self.tenant_id, parquet_service=self.parquet_service)
        
        pre_start = policy_effective_date - timedelta(days=pre_months * 30)
        pre_end = policy_effective_date
        post_start = policy_effective_date
        post_end = policy_effective_date + timedelta(days=post_months * 30)
        
        pre_df = impact_engine._load_data(pre_start, pre_end, treatment_filters, None)
        post_df = impact_engine._load_data(post_start, post_end, treatment_filters, None)
        
        if pre_df.is_empty() or post_df.is_empty():
            return {
                "archetypes": [],
                "provider_assignments": [],
                "total_providers": 0,
                "warnings": ["No data available for provider segmentation"],
            }
        
        # Filter to affected codes
        affected_pre_df = pre_df.filter(pl.col("cpt_code").is_in(affected_codes))
        affected_post_df = post_df.filter(pl.col("cpt_code").is_in(affected_codes))
        
        # Compute provider-level features
        provider_features = self._compute_provider_features(
            affected_pre_df, affected_post_df
        )
        
        if provider_features.is_empty() or len(provider_features) < n_clusters:
            return {
                "archetypes": [],
                "provider_assignments": [],
                "total_providers": len(provider_features),
                "warnings": ["Insufficient provider data for segmentation"],
            }
        
        # Perform clustering
        archetypes, provider_assignments = self._cluster_providers(
            provider_features, n_clusters
        )
        
        return {
            "archetypes": [a.to_dict() for a in archetypes],
            "provider_assignments": provider_assignments[:100],  # Top 100
            "total_providers": len(provider_features),
            "clustering_quality": self._assess_clustering_quality(
                provider_features, n_clusters
            ),
        }
    
    def _compute_provider_features(
        self,
        pre_df: pl.DataFrame,
        post_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """Compute provider-level response features"""
        # Compute pre-period metrics per provider
        # Use provider_id (from ClaimsLine contract) or rendering_provider_id if available
        provider_col = "provider_id"
        if "rendering_provider_id" in pre_df.columns and pre_df["rendering_provider_id"].null_count() < len(pre_df) * 0.5:
            provider_col = "rendering_provider_id"
        
        pre_provider = (
            pre_df.group_by(provider_col)
            .agg([
                pl.sum("allowed_amount").alias("pre_total_allowed"),
                pl.sum("units").alias("pre_total_units"),
                pl.count().alias("pre_claim_count"),
                pl.mean("allowed_amount").alias("pre_avg_allowed"),
                pl.col("place_of_service").mode().first().alias("pre_primary_pos"),
                pl.n_unique("member_id").alias("pre_member_count"),
            ])
            .rename({provider_col: "provider_id"})
        )
        
        # Compute post-period metrics per provider
        post_provider = (
            post_df.group_by(provider_col)
            .agg([
                pl.sum("allowed_amount").alias("post_total_allowed"),
                pl.sum("units").alias("post_total_units"),
                pl.count().alias("post_claim_count"),
                pl.mean("allowed_amount").alias("post_avg_allowed"),
                pl.col("place_of_service").mode().first().alias("post_primary_pos"),
                pl.n_unique("member_id").alias("post_member_count"),
            ])
            .rename({provider_col: "provider_id"})
        )
        
        # Join and compute deltas
        provider_features = (
            pre_provider.join(
                post_provider,
                on="provider_id",
                how="outer",
            )
            .with_columns([
                # Fill nulls with 0 for calculations
                pl.col("pre_total_allowed").fill_null(0),
                pl.col("post_total_allowed").fill_null(0),
                pl.col("pre_claim_count").fill_null(0),
                pl.col("post_claim_count").fill_null(0),
                pl.col("pre_avg_allowed").fill_null(0),
                pl.col("post_avg_allowed").fill_null(0),
            ])
            .with_columns([
                (pl.col("post_total_allowed") - pl.col("pre_total_allowed")).alias("allowed_delta"),
                (pl.col("post_claim_count") - pl.col("pre_claim_count")).alias("claim_count_delta"),
                ((pl.col("post_avg_allowed") - pl.col("pre_avg_allowed")) / 
                 pl.col("pre_avg_allowed").fill_null(1) * 100).alias("avg_allowed_pct_change"),
                # POS shift indicator (1 if changed, 0 if same)
                (pl.col("post_primary_pos") != pl.col("pre_primary_pos")).cast(pl.Int64).alias("pos_shift"),
                # Member count change
                ((pl.col("post_member_count").fill_null(0) - pl.col("pre_member_count").fill_null(0))).alias("member_count_delta"),
            ])
            .filter(
                (pl.col("pre_claim_count") > 0) | (pl.col("post_claim_count") > 0)
            )
        )
        
        return provider_features
    
    def _cluster_providers(
        self,
        provider_features: pl.DataFrame,
        n_clusters: int,
    ) -> tuple[list[ProviderArchetype], list[dict[str, Any]]]:
        """Perform K-means clustering on provider features"""
        # Select features for clustering
        feature_cols = [
            "allowed_delta",
            "claim_count_delta",
            "avg_allowed_pct_change",
            "pos_shift",
            "member_count_delta",
        ]
        
        # Convert to numpy
        X = provider_features.select(feature_cols).to_numpy()
        
        # Handle NaN/Inf values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        
        # Add cluster labels to dataframe
        provider_features = provider_features.with_columns([
            pl.Series("archetype_id", labels).alias("archetype_id"),
        ])
        
        # Build archetypes
        archetypes = []
        for cluster_id in range(n_clusters):
            cluster_df = provider_features.filter(pl.col("archetype_id") == cluster_id)
            
            if cluster_df.is_empty():
                continue
            
            # Compute cluster statistics
            archetype_label = self._label_archetype(cluster_df)
            top_features = self._get_top_features(cluster_df, feature_cols)
            stability_score = self._compute_stability_score(cluster_df, feature_cols)
            
            archetypes.append(ProviderArchetype(
                archetype_id=cluster_id,
                archetype_label=archetype_label,
                provider_count=len(cluster_df),
                avg_allowed_delta=float(cluster_df["allowed_delta"].mean()),
                avg_claim_count_delta=float(cluster_df["claim_count_delta"].mean()),
                avg_allowed_pct_change=float(cluster_df["avg_allowed_pct_change"].mean()),
                pos_shift_rate=float(cluster_df["pos_shift"].mean()),
                top_features=top_features,
                stability_score=stability_score,
            ))
        
        # Build provider assignments
        provider_assignments = []
        for row in provider_features.iter_rows(named=True):
            archetype_label = next(
                (a.archetype_label for a in archetypes if a.archetype_id == row["archetype_id"]),
                "UNKNOWN"
            )
            
            confidence_score = self._compute_provider_confidence(row)
            
            provider_assignments.append({
                "provider_id": row["provider_id"],
                "archetype_id": row["archetype_id"],
                "archetype_label": archetype_label,
                "allowed_delta": float(row["allowed_delta"]),
                "claim_count_delta": int(row["claim_count_delta"]),
                "avg_allowed_pct_change": float(row["avg_allowed_pct_change"]),
                "pos_shift": bool(row["pos_shift"]),
                "confidence_score": confidence_score,
            })
        
        # Sort assignments by confidence and magnitude
        provider_assignments.sort(
            key=lambda x: (x["confidence_score"], abs(x["allowed_delta"])),
            reverse=True
        )
        
        return archetypes, provider_assignments
    
    def _label_archetype(self, cluster_df: pl.DataFrame) -> str:
        """Label archetype based on cluster characteristics"""
        avg_delta = cluster_df["allowed_delta"].mean()
        avg_claim_delta = cluster_df["claim_count_delta"].mean()
        pos_shift_rate = cluster_df["pos_shift"].mean()
        avg_pct_change = cluster_df["avg_allowed_pct_change"].mean()
        
        # Rule-based labeling
        if avg_delta < -1000 and avg_claim_delta < -5:
            return "COMPLIERS"  # Significant reduction
        elif avg_delta > 1000 and pos_shift_rate > 0.5:
            return "CIRCUMVENTERS"  # High increase + site shift
        elif avg_delta > 500 and avg_pct_change > 50:
            return "SUBSTITUTORS"  # Significant substitution
        elif avg_delta < -100 and avg_claim_delta < 0:
            return "REDUCERS"  # Modest reduction
        elif avg_delta > 100:
            return "INCREASERS"  # Modest increase
        else:
            return "NEUTRAL"  # No significant change
    
    def _get_top_features(
        self,
        cluster_df: pl.DataFrame,
        feature_cols: list[str],
    ) -> list[dict[str, Any]]:
        """Get top contributing features for cluster"""
        features = []
        for col in feature_cols:
            mean_val = float(cluster_df[col].mean())
            std_val = float(cluster_df[col].std()) if len(cluster_df) > 1 else 0.0
            
            features.append({
                "feature": col,
                "mean_value": mean_val,
                "std_value": std_val,
                "importance": abs(mean_val),
            })
        
        features.sort(key=lambda x: x["importance"], reverse=True)
        return features[:3]
    
    def _compute_stability_score(self, cluster_df: pl.DataFrame, feature_cols: list[str]) -> float:
        """Compute cluster stability score (0-1) based on feature variance"""
        if len(cluster_df) <= 1:
            return 0.0
        
        # Lower variance = higher stability
        variances = []
        for col in feature_cols:
            var = float(cluster_df[col].var())
            variances.append(var)
        
        avg_variance = np.mean(variances)
        # Normalize to 0-1 scale (heuristic)
        stability = max(0.0, min(1.0, 1.0 / (1.0 + avg_variance / 1000.0)))
        
        return stability
    
    def _compute_provider_confidence(self, row: dict[str, Any]) -> int:
        """Compute confidence score for provider assignment (0-100)"""
        score = 50  # Base
        
        if abs(row["allowed_delta"]) > 1000:
            score += 20
        if abs(row["claim_count_delta"]) > 10:
            score += 20
        if row.get("pos_shift", False):
            score += 10
        if abs(row["avg_allowed_pct_change"]) > 50:
            score += 10
        
        return min(100, score)
    
    def _assess_clustering_quality(
        self,
        provider_features: pl.DataFrame,
        n_clusters: int,
    ) -> dict[str, Any]:
        """Assess clustering quality using silhouette score"""
        feature_cols = [
            "allowed_delta",
            "claim_count_delta",
            "avg_allowed_pct_change",
            "pos_shift",
            "member_count_delta",
        ]
        
        X = provider_features.select(feature_cols).to_numpy()
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        labels = provider_features["archetype_id"].to_list()
        
        if len(set(labels)) < 2:
            return {
                "silhouette_score": 0.0,
                "quality": "POOR",
                "recommendation": "Not enough distinct clusters",
            }
        
        try:
            silhouette_avg = silhouette_score(X_scaled, labels)
            
            if silhouette_avg > 0.5:
                quality = "GOOD"
            elif silhouette_avg > 0.3:
                quality = "FAIR"
            else:
                quality = "POOR"
            
            return {
                "silhouette_score": float(silhouette_avg),
                "quality": quality,
                "recommendation": f"Clustering quality: {quality} (silhouette={silhouette_avg:.3f})",
            }
        except Exception:
            return {
                "silhouette_score": 0.0,
                "quality": "UNKNOWN",
                "recommendation": "Unable to compute clustering quality",
            }

