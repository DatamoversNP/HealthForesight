"""Run elasticity analysis against the API database (used by Celery worker and API background fallback)."""
from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def run_elasticity_analysis_sync(
    db: Session,
    tenant_id: UUID,
    analysis_id: UUID,
    policy_id: UUID,
    service_categories: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Compute elasticity, persist ElasticityAnalysisResult + AnalysisResultIndex, update Analysis status.
    Caller supplies an open Session (worker or API request).
    """
    from uepi_api.config import get_settings
    from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisResultIndex, ElasticityAnalysisResult
    from uepi_common.analytics.elasticity import ElasticityModeler
    from uepi_common.storage.factory import create_storage_client

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        return {"status": "error", "message": "Analysis not found"}

    analysis.status = AnalysisStatus.RUNNING.value
    db.commit()

    from uepi_api.database import set_local_statement_timeout

    set_local_statement_timeout(db, 600_000)

    try:
        settings = get_settings()
        try:
            storage_client = create_storage_client(settings=settings.object_storage)
        except Exception:
            from uepi_common.storage.noop import NoOpBlobStorageClient

            storage_client = NoOpBlobStorageClient()
        bucket = (
            getattr(settings.object_storage, "bucket", None)
            or getattr(settings.object_storage, "bucket_name", None)
            or "uepi-data"
        )
        modeler = ElasticityModeler(storage_client, bucket)

        result = modeler.estimate_elasticity(
            tenant_id,
            policy_id,
            service_categories,
        )

        result_dict = {
            "policy_id": str(result.policy_id),
            "service_categories": {
                k: {
                    "service_category": v.service_category,
                    "elasticity_coefficient": v.elasticity_coefficient,
                    "elasticity_function": v.elasticity_function,
                    "threshold_friction": v.threshold_friction,
                    "confidence_score": v.confidence_score,
                    "data_points": v.data_points,
                    "model_version": getattr(v, "model_version", "1.0"),
                    "created_at": v.created_at.isoformat(),
                }
                for k, v in result.service_categories.items()
            },
            "overall_elasticity": result.overall_elasticity,
            "model_quality": result.model_quality,
            "warnings": getattr(result, "warnings", []),
            "created_at": result.created_at.isoformat(),
        }

        existing = (
            db.query(ElasticityAnalysisResult)
            .filter(
                ElasticityAnalysisResult.analysis_id == analysis_id,
                ElasticityAnalysisResult.tenant_id == tenant_id,
            )
            .first()
        )
        if existing:
            existing.result_data_json = result_dict
            existing.updated_at = datetime.utcnow()
        else:
            db.add(
                ElasticityAnalysisResult(
                    tenant_id=tenant_id,
                    analysis_id=analysis_id,
                    policy_id=policy_id,
                    result_data_json=result_dict,
                    schema_version="1.0",
                )
            )
        idx = (
            db.query(AnalysisResultIndex)
            .filter(
                AnalysisResultIndex.analysis_id == analysis_id,
                AnalysisResultIndex.result_type == "ELASTICITY",
            )
            .first()
        )
        if not idx:
            db.add(
                AnalysisResultIndex(
                    tenant_id=tenant_id,
                    analysis_id=analysis_id,
                    result_type="ELASTICITY",
                    data_uri=None,
                    schema_version="1.0",
                )
            )
        analysis.status = AnalysisStatus.COMPLETED.value
        db.commit()

        result_key = f"{tenant_id}/results/analyses/{analysis_id}/elasticity.json"
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
                json.dump(result_dict, tmp, indent=2, default=str)
                tmp_path = tmp.name
            try:
                with open(tmp_path, "rb") as f:
                    storage_client.upload_blob(
                        container=settings.object_storage.bucket,
                        blob_name=result_key,
                        data=f.read(),
                        content_type="application/json",
                    )
                uri = f"{settings.object_storage.bucket}/{result_key}"
                idx2 = (
                    db.query(AnalysisResultIndex)
                    .filter(
                        AnalysisResultIndex.analysis_id == analysis_id,
                        AnalysisResultIndex.result_type == "ELASTICITY",
                    )
                    .first()
                )
                if idx2:
                    idx2.data_uri = uri
                    db.commit()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as upload_err:
            print(f"Elasticity: optional upload failed (results saved to DB): {upload_err}")

        return {
            "status": "completed",
            "analysis_id": str(analysis_id),
            "model_quality": result.model_quality,
            "overall_elasticity": result.overall_elasticity,
        }
    except Exception as e:
        failed = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if failed:
            failed.status = AnalysisStatus.FAILED.value
            err_msg = str(e)
            if hasattr(failed, "error_message"):
                failed.error_message = (err_msg[:2000] if len(err_msg) > 2000 else err_msg) or None
            db.commit()
        raise


def run_elasticity_analysis_background_task(
    tenant_id: str,
    analysis_id: str,
    policy_id: str,
    service_categories: Optional[list[str]] = None,
) -> None:
    """Run elasticity in a fresh DB session after HTTP response (Celery-down fallback)."""
    from uepi_api.database import SessionLocal, set_local_statement_timeout

    db = SessionLocal()
    try:
        set_local_statement_timeout(db, 600_000)
        run_elasticity_analysis_sync(
            db,
            UUID(tenant_id),
            UUID(analysis_id),
            UUID(policy_id),
            service_categories,
        )
    except Exception:
        logger.exception("Background elasticity analysis failed")
    finally:
        db.close()
