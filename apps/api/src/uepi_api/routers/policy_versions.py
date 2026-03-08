"""Policy version endpoints - File storage only"""
from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.storage_policy_versions import (
    create_policy_version,
    get_policy_version,
    list_policy_versions,
    get_latest_version,
    update_policy_version,
)

router = APIRouter()


class PolicyVersionCreate(BaseModel):
    """Policy version creation model"""
    effective_start_date: str
    effective_end_date: Optional[str] = None
    status: str = "DRAFT"  # DRAFT, ACTIVE, PAUSED, RETIRED
    scope: Optional[dict] = None
    policy_levers: Optional[list[dict]] = None
    conditions: Optional[list[dict]] = None
    exceptions: Optional[list[dict]] = None
    change_description: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/policies/{policy_id}/versions", status_code=201)
async def create_version(
    policy_id: UUID,
    version_data: PolicyVersionCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Create a new policy version"""
    try:
        # Prepare version data with required fields
        version_dict = version_data.model_dump(exclude_none=True)
        version_dict["state"] = version_dict.get("status", "DRAFT")  # Map status to state
        version_dict["created_by"] = str(current_user.user_id)
        version_dict["created_at"] = datetime.utcnow().isoformat()
        if "effective_start_date" not in version_dict:
            version_dict["effective_start_date"] = datetime.utcnow().isoformat()
        
        version_doc = create_policy_version(
            tenant_id=current_user.tenant_id,
            policy_id=policy_id,
            version_data=version_dict,
        )
        return version_doc
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/policies/{policy_id}/versions")
async def list_versions(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """List all versions for a policy"""
    # Storage functions handle both UUID and string IDs
    versions = list_policy_versions(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    # Handle both model objects and dicts
    result = []
    for v in versions:
        if hasattr(v, 'model_dump'):
            result.append(v.model_dump(mode='json', exclude_none=True))
        elif isinstance(v, dict):
            result.append(v)
        else:
            try:
                result.append(dict(v))
            except:
                result.append(v)
    return result


@router.get("/policies/{policy_id}/versions/{version_number}")
async def get_version(
    policy_id: UUID,
    version_number: int,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get a policy version by version number"""
    version = get_policy_version(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
        version_number=version_number,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Policy version not found")
    return version


@router.get("/policies/{policy_id}/versions/active")
async def get_active_version(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    as_of_date: Optional[str] = Query(None),
):
    """Get the active policy version as of a given date"""
    # For now, return the latest version (can be enhanced later to check effective dates)
    version = get_latest_version(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    if not version:
        raise HTTPException(status_code=404, detail="No active policy version found")
    return version


@router.get("/policies/{policy_id}/versions/latest")
async def get_latest_version_endpoint(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get the latest policy version"""
    version = get_latest_version(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    if not version:
        raise HTTPException(status_code=404, detail="No policy versions found")
    return version


@router.get("/policies/{policy_id}/versions/{version_number}/changes")
async def get_version_changes(
    policy_id: UUID,
    version_number: int,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get changes between this version and its parent"""
    try:
        version = get_policy_version(
            tenant_id=current_user.tenant_id,
            policy_id=policy_id,
            version_number=version_number,
        )
        if not version:
            raise HTTPException(status_code=404, detail="Policy version not found")
        
        # Return change summary and details
        return {
            "version_number": version.version_number,
            "change_summary": version.change_summary,
            "change_details": version.change_details,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
