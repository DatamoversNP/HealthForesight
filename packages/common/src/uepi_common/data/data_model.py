"""
Simple Data Model Layer for Analytics & ML
Provides clean, simple interface to load and query healthcare data
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pathlib import Path
import polars as pl
import pandas as pd

from uepi_common.storage.interface import BlobStorageClient
from uepi_common.storage.factory import create_storage_client
from uepi_common.data_contracts.claims import ClaimsLine
from uepi_common.data_contracts.enrollment import EnrollmentRecord
from uepi_common.data_contracts.providers import ProviderRecord


class HealthcareDataModel:
    """
    Simple data model for analytics and ML
    
    Provides easy access to:
    - Claims lines (time-series, filtered, aggregated)
    - Member enrollment (cohorts, demographics)
    - Provider directory (network, specialties)
    - Policy events (timeline, impacts)
    """
    
    def __init__(
        self,
        storage_client: Optional[BlobStorageClient] = None,
        storage_path: Optional[Path] = None,
        tenant_id: Optional[UUID] = None,
    ):
        """
        Initialize data model
        
        Args:
            storage_client: BlobStorageClient (optional - for cloud storage)
            storage_path: Local path (optional - for file-based storage)
            tenant_id: Tenant ID for multi-tenancy
        """
        self.storage_client = storage_client
        self.storage_path = Path(storage_path) if storage_path else None
        self.tenant_id = tenant_id
        
        # Cache for loaded data
        self._claims_cache: Dict[str, pl.DataFrame] = {}
        self._enrollment_cache: Optional[pl.DataFrame] = None
        self._providers_cache: Optional[pl.DataFrame] = None
    
    # ========================================================================
    # CLAIMS LINES - Primary analytical dataset
    # ========================================================================
    
    def load_claims(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lob: Optional[str] = None,
        market: Optional[str] = None,
        service_category: Optional[str] = None,
        cpt_code: Optional[str] = None,
        in_network_only: bool = False,
        force_reload: bool = False,
    ) -> pl.DataFrame:
        """
        Load claims lines with optional filters
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            lob: Line of business filter
            market: Market filter
            service_category: Service category filter
            cpt_code: CPT code filter
            in_network_only: Filter to in-network only
            force_reload: Force reload from storage (ignore cache)
            
        Returns:
            Polars DataFrame with claims lines
        """
        cache_key = f"{start_date}_{end_date}_{lob}_{market}_{service_category}_{cpt_code}_{in_network_only}"
        
        if not force_reload and cache_key in self._claims_cache:
            return self._claims_cache[cache_key]
        
        # Load from file storage or object storage
        if self.storage_path:
            df = self._load_claims_from_local(start_date, end_date)
        else:
            df = self._load_claims_from_storage(start_date, end_date)
        
        # Apply filters
        if lob:
            df = df.filter(pl.col("lob") == lob)
        
        if market:
            df = df.filter(pl.col("market") == market)
        
        if service_category:
            df = df.filter(pl.col("service_category") == service_category)
        
        if cpt_code:
            df = df.filter(pl.col("cpt_code") == cpt_code)
        
        if in_network_only:
            df = df.filter(pl.col("in_network") == True)
        
        # Cache result
        self._claims_cache[cache_key] = df
        
        return df
    
    def _load_claims_from_local(self, start_date: Optional[date], end_date: Optional[date]) -> pl.DataFrame:
        """Load claims from local file storage"""
        claims_dir = self.storage_path / "claims"
        if not claims_dir.exists():
            return pl.DataFrame()
        
        all_data = []
        
        # Load partitioned files
        for year_dir in claims_dir.iterdir():
            if not year_dir.is_dir():
                continue
            
            year = int(year_dir.name)
            if start_date and year < start_date.year:
                continue
            if end_date and year > end_date.year:
                continue
            
            for month_file in year_dir.glob("*.parquet"):
                month = int(month_file.stem.split("_")[-1])
                
                if start_date:
                    file_date = date(year, month, 1)
                    if file_date < start_date.replace(day=1):
                        continue
                
                if end_date:
                    file_date = date(year, month, 28)  # Approximate end of month
                    if file_date > end_date:
                        continue
                
                df_month = pl.read_parquet(month_file)
                all_data.append(df_month)
        
        if not all_data:
            return pl.DataFrame()
        
        df = pl.concat(all_data)
        
        # Filter by date if specified
        if start_date or end_date:
            df = df.with_columns(
                pl.col("service_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date_parsed")
            )
            
            if start_date:
                df = df.filter(pl.col("service_date_parsed") >= start_date)
            
            if end_date:
                df = df.filter(pl.col("service_date_parsed") <= end_date)
            
            df = df.drop("service_date_parsed")
        
        return df
    
    def _load_claims_from_storage(self, start_date: Optional[date], end_date: Optional[date]) -> pl.DataFrame:
        """Load claims from object storage (S3-compatible)"""
        if not self.storage_client or not self.tenant_id:
            return pl.DataFrame()
        
        # Implementation would load from object storage
        # For now, return empty
        return pl.DataFrame()
    
    def get_claims_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: List[str] = None,
    ) -> pl.DataFrame:
        """
        Get aggregated summary of claims
        
        Args:
            start_date: Start date
            end_date: End date
            group_by: Columns to group by (e.g., ['lob', 'market', 'service_category'])
            
        Returns:
            Aggregated DataFrame
        """
        df = self.load_claims(start_date, end_date)
        
        if df.is_empty():
            return df
        
        if group_by is None:
            group_by = ["lob", "market", "service_category"]
        
        summary = df.group_by(group_by).agg([
            pl.count().alias("claim_count"),
            pl.sum("allowed_amount").alias("total_allowed"),
            pl.sum("paid_amount").alias("total_paid"),
            pl.sum("units").alias("total_units"),
            pl.n_unique("member_id").alias("unique_members"),
            pl.n_unique("provider_id").alias("unique_providers"),
        ])
        
        return summary
    
    # ========================================================================
    # MEMBER ENROLLMENT - Cohort building
    # ========================================================================
    
    def load_enrollment(
        self,
        enrollment_month: Optional[str] = None,
        lob: Optional[str] = None,
        market: Optional[str] = None,
        force_reload: bool = False,
    ) -> pl.DataFrame:
        """
        Load member enrollment data
        
        Args:
            enrollment_month: Month filter (YYYY-MM)
            lob: Line of business filter
            market: Market filter
            force_reload: Force reload from storage
            
        Returns:
            Polars DataFrame with enrollment records
        """
        if not force_reload and self._enrollment_cache is not None:
            df = self._enrollment_cache
        else:
            if self.storage_path:
                enrollment_file = self.storage_path / "enrollment_monthly.parquet"
                if enrollment_file.exists():
                    df = pl.read_parquet(enrollment_file)
                else:
                    df = pl.DataFrame()
            else:
                df = self._load_enrollment_from_storage()
            
            self._enrollment_cache = df
        
        # Apply filters
        if enrollment_month:
            df = df.filter(pl.col("enrollment_month") == enrollment_month)
        
        if lob:
            df = df.filter(pl.col("lob") == lob)
        
        if market:
            df = df.filter(pl.col("market") == market)
        
        return df
    
    def _load_enrollment_from_storage(self) -> pl.DataFrame:
        """Load enrollment from object storage"""
        return pl.DataFrame()
    
    def get_cohort_members(
        self,
        filters: Dict[str, Any],
        enrollment_month: Optional[str] = None,
    ) -> pl.DataFrame:
        """
        Get cohort of members based on filters
        
        Args:
            filters: Dictionary of filters (e.g., {'lob': 'COMMERCIAL', 'age_band': '50-64'})
            enrollment_month: Enrollment month (YYYY-MM)
            
        Returns:
            DataFrame with member IDs and attributes
        """
        df = self.load_enrollment(enrollment_month)
        
        if df.is_empty():
            return df
        
        for key, value in filters.items():
            if key in df.columns:
                df = df.filter(pl.col(key) == value)
        
        return df
    
    # ========================================================================
    # PROVIDERS - Network analysis
    # ========================================================================
    
    def load_providers(
        self,
        market: Optional[str] = None,
        specialty: Optional[str] = None,
        network_status: Optional[str] = None,
        force_reload: bool = False,
    ) -> pl.DataFrame:
        """
        Load provider directory
        
        Args:
            market: Market filter
            specialty: Specialty filter
            network_status: Network status filter (IN/OUT)
            force_reload: Force reload from storage
            
        Returns:
            Polars DataFrame with providers
        """
        if not force_reload and self._providers_cache is not None:
            df = self._providers_cache
        else:
            if self.storage_path:
                providers_file = self.storage_path / "providers.parquet"
                if providers_file.exists():
                    df = pl.read_parquet(providers_file)
                else:
                    df = pl.DataFrame()
            else:
                df = self._load_providers_from_storage()
            
            self._providers_cache = df
        
        # Apply filters
        if market:
            df = df.filter(pl.col("market") == market)
        
        if specialty:
            df = df.filter(pl.col("specialty") == specialty)
        
        if network_status:
            df = df.filter(pl.col("network_status") == network_status)
        
        return df
    
    def _load_providers_from_storage(self) -> pl.DataFrame:
        """Load providers from object storage"""
        return pl.DataFrame()
    
    # ========================================================================
    # ANALYTICS HELPERS - Common analytical queries
    # ========================================================================
    
    def get_utilization_timeseries(
        self,
        start_date: date,
        end_date: date,
        group_by: str = "service_category",
        frequency: str = "month",
    ) -> pl.DataFrame:
        """
        Get utilization timeseries
        
        Args:
            start_date: Start date
            end_date: End date
            group_by: Column to group by
            frequency: Time frequency (month, week, day)
            
        Returns:
            Timeseries DataFrame
        """
        df = self.load_claims(start_date, end_date)
        
        if df.is_empty():
            return df
        
        # Parse service date
        df = df.with_columns(
            pl.col("service_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date_parsed")
        )
        
        # Extract period based on frequency
        if frequency == "month":
            df = df.with_columns(
                pl.col("service_date_parsed").dt.truncate("1mo").alias("period")
            )
        elif frequency == "week":
            df = df.with_columns(
                pl.col("service_date_parsed").dt.truncate("1w").alias("period")
            )
        else:  # day
            df = df.with_columns(
                pl.col("service_date_parsed").alias("period")
            )
        
        # Aggregate
        agg_cols = [
            pl.count().alias("claim_count"),
            pl.sum("allowed_amount").alias("total_allowed"),
            pl.sum("paid_amount").alias("total_paid"),
            pl.n_unique("member_id").alias("unique_members"),
        ]
        
        timeseries = df.group_by(["period", group_by]).agg(agg_cols)
        
        return timeseries.sort("period")
    
    def get_provider_performance(
        self,
        start_date: date,
        end_date: date,
        provider_ids: Optional[List[str]] = None,
    ) -> pl.DataFrame:
        """
        Get provider performance metrics
        
        Args:
            start_date: Start date
            end_date: End date
            provider_ids: Optional list of provider IDs to filter
            
        Returns:
            Provider performance DataFrame
        """
        df = self.load_claims(start_date, end_date)
        
        if df.is_empty():
            return df
        
        if provider_ids:
            df = df.filter(pl.col("provider_id").is_in(provider_ids))
        
        performance = df.group_by("provider_id").agg([
            pl.count().alias("claim_count"),
            pl.sum("allowed_amount").alias("total_allowed"),
            pl.sum("paid_amount").alias("total_paid"),
            pl.mean("allowed_amount").alias("avg_allowed"),
            pl.n_unique("member_id").alias("unique_members"),
            pl.n_unique("service_category").alias("service_categories"),
        ])
        
        return performance
    
    # ========================================================================
    # ML HELPERS - Prepare data for ML models
    # ========================================================================
    
    def get_features_for_ml(
        self,
        start_date: date,
        end_date: date,
        target_variable: str = "allowed_amount",
    ) -> pd.DataFrame:
        """
        Get features ready for ML models
        
        Args:
            start_date: Start date
            end_date: End date
            target_variable: Target variable name
            
        Returns:
            Pandas DataFrame with features (for sklearn, etc.)
        """
        df = self.load_claims(start_date, end_date)
        
        if df.is_empty():
            return pd.DataFrame()
        
        # Convert to pandas
        df_pd = df.to_pandas()
        
        # Feature engineering
        if "service_date" in df_pd.columns:
            df_pd["service_date"] = pd.to_datetime(df_pd["service_date"])
            df_pd["month"] = df_pd["service_date"].dt.month
            df_pd["quarter"] = df_pd["service_date"].dt.quarter
            df_pd["year"] = df_pd["service_date"].dt.year
            df_pd["day_of_week"] = df_pd["service_date"].dt.dayofweek
        
        # One-hot encode categoricals
        categoricals = ["lob", "market", "service_category", "place_of_service"]
        for col in categoricals:
            if col in df_pd.columns:
                df_pd = pd.get_dummies(df_pd, columns=[col], prefix=col, drop_first=True)
        
        # Boolean to int
        if "in_network" in df_pd.columns:
            df_pd["in_network"] = df_pd["in_network"].astype(int)
        
        return df_pd
    
    def get_member_features(
        self,
        member_ids: List[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Get member-level features for ML
        
        Args:
            member_ids: List of member IDs
            start_date: Start date
            end_date: End date
            
        Returns:
            Member-level feature DataFrame
        """
        claims = self.load_claims(start_date, end_date)
        enrollment = self.load_enrollment()
        
        if claims.is_empty() or enrollment.is_empty():
            return pd.DataFrame()
        
        # Filter to members
        claims = claims.filter(pl.col("member_id").is_in(member_ids))
        enrollment = enrollment.filter(pl.col("member_id").is_in(member_ids))
        
        # Aggregate claims by member
        member_claims = claims.group_by("member_id").agg([
            pl.count().alias("total_claims"),
            pl.sum("allowed_amount").alias("total_allowed"),
            pl.sum("paid_amount").alias("total_paid"),
            pl.mean("allowed_amount").alias("avg_allowed"),
            pl.n_unique("provider_id").alias("unique_providers"),
            pl.n_unique("service_category").alias("unique_service_categories"),
        ])
        
        # Join with enrollment
        member_features = member_claims.join(
            enrollment.select([
                "member_id",
                "lob",
                "market",
                "age_band",
                "gender",
                "risk_score",
                "network_tier",
            ]),
            on="member_id",
            how="left",
        )
        
        # Convert to pandas for ML
        df_pd = member_features.to_pandas()
        
        # One-hot encode
        categoricals = ["lob", "market", "age_band", "gender", "network_tier"]
        for col in categoricals:
            if col in df_pd.columns:
                df_pd = pd.get_dummies(df_pd, columns=[col], prefix=col, drop_first=True)
        
        return df_pd


def create_data_model(
    storage_path: Optional[Path] = None,
    storage_client: Optional[BlobStorageClient] = None,
    tenant_id: Optional[UUID] = None,
) -> HealthcareDataModel:
    """
    Factory function to create HealthcareDataModel instance
    
    Args:
        storage_path: Local file path (for file-based storage)
        storage_client: BlobStorageClient (for cloud storage)
        tenant_id: Tenant ID
        
    Returns:
        HealthcareDataModel instance
    """
    return HealthcareDataModel(
        storage_client=storage_client,
        storage_path=storage_path,
        tenant_id=tenant_id,
    )

