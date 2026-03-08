"""Decision workspace API endpoints - Epic 3"""
from typing import Annotated, List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_decisions import (
    create_decision,
    get_decision,
    list_decisions,
    update_decision,
    finalize_decision,
    add_approval,
)
from uepi_api.storage_audit_trail import (
    create_audit_entry,
    get_audit_trail,
    get_reproducibility_pack,
)
from uepi_api.storage_evidence import (
    get_evidence_links,
    get_evidence_for_decision,
    create_evidence_snapshot,
    get_evidence_snapshot,
)
from uepi_common.models_enhanced import EvidenceLink, UncertaintyRange, ConfidenceInterval

router = APIRouter()


def convert_policy_id_to_uuid(policy_id: str, tenant_id: UUID) -> UUID:
    """Convert string policy ID to UUID - optimized (no expensive lookup)"""
    # Try UUID first
    try:
        return UUID(policy_id)
    except ValueError:
        # Not a UUID - generate deterministic UUID from string ID (fast, no lookup)
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())


# Request/Response Models
class DecisionCreate(BaseModel):
    title: str
    recommendation: str
    rationale: str
    confidence_score: float = 0.5
    uncertainty_range: Optional[Dict[str, Any]] = None
    confidence_interval: Optional[Dict[str, Any]] = None
    policy_id: Optional[str] = None
    policy_version_id: Optional[str] = None
    analysis_ids: List[str] = []
    evidence_links: List[Dict[str, Any]] = []
    assumptions_snapshot: Dict[str, Any] = {}


class DecisionUpdate(BaseModel):
    title: Optional[str] = None
    recommendation: Optional[str] = None
    rationale: Optional[str] = None
    confidence_score: Optional[float] = None
    uncertainty_range: Optional[Dict[str, Any]] = None
    confidence_interval: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    assumptions_snapshot: Optional[Dict[str, Any]] = None
    evidence_links: Optional[List[Dict[str, Any]]] = None


class ApprovalCreate(BaseModel):
    role: str
    comment: Optional[str] = None


class AuditEntryCreate(BaseModel):
    step_type: str
    step_id: str
    step_version: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None


class EvidenceLinkCreate(BaseModel):
    evidence_type: str
    evidence_id: str
    evidence_version: Optional[str] = None
    snapshot_hash: Optional[str] = None
    description: Optional[str] = None


@router.get("/decisions")
async def list_decisions_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    policy_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List all decisions, optionally filtered by policy or status"""
    try:
        policy_uuid = None
        if policy_id:
            try:
                policy_uuid = UUID(policy_id)
            except ValueError:
                # Not a UUID, convert using helper
                policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        decisions = list_decisions(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            status=status,
        )
        return [d.model_dump(mode='json', exclude_none=True) for d in decisions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list decisions: {str(e)}")


@router.post("/decisions", status_code=201)
async def create_decision_endpoint(
    decision_data: DecisionCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new decision"""
    try:
        # Validate current_user has valid user_id
        if not current_user.user_id:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
        
        decision_dict = decision_data.model_dump(exclude_none=True)
        decision_dict["created_by"] = str(current_user.user_id)
        decision_dict["created_at"] = datetime.utcnow().isoformat()
        decision_dict["updated_at"] = datetime.utcnow().isoformat()
        
        decision = create_decision(
            tenant_id=current_user.tenant_id,
            decision_data=decision_dict,
        )
        
        # Create initial audit entry
        try:
            create_audit_entry(
                tenant_id=current_user.tenant_id,
                decision_id=decision.id,
                entry_data={
                    "step_type": "decision",
                    "step_id": str(decision.id),
                    "step_version": "1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "performed_by": str(current_user.user_id),
                }
            )
        except Exception as audit_error:
            # Log but don't fail the decision creation if audit entry fails
            print(f"Warning: Failed to create audit entry: {audit_error}")
        
        return decision.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create decision: {str(e)}")


@router.get("/decisions/{decision_id}")
async def get_decision_endpoint(
    decision_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a decision by ID"""
    try:
        decision = get_decision(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
        )
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decision: {str(e)}")


@router.put("/decisions/{decision_id}")
async def update_decision_endpoint(
    decision_id: str,
    updates: DecisionUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a decision"""
    try:
        update_dict = updates.model_dump(exclude_none=True)
        decision = update_decision(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
            updates=update_dict,
        )
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update decision: {str(e)}")


@router.post("/decisions/{decision_id}/finalize")
async def finalize_decision_endpoint(
    decision_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Finalize a decision"""
    try:
        decision = finalize_decision(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
            finalized_by=current_user.user_id,
        )
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize decision: {str(e)}")


@router.post("/decisions/{decision_id}/approvals")
async def add_approval_endpoint(
    decision_id: str,
    approval_data: ApprovalCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Add an approval to a decision"""
    try:
        approval_dict = approval_data.model_dump(exclude_none=True)
        approval_dict["user_id"] = str(current_user.user_id)
        
        decision = add_approval(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
            approval_data=approval_dict,
        )
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add approval: {str(e)}")


@router.get("/decisions/{decision_id}/audit-trail")
async def get_audit_trail_endpoint(
    decision_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get audit trail for a decision"""
    try:
        audit_trail = get_audit_trail(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
        )
        return [e.model_dump(mode='json', exclude_none=True) for e in audit_trail]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")


@router.post("/decisions/{decision_id}/audit-trail")
async def create_audit_entry_endpoint(
    decision_id: str,
    entry_data: AuditEntryCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create an audit trail entry"""
    try:
        entry_dict = entry_data.model_dump(exclude_none=True)
        entry_dict["timestamp"] = datetime.utcnow().isoformat()
        entry_dict["performed_by"] = str(current_user.user_id)
        
        entry = create_audit_entry(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
            entry_data=entry_dict,
        )
        return entry.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit entry: {str(e)}")


@router.get("/decisions/{decision_id}/evidence")
async def get_evidence_endpoint(
    decision_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get evidence links for a decision"""
    try:
        evidence = get_evidence_for_decision(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
        )
        return evidence
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence: {str(e)}")


@router.post("/decisions/{decision_id}/evidence")
async def link_evidence_endpoint(
    decision_id: str,
    evidence_link: EvidenceLinkCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Link evidence to a decision"""
    try:
        # Validate decision_id
        try:
            decision_uuid = UUID(decision_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid decision ID format: {decision_id}")
        
        # Get current decision
        decision = get_decision(
            tenant_id=current_user.tenant_id,
            decision_id=decision_uuid,
        )
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Validate evidence_id is a valid UUID
        try:
            evidence_uuid = UUID(evidence_link.evidence_id)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid evidence ID format: '{evidence_link.evidence_id}'. Evidence ID must be a valid UUID."
            )
        
        # Create evidence link
        link = EvidenceLink(
            evidence_type=evidence_link.evidence_type,
            evidence_id=evidence_uuid,
            evidence_version=evidence_link.evidence_version,
            snapshot_hash=evidence_link.snapshot_hash,
            description=evidence_link.description,
        )
        
        # Add to decision's evidence links
        current_links = decision.evidence_links
        current_links.append(link)
        
        # Update decision
        updated_decision = update_decision(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
            updates={"evidence_links": [el.model_dump(mode='json', exclude_none=True) for el in current_links]},
        )
        
        return updated_decision.model_dump(mode='json', exclude_none=True) if updated_decision else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link evidence: {str(e)}")


@router.get("/decisions/{decision_id}/reproducibility-pack")
async def get_reproducibility_pack_endpoint(
    decision_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get reproducibility pack for a decision"""
    try:
        pack = get_reproducibility_pack(
            tenant_id=current_user.tenant_id,
            decision_id=UUID(decision_id),
        )
        if not pack:
            raise HTTPException(status_code=404, detail="Decision not found")
        return pack
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reproducibility pack: {str(e)}")


@router.get("/policies/{policy_id}/decisions")
async def get_policy_decisions_endpoint(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get all decisions for a policy"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        decisions = list_decisions(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
        )
        return [d.model_dump(mode='json', exclude_none=True) for d in decisions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policy decisions: {str(e)}")

