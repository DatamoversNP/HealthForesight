"""Scorecard endpoints - File storage only"""
from typing import Annotated, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token, get_demo_current_user
from uepi_api.storage_scorecards import (
    generate_scorecard_from_predicted_impact,
    save_scorecard,
    get_scorecard,
    list_scorecards,
)
from uepi_api.storage_policy_predicted_impact import get_predicted_impact
from uepi_api.storage_policies import list_policies

router = APIRouter()


class GenerateScorecardsRequest(BaseModel):
    """Request model for generating scorecards"""
    period: Optional[str] = None
    policy_ids: Optional[list[UUID | str]] = None  # Accept both UUID and string IDs


@router.get("/scorecards/policies")
async def list_policy_scorecards(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    period: str | None = Query(None),
    lob: str | None = Query(None),
    market: str | None = Query(None),
):
    """List policy scorecards - File storage only"""
    tenant_id = current_user.tenant_id
    
    # Get all scorecards
    scorecards = list_scorecards(
        tenant_id=tenant_id,
        period=period,
    )
    
    # Filter by LOB and market if provided (requires policy lookup)
    if lob or market:
        filtered = []
        for scorecard in scorecards:
            try:
                policy = list_policies(tenant_id)
                policy_id_str = scorecard["policy_id"]
                policy_match = next((p for p in policy if p["id"] == policy_id_str), None)
                
                if policy_match:
                    policy_scope = policy_match.get("scope", {})
                    policy_lob = policy_scope.get("lob")
                    policy_market = policy_scope.get("market")
                    
                    if lob and policy_lob != lob:
                        continue
                    if market and policy_market != market:
                        continue
                    
                    filtered.append(scorecard)
            except Exception:
                # Include scorecard if policy lookup fails
                filtered.append(scorecard)
        
        return filtered
    
    return scorecards


@router.get("/scorecards/policies/{policy_id}")
async def get_policy_scorecard(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    period: str | None = Query(None),
):
    """Get scorecard for a specific policy - File storage only"""
    tenant_id = current_user.tenant_id
    
    if period:
        scorecard = get_scorecard(policy_id, period, tenant_id)
    else:
        # Get latest scorecard
        scorecards = list_scorecards(
            tenant_id=tenant_id,
            policy_ids=[policy_id],
        )
        scorecard = scorecards[0] if scorecards else None
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not found. Generate scorecards first.")
    
    return scorecard


@router.post("/scorecards/generate", status_code=201)
async def generate_scorecards(
    request: GenerateScorecardsRequest,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Generate scorecards for a period - File storage only"""
    try:
        tenant_id = current_user.tenant_id
        
        # Get policies to generate scorecards for
        if request.policy_ids:
            # Convert to strings for consistent handling
            policy_ids = [str(pid) for pid in request.policy_ids]
        else:
            # Generate for all policies
            all_policies = list_policies(tenant_id)
            # Get policy IDs as strings (handle both UUID and string IDs)
            policy_ids = [str(p.get("id") or p.get("policy_id", "")) for p in all_policies if p.get("id") or p.get("policy_id")]
        
        if not policy_ids:
            raise HTTPException(status_code=404, detail="No policies found to generate scorecards for")
        
        generated_scorecards = []
        
        for policy_id_str in policy_ids:
            try:
                # Convert to UUID if possible, otherwise use as string
                try:
                    policy_id_uuid = UUID(policy_id_str)
                except (ValueError, AttributeError):
                    policy_id_uuid = policy_id_str
                
                # Get predicted impact for this policy
                predicted_impact = get_predicted_impact(policy_id_uuid, tenant_id)
                
                if not predicted_impact:
                    # Debug: Check what's in the policy
                    from uepi_api.storage_policies import get_policy
                    policy = get_policy(policy_id, tenant_id)
                    if policy:
                        print(f"DEBUG: Policy {policy_id} found but no predicted_impact")
                        print(f"DEBUG: Policy keys: {list(policy.keys())}")
                        print(f"DEBUG: Has predicted_impact at root: {policy.get('predicted_impact') is not None}")
                        print(f"DEBUG: Has metadata: {policy.get('metadata') is not None}")
                        if policy.get('metadata'):
                            print(f"DEBUG: Metadata keys: {list(policy.get('metadata', {}).keys())}")
                    else:
                        print(f"DEBUG: Policy {policy_id} not found")
                    continue
                
                # Generate scorecard from predicted impact
                # Convert policy_id to UUID for the function (it expects UUID)
                try:
                    policy_id_for_func = UUID(policy_id_str) if isinstance(policy_id_str, str) else policy_id_uuid
                except (ValueError, AttributeError):
                    # If it's not a valid UUID, generate a deterministic UUID from the string
                    import hashlib
                    namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
                    policy_id_for_func = UUID(bytes=hashlib.md5(namespace.bytes + str(policy_id_str).encode()).digest())
                
                scorecard = generate_scorecard_from_predicted_impact(
                    policy_id=policy_id_for_func,
                    predicted_impact=predicted_impact,
                    period=request.period,
                )
                
                # Update scorecard to use original policy_id string
                scorecard["policy_id"] = str(policy_id_str)
                
                # Save scorecard
                save_scorecard(scorecard, tenant_id)
                generated_scorecards.append(scorecard)
                print(f"DEBUG: Successfully generated scorecard for policy {policy_id_str}")
            except Exception as e:
                # Continue with other policies if one fails
                import traceback
                print(f"Warning: Failed to generate scorecard for policy {policy_id_str}: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                continue
        
        if not generated_scorecards:
            raise HTTPException(
                status_code=400,
                detail="No predicted impacts found for the specified policies. Please generate predicted impacts first using the 'Generate Predicted Impact' button on the Policies page."
            )
        
        return {
            "message": f"Generated {len(generated_scorecards)} scorecards",
            "scorecards": generated_scorecards,
            "count": len(generated_scorecards),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scorecards: {str(e)}")


@router.get("/scorecards/policies/{policy_id}/trends")
async def get_policy_scorecard_trends(
    policy_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    periods: int = Query(4, ge=1, le=12, description="Number of periods to return"),
):
    """Get scorecard trends for a policy - File storage only"""
    tenant_id = current_user.tenant_id
    
    # Get all scorecards for this policy
    scorecards = list_scorecards(
        tenant_id=tenant_id,
        policy_ids=[policy_id],
    )
    
    if not scorecards:
        raise HTTPException(status_code=404, detail="No scorecards found for this policy. Generate scorecards first.")
    
    # Sort by period (most recent first) and take the requested number
    sorted_scorecards = sorted(scorecards, key=lambda x: x.get("period", ""), reverse=True)
    trend_scorecards = sorted_scorecards[:periods]
    
    # Calculate trends
    if len(trend_scorecards) < 2:
        trends = {
            "message": "Insufficient data for trend analysis. Need at least 2 periods.",
            "periods": trend_scorecards,
        }
    else:
        # Calculate trend direction for each metric
        latest = trend_scorecards[0]
        previous = trend_scorecards[1] if len(trend_scorecards) > 1 else trend_scorecards[0]
        
        effectiveness_trend = latest.get("effectiveness_index", 0) - previous.get("effectiveness_index", 0)
        cost_trend = latest.get("cost_impact_score", 0) - previous.get("cost_impact_score", 0)
        
        trends = {
            "periods": trend_scorecards,
            "trend_direction": {
                "effectiveness_index": "UP" if effectiveness_trend > 0 else "DOWN" if effectiveness_trend < 0 else "STABLE",
                "cost_impact_score": "UP" if cost_trend > 0 else "DOWN" if cost_trend < 0 else "STABLE",
                "effectiveness_change": effectiveness_trend,
                "cost_change": cost_trend,
            },
        }
    
    return trends


@router.post("/scorecards/compare")
async def compare_scorecards(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    policy_ids: list[UUID] = Body(..., description="List of policy IDs to compare"),
    period: str | None = Query(None, description="Period to compare (defaults to latest)"),
):
    """Compare scorecards across multiple policies - File storage only"""
    tenant_id = current_user.tenant_id
    
    # Get scorecards for the specified policies
    scorecards = list_scorecards(
        tenant_id=tenant_id,
        policy_ids=policy_ids,
        period=period,
    )
    
    if not scorecards:
        if period:
            raise HTTPException(
                status_code=404,
                detail=f"No scorecards found for the specified policies and period {period}. Generate scorecards first."
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="No scorecards found for the specified policies. Generate scorecards first."
            )
    
    # Group scorecards by policy ID
    scorecards_by_policy = {}
    for scorecard in scorecards:
        policy_id = scorecard["policy_id"]
        if policy_id not in scorecards_by_policy:
            scorecards_by_policy[policy_id] = []
        scorecards_by_policy[policy_id].append(scorecard)
    
    # Get latest scorecard for each policy if period not specified
    if period is None:
        latest_scorecards = {}
        for policy_id, policy_scorecards in scorecards_by_policy.items():
            # Sort by period (most recent first) and take the first one
            sorted_scorecards = sorted(policy_scorecards, key=lambda x: x.get("period", ""), reverse=True)
            if sorted_scorecards:
                latest_scorecards[policy_id] = sorted_scorecards[0]
        scorecards = list(latest_scorecards.values())
    
    # Calculate comparison metrics
    comparison = {
        "policies": scorecards,
        "count": len(scorecards),
        "period": period or "latest",
        "metrics": {
            "avg_effectiveness_index": sum(s.get("effectiveness_index", 0) for s in scorecards) / len(scorecards) if scorecards else 0,
            "max_effectiveness_index": max((s.get("effectiveness_index", 0) for s in scorecards), default=0),
            "min_effectiveness_index": min((s.get("effectiveness_index", 0) for s in scorecards), default=0),
            "avg_cost_impact_score": sum(s.get("cost_impact_score", 0) for s in scorecards) / len(scorecards) if scorecards else 0,
            "avg_behavioral_risk_score": sum(s.get("behavioral_risk_score", 0) for s in scorecards) / len(scorecards) if scorecards else 0,
            "avg_access_impact_score": sum(s.get("access_impact_score", 0) for s in scorecards) / len(scorecards) if scorecards else 0,
        },
    }
    
    return comparison

