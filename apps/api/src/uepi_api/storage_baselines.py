"""Baseline storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.baseline import Baseline


def create_baseline(
    tenant_id: UUID,
    baseline_data: Dict[str, Any],
    input_refs: Optional[Dict[str, Any]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    triggered_by_user_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Create a new baseline. Optional input_refs/config_snapshot for deterministic lineage (Phase 1)."""
    return _create_baseline_in_db(
        tenant_id, baseline_data,
        input_refs=input_refs,
        config_snapshot=config_snapshot,
        triggered_by_user_id=triggered_by_user_id,
    )


def _create_baseline_in_db(
    tenant_id: UUID,
    baseline_data: Dict[str, Any],
    input_refs: Optional[Dict[str, Any]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    triggered_by_user_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Create baseline in database. Optionally create analytics run when explicit refs/config provided."""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate baseline_id if not provided
        baseline_id = baseline_data.get("baseline_id") or str(uuid4())
        
        # Parse dates
        window_start = datetime.fromisoformat(baseline_data["window_start_date"].replace("Z", "+00:00")) if isinstance(baseline_data.get("window_start_date"), str) else baseline_data.get("window_start_date")
        window_end = datetime.fromisoformat(baseline_data["window_end_date"].replace("Z", "+00:00")) if isinstance(baseline_data.get("window_end_date"), str) else baseline_data.get("window_end_date")
        computed_at = datetime.fromisoformat(baseline_data["computed_at"].replace("Z", "+00:00")) if isinstance(baseline_data.get("computed_at"), str) else baseline_data.get("computed_at", datetime.utcnow())
        
        # Parse UUIDs - handle both UUID objects and strings
        policy_id_value = baseline_data.get("policy_id")
        if policy_id_value:
            if isinstance(policy_id_value, UUID):
                policy_id = policy_id_value
            elif isinstance(policy_id_value, str):
                policy_id = UUID(policy_id_value)
            else:
                policy_id = None
        else:
            policy_id = None
        
        parent_baseline_id_value = baseline_data.get("parent_baseline_id")
        if parent_baseline_id_value:
            if isinstance(parent_baseline_id_value, UUID):
                parent_baseline_id = parent_baseline_id_value
            elif isinstance(parent_baseline_id_value, str):
                parent_baseline_id = UUID(parent_baseline_id_value)
            else:
                parent_baseline_id = None
        else:
            parent_baseline_id = None
        
        # Phase 1: optional analytics run for lineage when explicit refs/config provided
        run = None
        if input_refs is not None or config_snapshot is not None:
            try:
                from uepi_api.storage_analytics_run import create_run
                refs = input_refs if input_refs is not None else {}
                cfg = config_snapshot if config_snapshot is not None else {}
                if not refs and not cfg:
                    refs = {
                        "policy_id": str(policy_id) if policy_id else None,
                        "parent_baseline_id": str(parent_baseline_id) if parent_baseline_id else None,
                        "data_period_ids": baseline_data.get("data_period_ids", []),
                    }
                    cfg = {
                        "window_start_date": window_start.isoformat() if window_start else None,
                        "window_end_date": window_end.isoformat() if window_end else None,
                    }
                run = create_run(
                    tenant_id=tenant_id,
                    run_type="BASELINE",
                    input_refs=refs,
                    config_snapshot=cfg,
                    triggered_by_user_id=triggered_by_user_id,
                    db=db,
                )
            except Exception:
                # analytics_runs table may not exist yet (migration not run); continue without run
                run = None
        
        # Create baseline in database
        baseline = Baseline(
            tenant_id=tenant_id,
            baseline_id=baseline_id,
            version=baseline_data.get("version", 1),
            baseline_type=baseline_data.get("baseline_type", "ROLLING"),
            window_start_date=window_start,
            window_end_date=window_end,
            policy_id=policy_id,
            parent_baseline_id=parent_baseline_id,
            data_period_ids_json=baseline_data.get("data_period_ids", []),
            baseline_metrics_json=baseline_data.get("baseline_metrics", {}),
            computed_at=computed_at,
            computed_by=baseline_data.get("computed_by", "system"),
            shift_detected=baseline_data.get("shift_detected", False),
            shift_summary_json=baseline_data.get("shift_summary", {}),
            refresh_reason=baseline_data.get("refresh_reason", "NEW_DATA"),
            analytics_run_id=run.id if run else None,
        )
        
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        
        if run:
            from uepi_api.storage_analytics_run import complete_run
            complete_run(
                run.id,
                output_refs={"baseline_id": baseline.baseline_id, "baseline_db_id": str(baseline.id)},
                db=db,
            )
        
        # Return as dict (same format as file-based)
        return {
            "baseline_id": baseline.baseline_id,
            "tenant_id": str(baseline.tenant_id),
            "version": baseline.version,
            "baseline_type": baseline.baseline_type,
            "window_start_date": baseline.window_start_date.isoformat() if baseline.window_start_date else None,
            "window_end_date": baseline.window_end_date.isoformat() if baseline.window_end_date else None,
            "data_period_ids": baseline.data_period_ids_json if baseline.data_period_ids_json else [],
            "baseline_metrics": baseline.baseline_metrics_json if baseline.baseline_metrics_json else {},
            "computed_at": baseline.computed_at.isoformat() if baseline.computed_at else None,
            "computed_by": baseline.computed_by,
            "parent_baseline_id": str(baseline.parent_baseline_id) if baseline.parent_baseline_id else None,
            "policy_id": str(baseline.policy_id) if baseline.policy_id else None,
            "shift_detected": baseline.shift_detected,
            "shift_summary": baseline.shift_summary_json if baseline.shift_summary_json else {},
            "refresh_reason": baseline.refresh_reason,
            "created_at": baseline.created_at.isoformat() if baseline.created_at else None,
            "updated_at": baseline.updated_at.isoformat() if baseline.updated_at else None,
            "metadata": {},
            "analytics_run_id": str(baseline.analytics_run_id) if getattr(baseline, "analytics_run_id", None) else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create baseline: {e}")
    finally:
        db.close()


def get_baseline(tenant_id: UUID, baseline_id: str) -> Optional[Dict[str, Any]]:
    """Get a baseline by ID - from database"""
    return _get_baseline_from_db(tenant_id, baseline_id)


def _get_baseline_from_db(tenant_id: UUID, baseline_id: str) -> Optional[Dict[str, Any]]:
    """Get baseline from database by baseline_id (string) or id (UUID)"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Try to match by baseline_id (string) first
        baseline = db.query(Baseline).filter(
            Baseline.tenant_id == tenant_id,
            Baseline.baseline_id == baseline_id
        ).first()
        
        # If not found, try to match by id (UUID)
        if not baseline:
            try:
                from uuid import UUID as UUIDType
                baseline_uuid = UUIDType(baseline_id)
                baseline = db.query(Baseline).filter(
                    Baseline.tenant_id == tenant_id,
                    Baseline.id == baseline_uuid
                ).first()
            except (ValueError, TypeError):
                # baseline_id is not a valid UUID, continue
                pass
        
        if not baseline:
            return None
        
        # Return as dict (same format as file-based)
        return {
            "id": str(baseline.id),  # Database UUID (for foreign key)
            "baseline_id": baseline.baseline_id,  # String ID (for compatibility)
            "tenant_id": str(baseline.tenant_id),
            "version": baseline.version,
            "baseline_type": baseline.baseline_type,
            "window_start_date": baseline.window_start_date.isoformat() if baseline.window_start_date else None,
            "window_end_date": baseline.window_end_date.isoformat() if baseline.window_end_date else None,
            "data_period_ids": baseline.data_period_ids_json if baseline.data_period_ids_json else [],
            "baseline_metrics": baseline.baseline_metrics_json if baseline.baseline_metrics_json else {},
            "computed_at": baseline.computed_at.isoformat() if baseline.computed_at else None,
            "computed_by": baseline.computed_by,
            "parent_baseline_id": str(baseline.parent_baseline_id) if baseline.parent_baseline_id else None,
            "policy_id": str(baseline.policy_id) if baseline.policy_id else None,
            "shift_detected": baseline.shift_detected,
            "shift_summary": baseline.shift_summary_json if baseline.shift_summary_json else {},
            "refresh_reason": baseline.refresh_reason,
            "created_at": baseline.created_at.isoformat() if baseline.created_at else None,
            "updated_at": baseline.updated_at.isoformat() if baseline.updated_at else None,
            "metadata": {},
        }
        
    except Exception as e:
        print(f"ERROR get_baseline (DB): {e}")
        return None
    finally:
        db.close()


def list_baselines(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    baseline_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List baselines for a tenant - from database"""
    return _list_baselines_from_db(tenant_id, policy_id, baseline_type)


def get_latest_baseline(tenant_id: UUID, policy_id: Optional[UUID] = None, baseline_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get latest baseline for tenant (optionally filtered by policy_id and baseline_type)"""
    baselines = _list_baselines_from_db(tenant_id, policy_id, baseline_type)
    if not baselines:
        return None
    
    # Sort by computed_at descending and return latest
    baselines_sorted = sorted(
        baselines,
        key=lambda b: b.get("computed_at") or "",
        reverse=True
    )
    return baselines_sorted[0] if baselines_sorted else None


def _list_baselines_from_db(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    baseline_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List baselines from database. Falls back to raw SQL if analytics_run_id column is missing (migration not run)."""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc, text

    db: Session = SessionLocal()
    try:
        query = db.query(Baseline).filter(Baseline.tenant_id == tenant_id)

        if policy_id:
            query = query.filter(Baseline.policy_id == policy_id)
        if baseline_type:
            query = query.filter(Baseline.baseline_type == baseline_type)
        baselines = query.order_by(desc(Baseline.computed_at)).all()

        result = []
        for baseline in baselines:
            result.append({
                "id": str(baseline.id),
                "baseline_id": baseline.baseline_id,
                "tenant_id": str(baseline.tenant_id),
                "version": baseline.version,
                "baseline_type": baseline.baseline_type,
                "window_start_date": baseline.window_start_date.isoformat() if baseline.window_start_date else None,
                "window_end_date": baseline.window_end_date.isoformat() if baseline.window_end_date else None,
                "data_period_ids": baseline.data_period_ids_json if baseline.data_period_ids_json else [],
                "baseline_metrics": baseline.baseline_metrics_json if baseline.baseline_metrics_json else {},
                "computed_at": baseline.computed_at.isoformat() if baseline.computed_at else None,
                "computed_by": baseline.computed_by,
                "parent_baseline_id": str(baseline.parent_baseline_id) if baseline.parent_baseline_id else None,
                "policy_id": str(baseline.policy_id) if baseline.policy_id else None,
                "shift_detected": baseline.shift_detected,
                "shift_summary": baseline.shift_summary_json if baseline.shift_summary_json else {},
                "refresh_reason": baseline.refresh_reason,
                "created_at": baseline.created_at.isoformat() if baseline.created_at else None,
                "updated_at": baseline.updated_at.isoformat() if baseline.updated_at else None,
                "metadata": {},
            })
        return result

    except Exception as e:
        err_msg = str(e).lower()
        if "analytics_run_id" in err_msg and ("does not exist" in err_msg or "undefinedcolumn" in err_msg):
            db.rollback()
            try:
                return _list_baselines_from_db_fallback(db, tenant_id, policy_id, baseline_type)
            except Exception as fb_e:
                print(f"ERROR list_baselines (DB fallback): {fb_e}")
                return []
        print(f"ERROR list_baselines (DB): {e}")
        return []
    finally:
        db.close()


def _list_baselines_from_db_fallback(
    db: Session,
    tenant_id: UUID,
    policy_id: Optional[UUID],
    baseline_type: Optional[str],
) -> List[Dict[str, Any]]:
    """List baselines using raw SQL when analytics_run_id column is missing."""
    from sqlalchemy import text

    sql = """
        SELECT id, baseline_id, tenant_id, version, baseline_type,
               window_start_date, window_end_date, policy_id, parent_baseline_id,
               data_period_ids_json, baseline_metrics_json, computed_at, computed_by,
               shift_detected, shift_summary_json, refresh_reason, created_at, updated_at
        FROM baselines
        WHERE tenant_id = :tid
    """
    params: Dict[str, Any] = {"tid": str(tenant_id)}
    if policy_id:
        sql += " AND policy_id = :pid"
        params["pid"] = str(policy_id)
    if baseline_type:
        sql += " AND baseline_type = :bt"
        params["bt"] = baseline_type
    sql += " ORDER BY computed_at DESC"

    rows = db.execute(text(sql), params).fetchall()
    result = []
    for row in rows:
        result.append({
            "id": str(row.id),
            "baseline_id": row.baseline_id,
            "tenant_id": str(row.tenant_id),
            "version": row.version,
            "baseline_type": row.baseline_type,
            "window_start_date": row.window_start_date.isoformat() if row.window_start_date else None,
            "window_end_date": row.window_end_date.isoformat() if row.window_end_date else None,
            "data_period_ids": list(row.data_period_ids_json) if row.data_period_ids_json else [],
            "baseline_metrics": dict(row.baseline_metrics_json) if row.baseline_metrics_json else {},
            "computed_at": row.computed_at.isoformat() if row.computed_at else None,
            "computed_by": row.computed_by,
            "parent_baseline_id": str(row.parent_baseline_id) if row.parent_baseline_id else None,
            "policy_id": str(row.policy_id) if row.policy_id else None,
            "shift_detected": row.shift_detected,
            "shift_summary": dict(row.shift_summary_json) if row.shift_summary_json else {},
            "refresh_reason": row.refresh_reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "metadata": {},
        })
    return result


def get_latest_baseline(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    baseline_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get the latest baseline for a tenant (optionally filtered by policy and baseline_type)"""
    baselines = list_baselines(tenant_id=tenant_id, policy_id=policy_id, baseline_type=baseline_type)
    if not baselines:
        return None
    
    # Already sorted by computed_at descending, so return first
    return baselines[0]


def delete_policy_level_baselines(tenant_id: UUID) -> int:
    """Delete all policy-level baselines (where policy_id IS NOT NULL) for a tenant.
    Returns number of baselines deleted."""
    from uepi_api.database import SessionLocal

    db: Session = SessionLocal()
    try:
        deleted = db.query(Baseline).filter(
            Baseline.tenant_id == tenant_id,
            Baseline.policy_id.isnot(None),
        ).delete()
        db.commit()
        return deleted
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete policy-level baselines: {e}")
    finally:
        db.close()


def get_baseline_by_data_period(
    tenant_id: UUID,
    data_period_id: str,
) -> Optional[Dict[str, Any]]:
    """Get baseline that used a specific data period"""
    baselines = list_baselines(tenant_id=tenant_id)
    
    for baseline in baselines:
        if data_period_id in baseline.get("data_period_ids", []):
            return baseline
    
    return None


def update_baseline(
    tenant_id: UUID,
    baseline_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update an existing baseline in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        baseline = db.query(Baseline).filter(
            Baseline.tenant_id == tenant_id,
            Baseline.baseline_id == baseline_id
        ).first()
        
        if not baseline:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(baseline, key):
                if key in ['window_start_date', 'window_end_date', 'computed_at']:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif key == 'policy_id' and value:
                    value = UUID(value) if isinstance(value, str) else value
                elif key == 'parent_baseline_id' and value:
                    value = UUID(value) if isinstance(value, str) else value
                elif key in ['data_period_ids', 'baseline_metrics', 'shift_summary']:
                    # These are JSON fields, keep as dict/list
                    pass
                setattr(baseline, f"{key}_json" if key in ['data_period_ids', 'baseline_metrics', 'shift_summary'] else key, value)
        
        db.commit()
        db.refresh(baseline)
        
        # Return as dict
        return {
            "baseline_id": baseline.baseline_id,
            "tenant_id": str(baseline.tenant_id),
            "version": baseline.version,
            "baseline_type": baseline.baseline_type,
            "window_start_date": baseline.window_start_date.isoformat() if baseline.window_start_date else None,
            "window_end_date": baseline.window_end_date.isoformat() if baseline.window_end_date else None,
            "data_period_ids": baseline.data_period_ids_json if baseline.data_period_ids_json else [],
            "baseline_metrics": baseline.baseline_metrics_json if baseline.baseline_metrics_json else {},
            "computed_at": baseline.computed_at.isoformat() if baseline.computed_at else None,
            "computed_by": baseline.computed_by,
            "parent_baseline_id": str(baseline.parent_baseline_id) if baseline.parent_baseline_id else None,
            "policy_id": str(baseline.policy_id) if baseline.policy_id else None,
            "shift_detected": baseline.shift_detected,
            "shift_summary": baseline.shift_summary_json if baseline.shift_summary_json else {},
            "refresh_reason": baseline.refresh_reason,
            "created_at": baseline.created_at.isoformat() if baseline.created_at else None,
            "updated_at": baseline.updated_at.isoformat() if baseline.updated_at else None,
            "metadata": {},
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update baseline: {e}")
    finally:
        db.close()
