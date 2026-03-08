"""File-based decision storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from uepi_common.models_enhanced import Decision, EvidenceLink, UncertaintyRange, ConfidenceInterval
from sqlalchemy.dialects.postgresql import JSONB

try:
    JSONType = JSONB
except ImportError:
    from sqlalchemy import JSON
    JSONType = JSON


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


def create_decision(
    tenant_id: UUID,
    decision_data: Dict[str, Any]
) -> Decision:
    """Create a new decision - stored in database"""
    return _create_decision(tenant_id, decision_data)


def _create_decision(
    tenant_id: UUID,
    decision_data: Dict[str, Any]
) -> Decision:
    """Create decision in database - stored as JSONB"""
    from uepi_api.database import SessionLocal, engine
    
    db: Session = SessionLocal()
    try:
        decision_id = _safe_uuid(decision_data.get("id")) or uuid4()
        
        # Parse uncertainty range if provided
        uncertainty_range = None
        if decision_data.get("uncertainty_range"):
            ur_data = decision_data["uncertainty_range"]
            uncertainty_range = UncertaintyRange(
                p10=ur_data.get("p10", 0),
                p50=ur_data.get("p50", 0),
                p90=ur_data.get("p90", 0),
                mean=ur_data.get("mean"),
                std_dev=ur_data.get("std_dev"),
            )
        
        # Parse confidence interval if provided
        confidence_interval = None
        if decision_data.get("confidence_interval"):
            ci_data = decision_data["confidence_interval"]
            confidence_interval = ConfidenceInterval(
                lower_bound=ci_data.get("lower_bound", 0),
                upper_bound=ci_data.get("upper_bound", 0),
                confidence_level=ci_data.get("confidence_level", 0.95),
                distribution_type=ci_data.get("distribution_type"),
            )
        
        # Parse evidence links
        evidence_links = []
        for el_data in decision_data.get("evidence_links", []):
            evidence_id = _safe_uuid(el_data.get("evidence_id"))
            if evidence_id:
                evidence_links.append(EvidenceLink(
                    evidence_type=el_data.get("evidence_type", "analysis"),
                    evidence_id=evidence_id,
                    evidence_version=el_data.get("evidence_version"),
                    snapshot_hash=el_data.get("snapshot_hash"),
                    description=el_data.get("description"),
                ))
        
        # Create decision object
        created_by_uuid = _safe_uuid(decision_data.get("created_by")) or uuid4()
        
        decision = Decision(
            id=decision_id,
            tenant_id=tenant_id,
            title=decision_data["title"],
            recommendation=decision_data["recommendation"],
            rationale=decision_data["rationale"],
            confidence_score=decision_data.get("confidence_score", 0.5),
            uncertainty_range=uncertainty_range,
            confidence_interval=confidence_interval,
            policy_id=_safe_uuid(decision_data.get("policy_id")),
            policy_version_id=_safe_uuid(decision_data.get("policy_version_id")),
            analysis_ids=[aid for aid in [_safe_uuid(aid) for aid in decision_data.get("analysis_ids", [])] if aid],
            evidence_links=evidence_links,
            assumptions_snapshot=decision_data.get("assumptions_snapshot", {}),
            approvals=decision_data.get("approvals", []),
            status=decision_data.get("status", "DRAFT"),
            created_by=created_by_uuid,
            created_at=datetime.fromisoformat(decision_data["created_at"].replace("Z", "+00:00")) if isinstance(decision_data.get("created_at"), str) else decision_data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(decision_data["updated_at"].replace("Z", "+00:00")) if isinstance(decision_data.get("updated_at"), str) else decision_data.get("updated_at", datetime.utcnow()),
            finalized_at=datetime.fromisoformat(decision_data["finalized_at"].replace("Z", "+00:00")) if decision_data.get("finalized_at") and isinstance(decision_data.get("finalized_at"), str) else decision_data.get("finalized_at"),
            finalized_by=_safe_uuid(decision_data.get("finalized_by")),
        )
        
        # Store decision as JSONB in database
        # Create decisions table if it doesn't exist (using raw SQL for flexibility)
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS decisions (
                id UUID PRIMARY KEY,
                tenant_id UUID NOT NULL,
                decision_json JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                policy_id UUID,
                status VARCHAR(50),
                created_by UUID
            )
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_decisions_tenant ON decisions(tenant_id)
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_decisions_policy ON decisions(policy_id) WHERE policy_id IS NOT NULL
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_decisions_status ON decisions(status) WHERE status IS NOT NULL
        """))
        
        # Convert decision to JSON
        decision_dict = decision.model_dump(mode='json', exclude_none=True)
        
        # Insert decision
        db.execute(text("""
            INSERT INTO decisions (id, tenant_id, decision_json, created_at, updated_at, policy_id, status, created_by)
            VALUES (:id, :tenant_id, :decision_json, :created_at, :updated_at, :policy_id, :status, :created_by)
        """), {
            "id": decision_id,
            "tenant_id": tenant_id,
            "decision_json": decision_dict,
            "created_at": decision.created_at,
            "updated_at": decision.updated_at,
            "policy_id": decision.policy_id,
            "status": decision.status,
            "created_by": decision.created_by,
        })
        
        db.commit()
        return decision
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create decision: {e}")
    finally:
        db.close()


def get_decision(
    tenant_id: UUID,
    decision_id: UUID
) -> Optional[Decision]:
    """Get a decision by ID - from database"""
    return _get_decision(tenant_id, decision_id)


def _get_decision(
    tenant_id: UUID,
    decision_id: UUID
) -> Optional[Decision]:
    """Get decision from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT decision_json FROM decisions
            WHERE id = :decision_id AND tenant_id = :tenant_id
        """), {
            "decision_id": decision_id,
            "tenant_id": tenant_id
        })
        
        row = result.first()
        if not row:
            return None
        
        data = row[0]  # JSONB column
        
        # Parse datetime fields
        for field in ["created_at", "updated_at", "finalized_at"]:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        # Parse UUIDs
        data["id"] = UUID(data["id"])
        data["tenant_id"] = UUID(data["tenant_id"])
        data["created_by"] = UUID(data["created_by"])
        if data.get("policy_id"):
            data["policy_id"] = UUID(data["policy_id"])
        if data.get("policy_version_id"):
            data["policy_version_id"] = UUID(data["policy_version_id"])
        if data.get("finalized_by"):
            data["finalized_by"] = UUID(data["finalized_by"])
        
        # Parse analysis_ids
        data["analysis_ids"] = [UUID(aid) if isinstance(aid, str) else aid for aid in data.get("analysis_ids", [])]
        
        # Parse evidence links
        evidence_links = []
        for el_data in data.get("evidence_links", []):
            evidence_links.append(EvidenceLink(
                evidence_type=el_data.get("evidence_type", "analysis"),
                evidence_id=UUID(el_data["evidence_id"]) if isinstance(el_data.get("evidence_id"), str) else el_data.get("evidence_id"),
                evidence_version=el_data.get("evidence_version"),
                snapshot_hash=el_data.get("snapshot_hash"),
                description=el_data.get("description"),
            ))
        data["evidence_links"] = evidence_links
        
        # Parse uncertainty range
        if data.get("uncertainty_range"):
            ur_data = data["uncertainty_range"]
            data["uncertainty_range"] = UncertaintyRange(**ur_data)
        
        # Parse confidence interval
        if data.get("confidence_interval"):
            ci_data = data["confidence_interval"]
            data["confidence_interval"] = ConfidenceInterval(**ci_data)
        
        return Decision(**data)
        
    except Exception as e:
        print(f"ERROR get_decision (DB): {e}")
        return None
    finally:
        db.close()


def list_decisions(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    status: Optional[str] = None
) -> List[Decision]:
    """List all decisions for a tenant, optionally filtered by policy or status"""
    return _list_decisions(tenant_id, policy_id, status)


def _list_decisions(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    status: Optional[str] = None
) -> List[Decision]:
    """List decisions from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = """
            SELECT decision_json FROM decisions
            WHERE tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_id}
        
        if policy_id:
            query += " AND policy_id = :policy_id"
            params["policy_id"] = policy_id
        
        if status:
            query += " AND status = :status"
            params["status"] = status
        
        query += " ORDER BY created_at DESC"
        
        result = db.execute(text(query), params)
        decisions = []
        
        for row in result:
            data = row[0]  # JSONB column
            
            # Parse datetime fields
            for field in ["created_at", "updated_at", "finalized_at"]:
                if data.get(field):
                    data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
            
            # Parse UUIDs
            data["id"] = UUID(data["id"])
            data["tenant_id"] = UUID(data["tenant_id"])
            data["created_by"] = UUID(data["created_by"])
            if data.get("policy_id"):
                data["policy_id"] = UUID(data["policy_id"])
            if data.get("policy_version_id"):
                data["policy_version_id"] = UUID(data["policy_version_id"])
            if data.get("finalized_by"):
                data["finalized_by"] = UUID(data["finalized_by"])
            
            # Parse analysis_ids
            data["analysis_ids"] = [UUID(aid) if isinstance(aid, str) else aid for aid in data.get("analysis_ids", [])]
            
            # Parse evidence links
            evidence_links = []
            for el_data in data.get("evidence_links", []):
                evidence_links.append(EvidenceLink(
                    evidence_type=el_data.get("evidence_type", "analysis"),
                    evidence_id=UUID(el_data["evidence_id"]) if isinstance(el_data.get("evidence_id"), str) else el_data.get("evidence_id"),
                    evidence_version=el_data.get("evidence_version"),
                    snapshot_hash=el_data.get("snapshot_hash"),
                    description=el_data.get("description"),
                ))
            data["evidence_links"] = evidence_links
            
            # Parse uncertainty range
            if data.get("uncertainty_range"):
                ur_data = data["uncertainty_range"]
                data["uncertainty_range"] = UncertaintyRange(**ur_data)
            
            # Parse confidence interval
            if data.get("confidence_interval"):
                ci_data = data["confidence_interval"]
                data["confidence_interval"] = ConfidenceInterval(**ci_data)
            
            decisions.append(Decision(**data))
        
        return decisions
        
    except Exception as e:
        print(f"ERROR list_decisions (DB): {e}")
        return []
    finally:
        db.close()


def update_decision(
    tenant_id: UUID,
    decision_id: UUID,
    updates: Dict[str, Any]
) -> Optional[Decision]:
    """Update a decision - stored in database"""
    return _update_decision(tenant_id, decision_id, updates)


def _update_decision(
    tenant_id: UUID,
    decision_id: UUID,
    updates: Dict[str, Any]
) -> Optional[Decision]:
    """Update decision in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Get existing decision
        decision = _get_decision(tenant_id, decision_id)
        if not decision:
            return None
        
        # Update fields
        if "title" in updates:
            decision.title = updates["title"]
        if "recommendation" in updates:
            decision.recommendation = updates["recommendation"]
        if "rationale" in updates:
            decision.rationale = updates["rationale"]
        if "confidence_score" in updates:
            decision.confidence_score = updates["confidence_score"]
        if "status" in updates:
            decision.status = updates["status"]
        if "uncertainty_range" in updates:
            ur_data = updates["uncertainty_range"]
            decision.uncertainty_range = UncertaintyRange(**ur_data) if ur_data else None
        if "confidence_interval" in updates:
            ci_data = updates["confidence_interval"]
            decision.confidence_interval = ConfidenceInterval(**ci_data) if ci_data else None
        if "assumptions_snapshot" in updates:
            decision.assumptions_snapshot = updates["assumptions_snapshot"]
        if "evidence_links" in updates:
            evidence_links = []
            for el_data in updates["evidence_links"]:
                evidence_links.append(EvidenceLink(
                    evidence_type=el_data.get("evidence_type", "analysis"),
                    evidence_id=UUID(el_data["evidence_id"]) if isinstance(el_data.get("evidence_id"), str) else el_data.get("evidence_id"),
                    evidence_version=el_data.get("evidence_version"),
                    snapshot_hash=el_data.get("snapshot_hash"),
                    description=el_data.get("description"),
                ))
            decision.evidence_links = evidence_links
        
        decision.updated_at = datetime.utcnow()
        
        # Update in database
        decision_dict = decision.model_dump(mode='json', exclude_none=True)
        
        db.execute(text("""
            UPDATE decisions
            SET decision_json = :decision_json,
                updated_at = :updated_at,
                policy_id = :policy_id,
                status = :status
            WHERE id = :decision_id AND tenant_id = :tenant_id
        """), {
            "decision_id": decision_id,
            "tenant_id": tenant_id,
            "decision_json": decision_dict,
            "updated_at": decision.updated_at,
            "policy_id": decision.policy_id,
            "status": decision.status,
        })
        
        db.commit()
        return decision
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_decision (DB): {e}")
        return None
    finally:
        db.close()


def finalize_decision(
    tenant_id: UUID,
    decision_id: UUID,
    finalized_by: UUID
) -> Optional[Decision]:
    """Finalize a decision - stored in database"""
    return _finalize_decision(tenant_id, decision_id, finalized_by)


def _finalize_decision(
    tenant_id: UUID,
    decision_id: UUID,
    finalized_by: UUID
) -> Optional[Decision]:
    """Finalize decision in database"""
    decision = _get_decision(tenant_id, decision_id)
    if not decision:
        return None
    
    decision.status = "FINAL"
    decision.finalized_at = datetime.utcnow()
    decision.finalized_by = finalized_by
    decision.updated_at = datetime.utcnow()
    
    return _update_decision(tenant_id, decision_id, {
        "status": decision.status,
        "finalized_at": decision.finalized_at.isoformat(),
        "finalized_by": str(finalized_by),
    })


def add_approval(
    tenant_id: UUID,
    decision_id: UUID,
    approval_data: Dict[str, Any]
) -> Optional[Decision]:
    """Add an approval to a decision - stored in database"""
    # In database mode, approvals are managed separately via storage_collaboration
    # For now, just update the decision's approvals list for compatibility
    decision = _get_decision(tenant_id, decision_id)
    if not decision:
        return None
    
    approval = {
        "user_id": str(approval_data.get("user_id")),
        "role": approval_data.get("role", ""),
        "approved_at": datetime.utcnow().isoformat(),
        "comment": approval_data.get("comment", ""),
    }
    
    if not decision.approvals:
        decision.approvals = []
    decision.approvals.append(approval)
    
    # If all required approvals are in, update status
    if decision.status == "PENDING_APPROVAL" and len(decision.approvals) > 0:
        decision.status = "APPROVED"
    
    return _update_decision(tenant_id, decision_id, {
        "approvals": decision.approvals,
        "status": decision.status,
    })
