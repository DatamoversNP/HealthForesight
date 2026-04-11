"""Baseline endpoints - File storage only"""
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, get_demo_current_user, require_role
from uepi_api.database import get_db
from uepi_api.storage_baselines import (
    create_baseline,
    get_baseline,
    list_baselines,
    get_latest_baseline,
    update_baseline,
)
from uepi_api.baseline_refresh import (
    refresh_baseline,
    should_refresh_baseline,
    detect_baseline_shift,
)


router = APIRouter()


class BaselineRefreshRequest(BaseModel):
    """Baseline refresh request model"""
    policy_id: Optional[UUID] = None
    baseline_type: str = "ROLLING"
    window_months: int = 12
    refresh_reason: str = "MANUAL"


class BaselineResponse(BaseModel):
    """Baseline response model"""
    baseline_id: str
    tenant_id: UUID
    version: int
    baseline_type: str
    window_start_date: str
    window_end_date: str
    data_period_ids: List[str]
    baseline_metrics: dict
    computed_at: str
    computed_by: str
    parent_baseline_id: Optional[str]
    policy_id: Optional[UUID]
    shift_detected: bool
    shift_summary: dict
    refresh_reason: str
    created_at: str
    updated_at: str
    metadata: dict
    analytics_run_id: Optional[str] = None


class BaselineShiftResponse(BaseModel):
    """Baseline shift detection response model"""
    baseline_id: str
    previous_baseline_id: Optional[str]
    shift_detected: bool
    significant_shift: bool
    utilization_change_pct: float
    cost_change_pct: float
    shift_summary: dict


class RefreshAllBaselinesResponse(BaseModel):
    """Response for refresh-all: general baseline + one per policy"""
    general_baseline: Optional[dict] = None
    policy_baselines: List[dict] = []  # [{"policy_id": str, "policy_name": str, "baseline": dict}, ...]
    errors: List[str] = []


@router.post("/baselines/refresh", response_model=BaselineResponse, status_code=status.HTTP_201_CREATED)
async def refresh_baseline_route(
    request: BaselineRefreshRequest,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    """Refresh baseline using available baseline-eligible data periods or direct database computation"""
    baseline = refresh_baseline(
        tenant_id=current_user.tenant_id,
        policy_id=request.policy_id,
        baseline_type=request.baseline_type,
        window_months=request.window_months,
        refresh_reason=request.refresh_reason,
        db=db,  # Pass db session
    )
    
    if not baseline:
        raise HTTPException(
            status_code=400,
            detail="Failed to refresh baseline. No data available in database for baseline computation."
        )
    
    return BaselineResponse(**baseline)


@router.post("/baselines/refresh-all", response_model=RefreshAllBaselinesResponse, status_code=status.HTTP_200_OK)
async def refresh_all_baselines_route(
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN", "UM_LEADER"))],
    db: Session = Depends(get_db),
    baseline_type: str = "ROLLING",
    window_months: int = 12,
):
    """Refresh general baseline and policy-specific baselines for all policies in one go."""
    from uepi_api.storage_policies import list_policies

    result: RefreshAllBaselinesResponse = RefreshAllBaselinesResponse()
    tenant_id = current_user.tenant_id

    # 1. General (tenant-level) baseline
    try:
        general = refresh_baseline(
            tenant_id=tenant_id,
            policy_id=None,
            baseline_type=baseline_type,
            window_months=window_months,
            refresh_reason="MANUAL",
            db=db,
        )
        if general:
            result.general_baseline = general
    except Exception as e:
        result.errors.append(f"General baseline: {str(e)}")

    # 2. Policy-specific baselines
    policies = list_policies(tenant_id) or []
    for policy in policies:
        policy_id_str = policy.get("id") or policy.get("policy_id")
        policy_name = policy.get("name") or policy.get("policy_name") or str(policy_id_str)
        if not policy_id_str:
            result.errors.append("Policy missing id")
            continue
        try:
            policy_id_uuid = UUID(str(policy_id_str))
        except ValueError:
            result.errors.append(f"Invalid policy_id: {policy_id_str}")
            continue
        try:
            baseline = refresh_baseline(
                tenant_id=tenant_id,
                policy_id=policy_id_uuid,
                baseline_type=baseline_type,
                window_months=window_months,
                refresh_reason="MANUAL",
                db=db,
            )
            if baseline:
                result.policy_baselines.append({
                    "policy_id": str(policy_id_uuid),
                    "policy_name": policy_name,
                    "baseline": baseline,
                })
        except Exception as e:
            result.errors.append(f"{policy_name}: {str(e)}")

    return result


@router.get("/baselines", response_model=List[BaselineResponse])
async def list_baselines_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    policy_id: Optional[UUID] = Query(None, description="Filter by policy_id. Use null for general baselines."),
    baseline_type: Optional[str] = Query(None, description="Filter by baseline_type: 'ROLLING', 'FIXED', 'GENERAL', 'POLICY_SPECIFIC'"),
    general_only: bool = Query(False, description="If true, return only general baselines (policy_id is null)"),
):
    """List all baselines for the current tenant
    
    Filtering options:
    - general_only=true: Returns only general baselines (no policy_id)
    - policy_id=<uuid>: Returns only baselines for that policy
    - baseline_type: Filter by type (ROLLING, FIXED, GENERAL, POLICY_SPECIFIC)
    """
    # If general_only is requested, ensure policy_id is None
    if general_only:
        policy_id = None
    
    baselines = list_baselines(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
        baseline_type=baseline_type,
    )
    return [BaselineResponse(**b) for b in baselines]


@router.get("/baselines/latest", response_model=BaselineResponse)
async def get_latest_baseline_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    policy_id: Optional[UUID] = Query(None),
):
    """Get the latest baseline for the current tenant"""
    baseline = get_latest_baseline(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    
    if not baseline:
        raise HTTPException(status_code=404, detail="No baseline found")
    
    return BaselineResponse(**baseline)


@router.get("/baselines/{baseline_id}", response_model=BaselineResponse)
async def get_baseline_route(
    baseline_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a baseline by ID"""
    baseline = get_baseline(tenant_id=current_user.tenant_id, baseline_id=baseline_id)
    
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    
    return BaselineResponse(**baseline)


@router.get("/baselines/{baseline_id}/shift", response_model=BaselineShiftResponse)
async def get_baseline_shift_route(
    baseline_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get shift detection results for a baseline"""
    baseline = get_baseline(tenant_id=current_user.tenant_id, baseline_id=baseline_id)
    
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    
    shift_summary = baseline.get("shift_summary", {})
    parent_baseline_id = baseline.get("parent_baseline_id")
    
    return BaselineShiftResponse(
        baseline_id=baseline_id,
        previous_baseline_id=parent_baseline_id,
        shift_detected=baseline.get("shift_detected", False),
        significant_shift=shift_summary.get("significant_shift", False),
        utilization_change_pct=shift_summary.get("utilization_change_pct", 0.0),
        cost_change_pct=shift_summary.get("cost_change_pct", 0.0),
        shift_summary=shift_summary,
    )


@router.get("/baselines/for-policy/{policy_id}", response_model=BaselineResponse)
async def get_baseline_for_policy_route(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get the latest baseline for a specific policy"""
    baseline = get_latest_baseline(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    
    if not baseline:
        raise HTTPException(status_code=404, detail="No baseline found for this policy")
    
    return BaselineResponse(**baseline)


@router.get("/baselines/should-refresh")
async def check_should_refresh_baseline_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    policy_id: Optional[UUID] = Query(None),
):
    """Check if baseline should be refreshed"""
    should_refresh, reason = should_refresh_baseline(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    
    return {
        "should_refresh": should_refresh,
        "reason": reason,
    }
