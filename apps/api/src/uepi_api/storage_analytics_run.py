"""Storage for analytics runs - Phase 1 lineage."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from uepi_api.models.analytics_run import AnalyticsRun


def create_run(
    tenant_id: UUID,
    run_type: str,
    input_refs: Optional[Dict[str, Any]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    triggered_by_user_id: Optional[UUID] = None,
    db: Optional[Session] = None,
) -> AnalyticsRun:
    """Create an analytics run in RUNNING status. Returns the model instance."""
    run = AnalyticsRun(
        tenant_id=tenant_id,
        run_type=run_type,
        status="RUNNING",
        started_at=datetime.utcnow(),
        input_refs_json=input_refs or {},
        config_snapshot_json=config_snapshot or {},
        output_refs_json=None,
        triggered_by_user_id=triggered_by_user_id,
    )
    if db is not None:
        db.add(run)
        db.commit()
        db.refresh(run)
    return run


def complete_run(
    run_id: UUID,
    output_refs: Dict[str, Any],
    db: Optional[Session] = None,
) -> None:
    """Mark run COMPLETED and set output_refs. Logs audit event."""
    from uepi_api.database import SessionLocal
    session = db or SessionLocal()
    try:
        run = session.query(AnalyticsRun).filter(AnalyticsRun.id == run_id).first()
        if run:
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.output_refs_json = output_refs
            if db is None:
                session.commit()
            # Phase 2: audit trail
            try:
                from uepi_api.storage_audit_trail import log_audit_event
                log_audit_event(
                    tenant_id=run.tenant_id,
                    action="RUN_COMPLETED",
                    object_type="ANALYTICS_RUN",
                    object_id=run.id,
                    user_id=run.triggered_by_user_id,
                    metadata_json={"run_type": run.run_type, "output_refs": output_refs},
                )
            except Exception:
                pass
    finally:
        if db is None:
            session.close()


def fail_run(
    run_id: UUID,
    error_message: str,
    db: Optional[Session] = None,
) -> None:
    """Mark run FAILED with error message. Logs audit event."""
    from uepi_api.database import SessionLocal
    session = db or SessionLocal()
    try:
        run = session.query(AnalyticsRun).filter(AnalyticsRun.id == run_id).first()
        if run:
            run.status = "FAILED"
            run.completed_at = datetime.utcnow()
            run.error_message = error_message
            if db is None:
                session.commit()
            try:
                from uepi_api.storage_audit_trail import log_audit_event
                log_audit_event(
                    tenant_id=run.tenant_id,
                    action="RUN_FAILED",
                    object_type="ANALYTICS_RUN",
                    object_id=run.id,
                    user_id=run.triggered_by_user_id,
                    metadata_json={"run_type": run.run_type, "error_message": error_message},
                )
            except Exception:
                pass
    finally:
        if db is None:
            session.close()


def get_run(run_id: UUID, tenant_id: UUID, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """Get a run by id and tenant."""
    from uepi_api.database import SessionLocal
    session = db or SessionLocal()
    try:
        run = session.query(AnalyticsRun).filter(
            AnalyticsRun.id == run_id,
            AnalyticsRun.tenant_id == tenant_id,
        ).first()
        if not run:
            return None
        return _run_to_dict(run)
    finally:
        if db is None:
            session.close()


def list_runs(
    tenant_id: UUID,
    run_type: Optional[str] = None,
    limit: int = 100,
    db: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """List runs for tenant, optionally by run_type."""
    from uepi_api.database import SessionLocal
    session = db or SessionLocal()
    try:
        q = session.query(AnalyticsRun).filter(AnalyticsRun.tenant_id == tenant_id)
        if run_type:
            q = q.filter(AnalyticsRun.run_type == run_type)
        q = q.order_by(AnalyticsRun.started_at.desc()).limit(limit)
        return [_run_to_dict(r) for r in q.all()]
    finally:
        if db is None:
            session.close()


def _run_to_dict(run: AnalyticsRun) -> Dict[str, Any]:
    return {
        "id": str(run.id),
        "tenant_id": str(run.tenant_id),
        "run_type": run.run_type,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
        "input_refs": run.input_refs_json or {},
        "config_snapshot": run.config_snapshot_json or {},
        "output_refs": run.output_refs_json or {},
        "triggered_by_user_id": str(run.triggered_by_user_id) if run.triggered_by_user_id else None,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
