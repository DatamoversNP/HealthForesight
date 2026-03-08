"""Analytics runs API - Phase 1 lineage (list runs, get run by id)."""
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_analytics_run import get_run, list_runs

router = APIRouter()


@router.get("/runs")
async def list_analytics_runs(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    run_type: Optional[str] = Query(None, description="Filter by run_type: BASELINE | PREDICTION | OBSERVATION"),
    limit: int = Query(100, ge=1, le=500),
):
    """List analytics runs for the tenant (Phase 1 lineage)."""
    runs = list_runs(tenant_id=current_user.tenant_id, run_type=run_type, limit=limit)
    return {"items": runs, "count": len(runs)}


@router.get("/runs/{run_id}")
async def get_analytics_run(
    run_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a single analytics run by id (Phase 1 lineage)."""
    run = get_run(run_id=run_id, tenant_id=current_user.tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
