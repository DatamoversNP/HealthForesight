"""File-based evidence storage - database only"""
import json
import hashlib
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.evidence import Evidence as EvidenceDB
from uepi_common.models_enhanced import EvidenceLink


def _compute_hash(data: Any) -> str:
    """Compute hash of data for reproducibility"""
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True, default=str)
    else:
        data_str = str(data)
    return hashlib.sha256(data_str.encode()).hexdigest()


def link_evidence(
    tenant_id: UUID,
    decision_id: UUID,
    evidence_link: EvidenceLink
) -> EvidenceLink:
    """Link evidence to a decision (evidence is stored separately)"""
    # Evidence links are stored with the decision, not separately
    # This function is for creating evidence snapshots
    return evidence_link


def get_evidence_links(
    tenant_id: UUID,
    decision_id: UUID
) -> List[EvidenceLink]:
    """Get evidence links for a decision"""
    from uepi_api.storage_decisions import get_decision
    
    decision = get_decision(tenant_id, decision_id)
    if not decision:
        return []
    
    return decision.evidence_links


def get_evidence_snapshot(
    tenant_id: UUID,
    evidence_type: str,
    evidence_id: UUID,
    version: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get evidence snapshot - from database"""
    return _get_evidence_snapshot(tenant_id, evidence_type, evidence_id, version)


def _get_evidence_snapshot(
    tenant_id: UUID,
    evidence_type: str,
    evidence_id: UUID,
    version: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get evidence snapshot from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Query evidence by evidence_id (string) and evidence_type
        evidence_db = db.query(EvidenceDB).filter(
            EvidenceDB.tenant_id == tenant_id,
            EvidenceDB.evidence_id == str(evidence_id),
            EvidenceDB.evidence_type == evidence_type
        ).first()
        
        if not evidence_db:
            return None
        
        # Return as dict (same format as file-based)
        metadata = evidence_db.metadata_json if evidence_db.metadata_json else {}
        return {
            "evidence_type": evidence_db.evidence_type,
            "evidence_id": evidence_db.evidence_id,
            "version": version or metadata.get("version", "latest"),
            "snapshot_hash": metadata.get("snapshot_hash"),
            "snapshot_data": metadata.get("snapshot_data", {}),
            "created_at": evidence_db.created_at.isoformat() if evidence_db.created_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_evidence_snapshot (DB): {e}")
        return None
    finally:
        db.close()


def create_evidence_snapshot(
    tenant_id: UUID,
    evidence_type: str,
    evidence_id: UUID,
    snapshot_data: Dict[str, Any],
    version: Optional[str] = None
) -> str:
    """Create evidence snapshot and return hash - stored in database"""
    return _create_evidence_snapshot(tenant_id, evidence_type, evidence_id, snapshot_data, version)


def _create_evidence_snapshot(
    tenant_id: UUID,
    evidence_type: str,
    evidence_id: UUID,
    snapshot_data: Dict[str, Any],
    version: Optional[str] = None
) -> str:
    """Create evidence snapshot in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Compute hash
        snapshot_hash = _compute_hash(snapshot_data)
        
        # Check if evidence already exists
        evidence_db = db.query(EvidenceDB).filter(
            EvidenceDB.tenant_id == tenant_id,
            EvidenceDB.evidence_id == str(evidence_id),
            EvidenceDB.evidence_type == evidence_type
        ).first()
        
        if evidence_db:
            # Update existing evidence
            metadata = evidence_db.metadata_json if evidence_db.metadata_json else {}
            metadata.update({
                "snapshot_hash": snapshot_hash,
                "snapshot_data": snapshot_data,
                "version": version or "latest",
            })
            evidence_db.metadata_json = metadata
        else:
            # Create new evidence
            # Note: Evidence model requires resource_type and resource_id
            # We'll use evidence_type as resource_type and evidence_id as resource_id (string)
            evidence_db = EvidenceDB(
                tenant_id=tenant_id,
                resource_type=evidence_type,
                resource_id=str(evidence_id),
                evidence_id=str(evidence_id),
                evidence_type=evidence_type,
                uri=f"internal://evidence/{evidence_id}",  # Internal URI
                metadata_json={
                    "snapshot_hash": snapshot_hash,
                    "snapshot_data": snapshot_data,
                    "version": version or "latest",
                },
            )
            db.add(evidence_db)
        
        db.commit()
        db.refresh(evidence_db)
        
        return snapshot_hash
        
    except Exception as e:
        db.rollback()
        print(f"ERROR create_evidence_snapshot (DB): {e}")
        raise ValueError(f"Failed to create evidence snapshot: {e}")
    finally:
        db.close()


def get_evidence_for_decision(
    tenant_id: UUID,
    decision_id: UUID
) -> List[Dict[str, Any]]:
    """Get all evidence with snapshots for a decision"""
    evidence_links = get_evidence_links(tenant_id, decision_id)
    evidence_list = []
    
    for link in evidence_links:
        snapshot = get_evidence_snapshot(
            tenant_id,
            link.evidence_type,
            link.evidence_id,
            link.evidence_version
        )
        
        evidence_list.append({
            "evidence_link": link.model_dump(mode='json', exclude_none=True),
            "snapshot": snapshot,
            "snapshot_hash": link.snapshot_hash,
            "snapshot_verified": snapshot and snapshot.get("snapshot_hash") == link.snapshot_hash if link.snapshot_hash else None,
        })
    
    return evidence_list
