"""Policy workspace API endpoints - Epic 2"""
from typing import Annotated, List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_policies import get_policy
from uepi_api.storage_policy_versions import (
    create_policy_version,
    get_policy_version,
    list_policy_versions,
    get_latest_version,
    update_policy_version,
)
from uepi_api.storage_policy_assumptions import (
    create_assumption,
    get_assumptions,
    update_assumption,
    delete_assumption,
)
from uepi_api.storage_policy_guardrails import (
    create_guardrail,
    get_guardrails,
    update_guardrail,
    delete_guardrail,
    check_guardrails,
)
from uepi_api.storage_policy_changelog import (
    create_changelog_entry,
    get_changelog,
    get_changelog_by_version,
)
from uepi_common.models_enhanced import PolicyLifecycleState
from uepi_api.logging_config import get_logger, log_action

logger = get_logger(__name__)

router = APIRouter()


def convert_policy_id_to_uuid(policy_id: str, tenant_id: UUID, policy_cache: Optional[Dict[str, Any]] = None) -> UUID:
    """Convert string policy ID to UUID - optimized for performance
    
    Args:
        policy_id: Policy ID (string or UUID string)
        tenant_id: Tenant ID
        policy_cache: Optional policy dict to avoid extra lookup
    """
    # Try UUID first
    try:
        return UUID(policy_id)
    except ValueError:
        # Not a UUID - if we have policy cache, try to get UUID from it
        if policy_cache:
            actual_id = policy_cache.get('policy_id') or policy_cache.get('id')
            if isinstance(actual_id, str) and len(actual_id) == 36:
                try:
                    return UUID(actual_id)
                except ValueError:
                    pass
            if isinstance(actual_id, UUID):
                return actual_id
        
        # Generate deterministic UUID from string ID (fast, no expensive lookup)
        # This ensures consistent UUIDs for file storage paths
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())


# Request/Response Models
class PolicyVersionCreate(BaseModel):
    effective_start_date: str
    effective_end_date: Optional[str] = None
    state: str
    change_summary: str
    change_details: Dict[str, Any] = {}
    created_by: str


class PolicyVersionResponse(BaseModel):
    version_number: int
    policy_id: str
    effective_start_date: str
    effective_end_date: Optional[str] = None
    state: str
    change_summary: str
    change_details: Dict[str, Any]
    created_by: str
    created_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class PolicyStateUpdate(BaseModel):
    new_state: str
    reason: str
    user_id: str


class AssumptionCreate(BaseModel):
    assumption_type: str
    description: str
    range: Optional[Dict[str, Any]] = None
    value: Optional[float] = None
    source: Optional[str] = None
    confidence: float = 0.5


class AssumptionUpdate(BaseModel):
    assumption_type: Optional[str] = None
    description: Optional[str] = None
    range: Optional[Dict[str, Any]] = None
    value: Optional[float] = None
    source: Optional[str] = None
    confidence: Optional[float] = None


class GuardrailCreate(BaseModel):
    metric_name: str
    threshold_type: str
    threshold_value: float
    action: str
    description: str


class GuardrailUpdate(BaseModel):
    metric_name: Optional[str] = None
    threshold_type: Optional[str] = None
    threshold_value: Optional[float] = None
    action: Optional[str] = None
    description: Optional[str] = None


class ChangelogEntryCreate(BaseModel):
    version_number: int
    changed_by: str
    change_type: str
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None


# Workspace Endpoint
@router.get("/policies/{policy_id}/workspace")
async def get_policy_workspace(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get complete policy workspace data"""
    log_action(
        logger=logger,
        action="policy_workspace_viewed",
        details={"policy_id": policy_id},
        user_id=str(current_user.user_id),
        tenant_id=str(current_user.tenant_id)
    )
    
    try:
        # Get policy - handle both UUID and string IDs
        policy = get_policy(policy_id, current_user.tenant_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Get the actual policy ID (might be UUID or string)
        actual_policy_id = policy.get('id') or policy.get('policy_id') or policy_id
        
        # Use the original policy_id (string) for storage functions - they handle both UUID and string
        # Don't convert to UUID - the storage functions can work with string IDs directly
        storage_policy_id = actual_policy_id
        
        # Get versions - handle errors gracefully with timeout protection
        try:
            versions = list_policy_versions(current_user.tenant_id, storage_policy_id)
            print(f"DEBUG get_policy_workspace: Loaded {len(versions) if isinstance(versions, list) else 0} versions")
        except Exception as e:
            print(f"ERROR: Could not load versions: {e}")
            import traceback
            traceback.print_exc()
            versions = []
        
        # Get assumptions - handle errors gracefully
        try:
            assumptions = get_assumptions(current_user.tenant_id, storage_policy_id)
            print(f"DEBUG get_policy_workspace: Loaded {len(assumptions) if isinstance(assumptions, list) else 0} assumptions")
        except Exception as e:
            print(f"ERROR: Could not load assumptions: {e}")
            import traceback
            traceback.print_exc()
            assumptions = []
        
        # Get guardrails - handle errors gracefully
        try:
            guardrails = get_guardrails(current_user.tenant_id, storage_policy_id)
            print(f"DEBUG get_policy_workspace: Loaded {len(guardrails) if isinstance(guardrails, list) else 0} guardrails")
        except Exception as e:
            print(f"ERROR: Could not load guardrails: {e}")
            import traceback
            traceback.print_exc()
            guardrails = []
        
        # Get changelog (last 50 entries) - handle errors gracefully
        try:
            changelog = get_changelog(current_user.tenant_id, storage_policy_id, limit=50)
            print(f"DEBUG get_policy_workspace: Loaded {len(changelog) if isinstance(changelog, list) else 0} changelog entries")
        except Exception as e:
            print(f"ERROR: Could not load changelog: {e}")
            import traceback
            traceback.print_exc()
            changelog = []
        
        # Ensure assumptions and guardrails are lists
        if not isinstance(assumptions, list):
            assumptions = []
        if not isinstance(guardrails, list):
            guardrails = []
        if not isinstance(changelog, list):
            changelog = []
        
        # Convert versions to dicts if they're models
        versions_list = []
        for v in versions:
            if hasattr(v, 'model_dump'):
                versions_list.append(v.model_dump(mode='json', exclude_none=True))
            elif isinstance(v, dict):
                versions_list.append(v)
            else:
                # Try to convert to dict
                try:
                    versions_list.append(dict(v))
                except:
                    versions_list.append(v)
        
        # Ensure all data is JSON-serializable
        # Convert any UUID objects to strings
        def make_serializable(obj):
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime
                return obj.isoformat()
            return obj
        
        assumptions = make_serializable(assumptions)
        guardrails = make_serializable(guardrails)
        versions_list = make_serializable(versions_list)
        changelog = make_serializable(changelog)
        
        # Debug: Log what we're returning
        print(f"DEBUG get_policy_workspace: Returning workspace data for {policy_id}")
        print(f"  - Policy ID: {policy.get('policy_id', 'N/A')}")
        print(f"  - Assumptions count: {len(assumptions) if isinstance(assumptions, list) else 0}")
        print(f"  - Guardrails count: {len(guardrails) if isinstance(guardrails, list) else 0}")
        print(f"  - Versions count: {len(versions_list)}")
        print(f"  - Changelog count: {len(changelog) if isinstance(changelog, list) else 0}")
        
        result = {
            "policy": policy,
            "versions": versions_list,
            "assumptions": assumptions if isinstance(assumptions, list) else [],
            "guardrails": guardrails if isinstance(guardrails, list) else [],
            "changelog": changelog if isinstance(changelog, list) else [],
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policy workspace: {str(e)}")


# Version Endpoints
@router.get("/policies/{policy_id}/versions", response_model=List[PolicyVersionResponse])
async def list_versions(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """List all versions for a policy"""
    try:
        # Don't convert to UUID - storage functions handle string IDs directly
        versions = list_policy_versions(current_user.tenant_id, policy_id)
        # Handle both model objects and dicts
        result = []
        for v in versions:
            if hasattr(v, 'model_dump'):
                result.append(v.model_dump(mode='json', exclude_none=True))
            elif isinstance(v, dict):
                result.append(v)
            else:
                # Try to convert to dict
                try:
                    result.append(dict(v))
                except:
                    result.append(v)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.post("/policies/{policy_id}/versions", response_model=PolicyVersionResponse, status_code=201)
async def create_version(
    policy_id: str,
    version_data: PolicyVersionCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new policy version"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        version = create_policy_version(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            version_data=version_data.model_dump(),
        )
        
        # Create changelog entry
        create_changelog_entry(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            entry_data={
                "version_number": version.version_number,
                "changed_by": version.created_by,
                "change_type": "version_created",
                "reason": version.change_summary,
            }
        )
        
        return version.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/policies/{policy_id}/versions/{version_number}", response_model=PolicyVersionResponse)
async def get_version(
    policy_id: str,
    version_number: int,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a specific policy version"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        version = get_policy_version(current_user.tenant_id, policy_uuid, version_number)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        return version.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get version: {str(e)}")


# State Management
@router.put("/policies/{policy_id}/state")
async def update_policy_state(
    policy_id: str,
    state_update: PolicyStateUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update policy lifecycle state"""
    try:
        from uepi_api.storage_policies import update_policy
        
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        
        # Validate state
        try:
            PolicyLifecycleState(state_update.new_state)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid state: {state_update.new_state}")
        
        # Get current policy
        policy = get_policy(policy_id, current_user.tenant_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        old_state = policy.get("status", "DRAFT")
        
        # Update policy status
        updated_policy = update_policy(
            policy_id=policy_uuid,
            tenant_id=current_user.tenant_id,
            policy_data={"status": state_update.new_state}
        )
        
        if not updated_policy:
            raise HTTPException(status_code=500, detail="Failed to update policy state")
        
        # Create changelog entry
        create_changelog_entry(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            entry_data={
                "version_number": 1,  # Will be updated when versioning is implemented
                "changed_by": UUID(state_update.user_id) if isinstance(state_update.user_id, str) else state_update.user_id,
                "change_type": "state_change",
                "field_name": "status",
                "old_value": old_state,
                "new_value": state_update.new_state,
                "reason": state_update.reason,
            }
        )
        
        return {"status": state_update.new_state, "updated_at": datetime.utcnow().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy state: {str(e)}")


# Assumptions Endpoints
@router.get("/policies/{policy_id}/assumptions")
async def list_assumptions(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get all assumptions for a policy"""
    try:
        # Don't convert to UUID - storage functions handle string IDs directly
        assumptions = get_assumptions(current_user.tenant_id, policy_id)
        return assumptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assumptions: {str(e)}")


@router.post("/policies/{policy_id}/assumptions", status_code=201)
async def create_policy_assumption(
    policy_id: str,
    assumption_data: AssumptionCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new policy assumption"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        assumption = create_assumption(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            assumption_data=assumption_data.model_dump(),
        )
        
        # Create changelog entry
        create_changelog_entry(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            entry_data={
                "version_number": 1,
                "changed_by": current_user.user_id,
                "change_type": "assumption_added",
                "field_name": "assumptions",
                "new_value": assumption_data.assumption_type,
                "reason": f"Added assumption: {assumption_data.description}",
            }
        )
        
        return assumption.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create assumption: {str(e)}")


@router.put("/policies/{policy_id}/assumptions/{assumption_id}")
async def update_policy_assumption(
    policy_id: str,
    assumption_id: str,
    updates: AssumptionUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a policy assumption"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        updated = update_assumption(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            assumption_id=assumption_id,
            updates=updates.model_dump(exclude_none=True),
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Assumption not found")
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update assumption: {str(e)}")


@router.delete("/policies/{policy_id}/assumptions/{assumption_id}", status_code=204)
async def delete_policy_assumption(
    policy_id: str,
    assumption_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete a policy assumption"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        deleted = delete_assumption(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            assumption_id=assumption_id,
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Assumption not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete assumption: {str(e)}")


# Guardrails Endpoints
@router.get("/policies/{policy_id}/guardrails")
async def list_guardrails(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get all guardrails for a policy"""
    try:
        # Don't convert to UUID - storage functions handle string IDs directly
        guardrails = get_guardrails(current_user.tenant_id, policy_id)
        return guardrails
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guardrails: {str(e)}")


@router.post("/policies/{policy_id}/guardrails", status_code=201)
async def create_policy_guardrail(
    policy_id: str,
    guardrail_data: GuardrailCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new policy guardrail"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        guardrail = create_guardrail(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            guardrail_data=guardrail_data.model_dump(),
        )
        
        return guardrail.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create guardrail: {str(e)}")


@router.put("/policies/{policy_id}/guardrails/{guardrail_id}")
async def update_policy_guardrail(
    policy_id: str,
    guardrail_id: str,
    updates: GuardrailUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a policy guardrail"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        updated = update_guardrail(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            guardrail_id=guardrail_id,
            updates=updates.model_dump(exclude_none=True),
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Guardrail not found")
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update guardrail: {str(e)}")


@router.delete("/policies/{policy_id}/guardrails/{guardrail_id}", status_code=204)
async def delete_policy_guardrail(
    policy_id: str,
    guardrail_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete a policy guardrail"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        deleted = delete_guardrail(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            guardrail_id=guardrail_id,
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Guardrail not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete guardrail: {str(e)}")


@router.post("/policies/{policy_id}/guardrails/check")
async def check_policy_guardrails(
    policy_id: str,
    metrics: Dict[str, float],
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Check if any guardrails are triggered"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        triggered = check_guardrails(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            metrics=metrics,
        )
        return {"triggered": triggered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check guardrails: {str(e)}")


# Changelog Endpoints
@router.get("/policies/{policy_id}/changelog")
async def get_policy_changelog(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(100, ge=1, le=1000),
):
    """Get changelog for a policy"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        changelog = get_changelog(current_user.tenant_id, policy_uuid, limit=limit)
        return changelog
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get changelog: {str(e)}")


@router.post("/policies/{policy_id}/changelog", status_code=201)
async def create_changelog_entry_endpoint(
    policy_id: str,
    entry_data: ChangelogEntryCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a changelog entry (usually automatic, but can be manual)"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        entry = create_changelog_entry(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            entry_data=entry_data.model_dump(),
        )
        return entry.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create changelog entry: {str(e)}")


