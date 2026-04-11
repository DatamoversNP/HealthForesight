"""Traceability endpoints - File storage only"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.traceability_store import (
    add_traceability,
    get_traceability,
    query_by_traceability,
    detect_refresh_triggers,
    generate_audit_trail,
)


router = APIRouter()


class TraceabilityCreate(BaseModel):
    """Traceability creation model"""
    entity_type: str
    entity_id: UUID
    data_period_id: Optional[UUID] = None
    policy_id: Optional[UUID] = None
    policy_version_id: Optional[UUID] = None
    metadata: dict = {}


class TraceabilityResponse(BaseModel):
    """Traceability response model"""
    trace_id: str
    tenant_id: UUID
    entity_type: str
    entity_id: str
    data_period_id: Optional[str]
    policy_id: Optional[str]
    policy_version_id: Optional[str]
    created_at: str
    metadata: dict


class RefreshStatusResponse(BaseModel):
    """Refresh status response model"""
    entity_type: str
    entity_id: str
    needs_refresh: bool
    refresh_reason: Optional[str]
    last_refresh_timestamp: Optional[str]
    dependencies: dict


@router.post("/traceability", response_model=TraceabilityResponse, status_code=201)
async def create_traceability_route(
    traceability_data: TraceabilityCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Add traceability metadata to an entity"""
    trace_record = add_traceability(
        tenant_id=current_user.tenant_id,
        entity_type=traceability_data.entity_type,
        entity_id=traceability_data.entity_id,
        data_period_id=traceability_data.data_period_id,
        policy_id=traceability_data.policy_id,
        policy_version_id=traceability_data.policy_version_id,
        metadata=traceability_data.metadata,
    )
    return TraceabilityResponse(**trace_record)


# Static paths MUST be registered before /traceability/{trace_id} or "refresh-status",
# "query", and "audit-trail" are captured as trace_id and UUID() raises → HTTP 500.


@router.get("/traceability/query")
async def query_traceability_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    data_period_id: Optional[UUID] = Query(None),
    policy_id: Optional[UUID] = Query(None),
    policy_version_id: Optional[UUID] = Query(None),
):
    """Query traceability records based on criteria"""
    records = query_by_traceability(
        tenant_id=current_user.tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        data_period_id=data_period_id,
        policy_id=policy_id,
        policy_version_id=policy_version_id,
    )
    return [TraceabilityResponse(**r) for r in records]


@router.get("/traceability/refresh-status")
async def get_refresh_status_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    entity_type: str = Query(..., description="Entity type (baseline, prediction, observation)"),
    entity_id: UUID = Query(..., description="Entity ID"),
    last_refresh_timestamp: str = Query(..., description="Last refresh timestamp (ISO format)"),
):
    """Check if an entity needs refresh based on underlying dependencies"""
    from datetime import datetime
    
    try:
        last_refresh = datetime.fromisoformat(last_refresh_timestamp.replace('Z', '+00:00'))
        needs_refresh = detect_refresh_triggers(
            tenant_id=current_user.tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            last_refresh_timestamp=last_refresh,
        )
        
        # Get dependencies
        trace_records = query_by_traceability(
            tenant_id=current_user.tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        
        dependencies = {
            "data_periods": [r.get("data_period_id") for r in trace_records if r.get("data_period_id")],
            "policy_versions": [r.get("policy_version_id") for r in trace_records if r.get("policy_version_id")],
        }
        
        return RefreshStatusResponse(
            entity_type=entity_type,
            entity_id=str(entity_id),
            needs_refresh=needs_refresh,
            refresh_reason="Underlying data periods or policy versions have changed" if needs_refresh else None,
            last_refresh_timestamp=last_refresh_timestamp,
            dependencies=dependencies,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {e}")


@router.get("/traceability/audit-trail")
async def get_audit_trail_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    entity_type: str = Query(..., description="Entity type"),
    entity_id: UUID = Query(..., description="Entity ID"),
):
    """Generate audit trail for an entity"""
    audit_records = generate_audit_trail(
        tenant_id=current_user.tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return [TraceabilityResponse(**r) for r in audit_records]


@router.get("/traceability/{trace_id}", response_model=TraceabilityResponse)
async def get_traceability_route(
    trace_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get traceability metadata by trace ID"""
    trace_record = get_traceability(current_user.tenant_id, UUID(trace_id))
    if not trace_record:
        raise HTTPException(status_code=404, detail="Traceability record not found")
    return TraceabilityResponse(**trace_record)
