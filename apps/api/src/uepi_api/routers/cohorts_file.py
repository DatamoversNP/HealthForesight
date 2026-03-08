"""Cohort endpoints - Database-only (uses storage_cohorts which is database-only)"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_cohorts import (
    create_cohort,
    get_cohort,
    list_cohorts,
    update_cohort,
    delete_cohort,
    get_cohort_members,
)
from uepi_api.storage_policies import list_policies
from uepi_api.routers.dashboard import get_policy_performance

router = APIRouter()


class CohortCreate(BaseModel):
    """Cohort creation model"""
    name: str
    description: str | None = None
    criteria: dict  # FilterSpec


class CohortResponse(BaseModel):
    """Cohort response model"""
    id: str
    tenant_id: str
    name: str
    description: str | None
    criteria: dict
    member_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_used_at: str | None = None


@router.get("/cohorts", response_model=list[CohortResponse])
async def list_cohorts_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List cohorts - File storage implementation"""
    try:
        cohorts = list_cohorts(current_user.tenant_id, skip=skip, limit=limit)
        return cohorts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cohorts: {str(e)}")


@router.post("/cohorts", response_model=CohortResponse, status_code=201)
async def create_cohort_endpoint(
    cohort_data: CohortCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create cohort - File storage implementation"""
    try:
        cohort = create_cohort(
            tenant_id=current_user.tenant_id,
            name=cohort_data.name,
            description=cohort_data.description,
            criteria=cohort_data.criteria,
        )
        return cohort
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create cohort: {str(e)}")


@router.get("/cohorts/{cohort_id}", response_model=CohortResponse)
async def get_cohort_endpoint(
    cohort_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get cohort - File storage implementation"""
    try:
        cohort = get_cohort(current_user.tenant_id, cohort_id)
        if not cohort:
            raise HTTPException(status_code=404, detail="Cohort not found")
        return cohort
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cohort: {str(e)}")


@router.put("/cohorts/{cohort_id}", response_model=CohortResponse)
async def update_cohort_endpoint(
    cohort_id: UUID,
    cohort_data: CohortCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update cohort - File storage implementation"""
    try:
        cohort = update_cohort(
            tenant_id=current_user.tenant_id,
            cohort_id=cohort_id,
            name=cohort_data.name,
            description=cohort_data.description,
            criteria=cohort_data.criteria,
        )
        if not cohort:
            raise HTTPException(status_code=404, detail="Cohort not found")
        return cohort
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cohort: {str(e)}")


@router.delete("/cohorts/{cohort_id}", status_code=204)
async def delete_cohort_endpoint(
    cohort_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete cohort - File storage implementation"""
    try:
        deleted = delete_cohort(current_user.tenant_id, cohort_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Cohort not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cohort: {str(e)}")


@router.get("/cohorts/{cohort_id}/members")
async def get_cohort_members_endpoint(
    cohort_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get cohort members (policies) - File storage implementation"""
    try:
        # Load policies and performance data to match against criteria
        policies = list_policies(current_user.tenant_id)
        
        # Get performance data - build from observations and predicted impacts
        from uepi_api.storage_observations import list_observations
        from uepi_api.storage_policy_predicted_impact import get_predicted_impact
        
        # Build performance list from observations and predicted impacts
        observations = list_observations(current_user.tenant_id)
        performance = []
        
        # Create a policy lookup map for efficient matching
        policy_lookup = {}
        for p in policies:
            p_id = p.get("id") or p.get("policy_id")
            if p_id:
                p_id_str = str(p_id)
                policy_lookup[p_id_str] = p
                # Also index by UUID if it's a UUID
                try:
                    from uuid import UUID
                    if isinstance(p_id, str):
                        try:
                            uuid_obj = UUID(p_id)
                            policy_lookup[str(uuid_obj)] = p
                        except ValueError:
                            pass
                except Exception:
                    pass
        
        # Add from observations - only include if we can match to a policy
        for obs in observations:
            policy_id = obs.get("policy_id")
            if not policy_id:
                continue
                
            policy_id_str = str(policy_id)
            
            # Find policy in lookup
            policy = policy_lookup.get(policy_id_str)
            if not policy:
                # Try one more time with direct comparison
                for p in policies:
                    p_id = str(p.get("id") or p.get("policy_id") or "")
                    if p_id == policy_id_str:
                        policy = p
                        break
            
            # Only include if we found a matching policy
            if policy:
                metrics = obs.get("metrics", {})
                comparisons = obs.get("comparisons", {})
                vs_baseline = comparisons.get("vs_baseline", {})
                
                # Get policy name
                policy_name = policy.get("name") or policy.get("policy_name") or policy.get("description")
                if not policy_name or policy_name.strip() == "":
                    policy_name = f"Policy {policy_id_str[:8]}"
                # Clean up name - remove extra whitespace
                policy_name = " ".join(policy_name.split())
                # Truncate if too long
                if len(policy_name) > 100:
                    policy_name = policy_name[:100] + "..."
                
                performance.append({
                    "policy_id": policy_id_str,
                    "policy_name": policy_name,
                    "avg_utilization_change_pct": metrics.get("observed_percent_change", 0),
                    "avg_cost_impact": vs_baseline.get("change_from_baseline", 0),
                    "is_predicted": False,
                })
        
        # Add from predicted impacts (if not already in observations)
        for policy in policies[:100]:  # Limit to avoid too many API calls
            policy_id = policy.get("id") or policy.get("policy_id")
            if not policy_id:
                continue
                
            policy_id_str = str(policy_id)
            if not any(p.get("policy_id") == policy_id_str for p in performance):
                try:
                    predicted = get_predicted_impact(policy_id, current_user.tenant_id)
                    if predicted:
                        metrics = predicted.get("metrics", {})
                        # Get policy name
                        policy_name = policy.get("name") or policy.get("policy_name") or policy.get("description", "Unnamed Policy")
                        if len(policy_name) > 100:
                            policy_name = policy_name[:100] + "..."
                        
                        performance.append({
                            "policy_id": policy_id_str,
                            "policy_name": policy_name,
                            "avg_utilization_change_pct": metrics.get("utilization_change_pct", 0),
                            "avg_cost_impact": metrics.get("cost_change_pmpm", 0) * 10000,  # Rough estimate
                            "is_predicted": True,
                        })
                except Exception:
                    pass
        
        members = get_cohort_members(
            tenant_id=current_user.tenant_id,
            cohort_id=cohort_id,
            policies=policies,
            performance=performance,
            skip=skip,
            limit=limit,
        )
        
        return {
            "cohort_id": str(cohort_id),
            "members": members,
            "total": len(members),
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cohort members: {str(e)}")
