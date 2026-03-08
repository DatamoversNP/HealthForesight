"""File-based audit trail storage - database only"""
import hashlib
import json
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.audit import AuditEvent as AuditEventDB
from uepi_common.models_enhanced import AuditTrailEntry


def log_generic_audit_event(
    tenant_id: UUID,
    action: str,
    object_type: str,
    object_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> None:
    """Log a generic audit event (e.g. RUN_COMPLETED, RUN_FAILED, EXPORT)."""
    from uepi_api.database import SessionLocal
    session = db or SessionLocal()
    try:
        ev = AuditEventDB(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            metadata_json=metadata_json or {},
        )
        session.add(ev)
        if db is None:
            session.commit()
    except Exception as e:
        if db is None:
            session.rollback()
        print(f"WARNING log_generic_audit_event failed: {e}")
    finally:
        if db is None:
            session.close()


def _safe_uuid(value: Any) -> Optional[UUID]:
    """Safely convert value to UUID, handling None, empty strings, and invalid formats"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            return None
    return None


def _compute_hash(data: Any) -> str:
    """Compute hash of data for reproducibility"""
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True, default=str)
    else:
        data_str = str(data)
    return hashlib.sha256(data_str.encode()).hexdigest()


def create_audit_entry(
    tenant_id: UUID,
    decision_id: UUID,
    entry_data: Dict[str, Any]
) -> AuditTrailEntry:
    """Create a new audit trail entry - stored in database"""
    return _create_audit_entry(tenant_id, decision_id, entry_data)


def _create_audit_entry(
    tenant_id: UUID,
    decision_id: UUID,
    entry_data: Dict[str, Any]
) -> AuditTrailEntry:
    """Create audit entry in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        entry_id = _safe_uuid(entry_data.get("entry_id")) or uuid4()
        
        # Compute hashes if data provided
        input_hash = None
        if entry_data.get("input_data"):
            input_hash = _compute_hash(entry_data["input_data"])
        
        output_hash = None
        if entry_data.get("output_data"):
            output_hash = _compute_hash(entry_data["output_data"])
        
        step_id = _safe_uuid(entry_data.get("step_id")) or uuid4()
        timestamp = datetime.fromisoformat(entry_data["timestamp"].replace("Z", "+00:00")) if isinstance(entry_data.get("timestamp"), str) else entry_data.get("timestamp", datetime.utcnow())
        performed_by = _safe_uuid(entry_data.get("performed_by")) or uuid4()
        
        # Create audit event
        audit_event_db = AuditEventDB(
            id=entry_id,
            tenant_id=tenant_id,
            user_id=performed_by,
            action=entry_data["step_type"],
            object_type="DECISION",
            object_id=decision_id,
            diff_summary={
                "step_id": str(step_id),
                "step_version": entry_data.get("step_version"),
                "input_hash": input_hash or entry_data.get("input_hash"),
                "output_hash": output_hash or entry_data.get("output_hash"),
            },
            metadata_json={
                "step_type": entry_data["step_type"],
            },
        )
        
        db.add(audit_event_db)
        db.commit()
        db.refresh(audit_event_db)
        
        # Return Pydantic AuditTrailEntry for compatibility
        return AuditTrailEntry(
            entry_id=entry_id,
            decision_id=decision_id,
            step_type=entry_data["step_type"],
            step_id=step_id,
            step_version=entry_data.get("step_version"),
            input_hash=input_hash or entry_data.get("input_hash"),
            output_hash=output_hash or entry_data.get("output_hash"),
            timestamp=timestamp,
            performed_by=performed_by,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR create_audit_entry (DB): {e}")
        raise ValueError(f"Failed to create audit entry: {e}")
    finally:
        db.close()


def log_audit_event(
    tenant_id: UUID,
    action: str,
    object_type: str,
    object_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> None:
    """Phase 2: Log a generic audit event (runs, exports, verdicts)."""
    from uepi_api.database import SessionLocal
    db: Session = SessionLocal()
    try:
        ev = AuditEventDB(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            metadata_json=metadata_json or {},
        )
        db.add(ev)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ERROR log_audit_event: {e}")
    finally:
        db.close()


def get_audit_trail(
    tenant_id: UUID,
    decision_id: UUID
) -> List[AuditTrailEntry]:
    """Get complete audit trail for a decision - from database"""
    return _get_audit_trail(tenant_id, decision_id)


def _get_audit_trail(
    tenant_id: UUID,
    decision_id: UUID
) -> List[AuditTrailEntry]:
    """Get audit trail from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        audit_events_db = db.query(AuditEventDB).filter(
            AuditEventDB.tenant_id == tenant_id,
            AuditEventDB.object_type == "DECISION",
            AuditEventDB.object_id == decision_id
        ).order_by(AuditEventDB.created_at).all()
        
        entries = []
        for audit_event_db in audit_events_db:
            diff_summary = audit_event_db.diff_summary if audit_event_db.diff_summary else {}
            metadata = audit_event_db.metadata_json if audit_event_db.metadata_json else {}
            
            entries.append(AuditTrailEntry(
                entry_id=audit_event_db.id,
                decision_id=decision_id,
                step_type=metadata.get("step_type", audit_event_db.action),
                step_id=UUID(diff_summary.get("step_id", str(uuid4()))) if diff_summary.get("step_id") else uuid4(),
                step_version=diff_summary.get("step_version"),
                input_hash=diff_summary.get("input_hash"),
                output_hash=diff_summary.get("output_hash"),
                timestamp=audit_event_db.created_at,
                performed_by=audit_event_db.user_id or uuid4(),
            ))
        
        return sorted(entries, key=lambda e: e.timestamp)
        
    except Exception as e:
        print(f"ERROR get_audit_trail (DB): {e}")
        return []
    finally:
        db.close()


def get_audit_trail_by_step(
    tenant_id: UUID,
    step_type: str,
    step_id: UUID
) -> List[AuditTrailEntry]:
    """Get audit trail entries for a specific step - from database"""
    return _get_audit_trail_by_step(tenant_id, step_type, step_id)


def _get_audit_trail_by_step(
    tenant_id: UUID,
    step_type: str,
    step_id: UUID
) -> List[AuditTrailEntry]:
    """Get audit trail entries for a specific step from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        audit_events_db = db.query(AuditEventDB).filter(
            AuditEventDB.tenant_id == tenant_id,
            AuditEventDB.action == step_type
        ).all()
        
        entries = []
        for audit_event_db in audit_events_db:
            diff_summary = audit_event_db.diff_summary if audit_event_db.diff_summary else {}
            metadata = audit_event_db.metadata_json if audit_event_db.metadata_json else {}
            
            step_id_str = diff_summary.get("step_id") or metadata.get("step_id")
            if step_id_str and UUID(step_id_str) == step_id:
                entries.append(AuditTrailEntry(
                    entry_id=audit_event_db.id,
                    decision_id=audit_event_db.object_id or uuid4(),
                    step_type=metadata.get("step_type", audit_event_db.action),
                    step_id=step_id,
                    step_version=diff_summary.get("step_version"),
                    input_hash=diff_summary.get("input_hash"),
                    output_hash=diff_summary.get("output_hash"),
                    timestamp=audit_event_db.created_at,
                    performed_by=audit_event_db.user_id or uuid4(),
                ))
        
        return sorted(entries, key=lambda e: e.timestamp)
        
    except Exception as e:
        print(f"ERROR get_audit_trail_by_step (DB): {e}")
        return []
    finally:
        db.close()


def get_reproducibility_pack(
    tenant_id: UUID,
    decision_id: UUID
) -> Dict[str, Any]:
    """Get complete reproducibility pack for a decision - from database"""
    from uepi_api.storage_decisions import get_decision
    
    decision = get_decision(tenant_id, decision_id)
    if not decision:
        return {}
    
    audit_trail = get_audit_trail(tenant_id, decision_id)
    
    step_ids = {}
    for entry in audit_trail:
        step_key = f"{entry.step_type}_{entry.step_id}"
        if step_key not in step_ids:
            step_ids[step_key] = {
                "step_type": entry.step_type,
                "step_id": str(entry.step_id),
                "step_version": entry.step_version,
                "input_hash": entry.input_hash,
                "output_hash": entry.output_hash,
            }
    
    pack = {
        "decision_id": str(decision_id),
        "decision": decision.model_dump(mode='json', exclude_none=True),
        "audit_trail": [e.model_dump(mode='json', exclude_none=True) for e in audit_trail],
        "steps": list(step_ids.values()),
        "evidence_links": [el.model_dump(mode='json', exclude_none=True) for el in decision.evidence_links],
        "assumptions_snapshot": decision.assumptions_snapshot,
        "generated_at": datetime.utcnow().isoformat(),
    }
    
    return pack
