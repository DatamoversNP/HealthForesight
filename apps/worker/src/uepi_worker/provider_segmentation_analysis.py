"""Provider segmentation analysis - refactored to use new analytics modules"""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from uepi_common.analytics.provider_segmentation import ProviderSegmentation
from uepi_common.data.parquet_service import ParquetDataService
from uepi_common.storage.factory import create_storage_client

from uepi_worker.config import get_settings

settings = get_settings()


def run_provider_segmentation_analysis(
    tenant_id: UUID,
    analysis_id: UUID,
    policy_id: UUID,
    policy_effective_date: datetime,
    treatment_filters: dict[str, Any],
    pre_months: int = 6,
    post_months: int = 6,
    affected_codes: Optional[list[str]] = None,
    n_clusters: int = 4,
) -> dict[str, Any]:
    """Run provider segmentation analysis (Phase 6)
    
    Args:
        tenant_id: Tenant ID
        analysis_id: Analysis ID
        policy_id: Policy ID
        policy_effective_date: Policy effective date
        treatment_filters: Treatment group filters
        pre_months: Pre-policy window in months
        post_months: Post-policy window in months
        affected_codes: Optional list of affected codes (if None, will fetch from policy)
        n_clusters: Number of clusters (archetypes)
        
    Returns:
        Dictionary with provider segmentation results
    """
    # Initialize services
    storage_client = create_storage_client(settings=settings.object_storage)
    parquet_service = ParquetDataService(
        storage_client=storage_client,
        container=settings.object_storage.bucket_name_or_bucket,
    )
    
    # If affected_codes not provided, fetch from policy
    if affected_codes is None:
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
                    "total_providers": 0,
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
    
    if not affected_codes:
        return {
            "archetypes": [],
            "provider_assignments": [],
            "total_providers": 0,
            "warnings": ["No affected codes found in policy"],
        }
    
    # Initialize provider segmentation engine
    segmentation = ProviderSegmentation(tenant_id=tenant_id, parquet_service=parquet_service)
    
    # Run segmentation
    result = segmentation.segment_providers(
        policy_effective_date=policy_effective_date,
        affected_codes=affected_codes,
        treatment_filters=treatment_filters,
        pre_months=pre_months,
        post_months=post_months,
        n_clusters=n_clusters,
    )
    
    # Add metadata
    result["policy_id"] = str(policy_id)
    result["analysis_id"] = str(analysis_id)
    result["affected_codes"] = affected_codes
    
    return result

