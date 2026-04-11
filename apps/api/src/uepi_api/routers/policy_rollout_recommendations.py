"""Policy rollout recommendations — data-driven, deduplicated, explainable."""
from __future__ import annotations

from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.services.policy_rollout_recommendations import compute_policy_rollout_recommendations

router = APIRouter()


@router.get("/recommendations/policy-rollouts")
def get_policy_rollout_recommendations(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    months_lookback: int = Query(12, ge=3, le=36, description="Claims aggregation window (months)"),
    limit: int = Query(20, ge=1, le=50, description="Max recommendations to return"),
    jaccard_threshold: float = Query(
        0.55, ge=0.2, le=0.95, description="Code-set similarity above which an archetype matches an existing policy"
    ),
) -> Dict[str, Any]:
    """
    Rank net-new policy rollout ideas for the tenant.

    Uses historical claims concentration, curated clinical/UM archetypes, tenant baseline references,
    optional learned elasticity models, and structured deduplication against in-force policies.
    """
    try:
        return compute_policy_rollout_recommendations(
            db,
            current_user.tenant_id,
            months_lookback=months_lookback,
            limit=limit,
            jaccard_threshold=jaccard_threshold,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy rollout recommendations failed: {e!s}") from e
