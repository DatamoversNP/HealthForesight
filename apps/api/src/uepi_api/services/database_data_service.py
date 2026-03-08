"""Database-aware data service for analytics (replaces ParquetDataService)"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
import polars as pl
import pandas as pd

from sqlalchemy.orm import Session
from uepi_api.repositories.canonical_data import CanonicalDataRepository


class DatabaseDataService:
    """Service for loading data from database for analytics"""
    
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = CanonicalDataRepository(db)
    
    def load_claims_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pl.DataFrame:
        """Load claims data from database as Polars DataFrame"""
        # Get data from repository
        df = self.repository.get_claims_lines(
            tenant_id=self.tenant_id,
            start_date=start_date,
            end_date=end_date,
            lob=filters.get("lob") if filters else None,
            market=filters.get("market") if filters else None,
        )
        
        if df is None or len(df) == 0:
            return pl.DataFrame()
        
        # Convert pandas to polars
        df_pl = pl.from_pandas(df)
        
        # Apply additional filters
        if filters:
            if filters.get("in_network_only"):
                df_pl = df_pl.filter(pl.col("in_network") == True)
            
            if filters.get("cpt_codes"):
                cpt_codes = filters["cpt_codes"]
                if isinstance(cpt_codes, str):
                    cpt_codes = [cpt_codes]
                df_pl = df_pl.filter(pl.col("cpt_code").is_in(cpt_codes))
            
            if filters.get("service_category"):
                df_pl = df_pl.filter(pl.col("service_category") == filters["service_category"])
        
        return df_pl
    
    def load_enrollment_data(
        self,
        start_month: Optional[date] = None,
        end_month: Optional[date] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pl.DataFrame:
        """Load enrollment data from database as Polars DataFrame"""
        df = self.repository.get_enrollment_records(
            tenant_id=self.tenant_id,
            start_month=start_month,
            end_month=end_month,
            lob=filters.get("lob") if filters else None,
            market=filters.get("market") if filters else None,
        )
        
        if df is None or len(df) == 0:
            return pl.DataFrame()
        
        return pl.from_pandas(df)
    
    def load_provider_data(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pl.DataFrame:
        """Load provider data from database as Polars DataFrame"""
        df = self.repository.get_provider_records(
            tenant_id=self.tenant_id,
            market=filters.get("market") if filters else None,
            network_status=filters.get("network_status") if filters else None,
        )
        
        if df is None or len(df) == 0:
            return pl.DataFrame()
        
        return pl.from_pandas(df)

