"""Policy routes using file storage only (no database)"""
from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_policies import (
    list_policies,
    get_policy,
    create_policy,
    update_policy,
    delete_policy,
)

router = APIRouter()


class PolicyCreate(BaseModel):
    name: str
    description: str | None = None
    status: str = "draft"
    policy_type: str
    effective_date: str | None = None
    expiration_date: str | None = None
    metadata: dict = {}
    logic: dict = {}


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    policy_type: str | None = None
    effective_date: str | None = None
    expiration_date: str | None = None
    metadata: dict | None = None
    logic: dict | None = None


@router.get("/policies", response_model=List[dict])
async def get_policies(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """List all policies for the current tenant"""
    policies = list_policies(current_user.tenant_id)
    return policies


@router.get("/policies/{policy_id}", response_model=dict)
async def get_policy_by_id(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a policy by ID"""
    # Try to convert to UUID if it's a UUID string, otherwise use as-is
    try:
        policy_id_uuid = UUID(policy_id)
        policy = get_policy(policy_id_uuid, current_user.tenant_id)
    except ValueError:
        # Not a UUID, try as string ID
        from uepi_api.storage_policies import list_policies
        all_policies = list_policies(current_user.tenant_id)
        policy = None
        for p in all_policies:
            if str(p.get('policy_id', '')) == policy_id:
                policy = p
                break
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/policies", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_policy_route(
    policy_data: PolicyCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new policy"""
    policy = create_policy(current_user.tenant_id, policy_data.model_dump())
    return policy


@router.put("/policies/{policy_id}", response_model=dict)
async def update_policy_route(
    policy_id: str,  # Accept both UUID and string IDs
    policy_data: PolicyUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a policy"""
    # Try to convert to UUID if it's a UUID string, otherwise use as-is
    try:
        policy_id_uuid = UUID(policy_id)
        update_dict = {k: v for k, v in policy_data.model_dump().items() if v is not None}
        policy = update_policy(policy_id_uuid, current_user.tenant_id, update_dict)
    except ValueError:
        # Not a UUID, find by string ID first
        from uepi_api.storage_policies import list_policies, get_policy
        all_policies = list_policies(current_user.tenant_id)
        found_policy = None
        for p in all_policies:
            if str(p.get('policy_id', '')) == policy_id:
                found_policy = p
                break
        if not found_policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        # For string IDs, we need to update differently - use the policy's actual UUID if it has one
        actual_id = found_policy.get('policy_id')
        if isinstance(actual_id, str) and len(actual_id) == 36:  # UUID string
            policy_id_uuid = UUID(actual_id)
        else:
            # Can't update by string ID directly, return error or update via list
            raise HTTPException(status_code=400, detail="Cannot update policy with string ID. Please use UUID.")
        update_dict = {k: v for k, v in policy_data.model_dump().items() if v is not None}
        policy = update_policy(policy_id_uuid, current_user.tenant_id, update_dict)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy_route(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete a policy"""
    # Try to convert to UUID if it's a UUID string, otherwise use as-is
    try:
        policy_id_uuid = UUID(policy_id)
        deleted = delete_policy(policy_id_uuid, current_user.tenant_id)
    except ValueError:
        # Not a UUID, find by string ID first
        from uepi_api.storage_policies import list_policies
        all_policies = list_policies(current_user.tenant_id)
        found_policy = None
        for p in all_policies:
            if str(p.get('policy_id', '')) == policy_id:
                found_policy = p
                break
        if not found_policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        # Get the actual UUID from the policy
        actual_id = found_policy.get('policy_id')
        if isinstance(actual_id, str) and len(actual_id) == 36:  # UUID string
            policy_id_uuid = UUID(actual_id)
            deleted = delete_policy(policy_id_uuid, current_user.tenant_id)
        else:
            raise HTTPException(status_code=400, detail="Cannot delete policy with string ID. Please use UUID.")
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")


@router.get("/policies/{policy_id}/predicted-impact")
async def get_policy_predicted_impact(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get predicted impact for a policy - returns 404 if not found, empty dict if exists but no metrics"""
    """Get predicted impact for a policy (Stage 3.5) - File storage only"""
    from uepi_api.routers.policy_predicted_impact import get_predicted_impact_from_metadata
    from uepi_api.storage_policies import get_policy
    from uepi_api.storage_file import BASE_PATH
    import json
    from pathlib import Path
    
    # OPTIMIZATION: Try to load policy file directly first (faster for string IDs)
    # This avoids loading all policies when we have a string ID like "ST_BIOLOGIC_006"
    policy_data = None
    
    # First, try direct file lookup for string IDs (e.g., data/policy_ST_BIOLOGIC_006.json)
    try:
        policy_file = BASE_PATH / f"policy_{policy_id}.json"
        if policy_file.exists():
            with open(policy_file, 'r') as f:
                policy_data = json.load(f)
    except Exception:
        pass  # File doesn't exist or can't be read, continue with other methods
    
    # If direct file lookup failed, try UUID lookup (fast for UUIDs)
    if not policy_data:
        try:
            policy_id_uuid = UUID(policy_id)
            policy_data = get_policy(policy_id_uuid, current_user.tenant_id)
        except (ValueError, AttributeError):
            # Not a UUID, will try get_policy with string ID below
            pass
    
    # Last resort: use get_policy with string ID (this will load all policies, but only if needed)
    if not policy_data:
        policy_data = get_policy(policy_id, current_user.tenant_id)
    
    if not policy_data:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Extract predicted impact from policy data (can be in metadata or at root)
    predicted_impact = policy_data.get("predicted_impact")
    if not predicted_impact:
        # Try in metadata if it exists
        metadata = policy_data.get("metadata", {})
        predicted_impact = get_predicted_impact_from_metadata(metadata)
    
    # Fallback: Check separate predicted impact file in data/predicted_impacts/
    if not predicted_impact:
        try:
            predicted_impacts_dir = BASE_PATH / "predicted_impacts" / str(current_user.tenant_id)
            # Try both UUID and string ID as filename
            for pid in [policy_id, str(policy_data.get('policy_id', '')), str(policy_data.get('id', ''))]:
                if not pid:
                    continue
                impact_file = predicted_impacts_dir / f"{pid}.json"
                if impact_file.exists():
                    with open(impact_file, 'r') as f:
                        predicted_impact = json.load(f)
                    break
        except Exception:
            # If file read fails, continue without it
            pass
    
    if not predicted_impact:
        # Return 404 - frontend expects this for missing data
        raise HTTPException(status_code=404, detail="Predicted impact not found for this policy")
    
    # Ensure metrics structure exists - if predicted_impact is the metrics itself, wrap it
    if isinstance(predicted_impact, dict):
        if "metrics" not in predicted_impact:
            # Check if it's already a metrics object
            if any(key in predicted_impact for key in ["utilization_change_per_1k", "cost_change_pmpm", "cost_change_total"]):
                predicted_impact = {"metrics": predicted_impact, "predicted_at": predicted_impact.get("predicted_at", ""), "policy_id": policy_id}
    
    return predicted_impact


@router.post("/policies/{policy_id}/refresh-prediction")
async def refresh_stale_prediction(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Item 3: Refresh stale prediction for a policy (Continuous Learning Cycle)"""
    from uepi_api.routers.policy_predicted_impact import (
        generate_predicted_impact_for_policy,
        store_predicted_impact_in_metadata,
    )
    
    # Get policy data - handle both UUID and string IDs
    try:
        policy_id_uuid = UUID(policy_id)
        policy_data = get_policy(policy_id_uuid, current_user.tenant_id)
        actual_policy_id = policy_id_uuid
    except ValueError:
        # Not a UUID, search by string ID
        from uepi_api.storage_policies import list_policies
        all_policies = list_policies(current_user.tenant_id)
        policy_data = None
        for p in all_policies:
            if str(p.get('policy_id', '')) == policy_id:
                policy_data = p
                # Use the policy's actual ID (might be UUID or string)
                actual_policy_id = p.get('policy_id')
                break
    
    if not policy_data:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Check if prediction is stale
    metadata = policy_data.get("metadata", {})
    if not metadata.get("prediction_stale"):
        return {
            "message": "Prediction is up to date",
            "policy_id": str(policy_id),
            "refreshed": False,
        }
    
    # Regenerate predicted impact with latest elasticity models
    policy_levers = policy_data.get("logic", {}).get("policy_levers", []) or policy_data.get("policy_levers", [])
    policy_scope = policy_data.get("scope", {})
    
    # Item 8: Load baseline metrics if available
    baseline_metrics = None
    try:
        from uepi_api.storage_baselines import get_latest_baseline
        baseline = get_latest_baseline(current_user.tenant_id)
        if baseline:
            baseline_metrics = baseline.get("baseline_metrics", {}) or baseline.get("metrics", {})
    except Exception as e:
        print(f"Warning: Could not load baseline metrics: {e}")
    
    # Use actual_policy_id (which might be UUID or string)
    try:
        policy_id_for_generation = UUID(actual_policy_id) if isinstance(actual_policy_id, str) and len(actual_policy_id) == 36 else actual_policy_id
    except (ValueError, AttributeError):
        policy_id_for_generation = actual_policy_id
    
    predicted_impact = generate_predicted_impact_for_policy(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id_for_generation,
        policy_levers=policy_levers,
        policy_scope=policy_scope,
        baseline_metrics=baseline_metrics,
    )
    
    # Store updated predicted impact
    updated_metadata = store_predicted_impact_in_metadata(metadata, predicted_impact)
    updated_metadata["prediction_stale"] = False
    updated_metadata["prediction_refreshed_at"] = datetime.utcnow().isoformat()
    
    # Update policy - try UUID first, then string
    from datetime import datetime
    try:
        update_policy_id = UUID(actual_policy_id) if isinstance(actual_policy_id, str) and len(actual_policy_id) == 36 else actual_policy_id
        update_policy(update_policy_id, current_user.tenant_id, {"metadata": updated_metadata})
    except (ValueError, AttributeError):
        # Can't update with string ID, skip update
        pass
    
    return {
        "message": "Prediction refreshed successfully",
        "policy_id": str(actual_policy_id),
        "refreshed": True,
        "predicted_impact": predicted_impact.model_dump(mode='json'),
    }


@router.post("/policies/{policy_id}/predicted-impact")
async def generate_policy_predicted_impact(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Generate predicted impact for a policy (Stage 3.5) - File storage only"""
    # Check if scipy is available
    try:
        import scipy
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="scipy library is required for predicted impact generation. Please install it: pip install scipy"
        )
    from uepi_api.routers.policy_predicted_impact import (
        generate_predicted_impact_for_policy,
        store_predicted_impact_in_metadata,
    )
    
    # Get policy data - handle both UUID and string IDs
    try:
        policy_id_uuid = UUID(policy_id)
        policy_data = get_policy(policy_id_uuid, current_user.tenant_id)
    except ValueError:
        # Not a UUID, search by string ID
        from uepi_api.storage_policies import list_policies
        all_policies = list_policies(current_user.tenant_id)
        policy_data = None
        for p in all_policies:
            if str(p.get('policy_id', '')) == policy_id:
                policy_data = p
                break
    
    if not policy_data:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Extract policy levers from policy data
    policy_levers = policy_data.get("policy_levers", [])
    if not policy_levers:
        # Try in metadata/logic
        metadata = policy_data.get("metadata", {})
        logic = policy_data.get("logic", {}) or policy_data.get("policy_logic", {})
        policy_levers = (
            metadata.get("policy_levers", []) or 
            logic.get("policy_levers", []) or 
            logic.get("levers", [])  # Also check "levers" field
        )
    
    if not policy_levers:
        raise HTTPException(
            status_code=400,
            detail="Policy does not have policy levers. Predicted impact requires policy levers to be defined."
        )
    
    policy_scope = policy_data.get("scope") or policy_data.get("metadata", {}).get("scope")
    
    # Load baseline metrics for better predictions
    # Use policy-specific baseline first (uses historical data before activation), then fall back to general baseline
    baseline_metrics_for_prediction = None
    try:
        from uepi_api.storage_baselines import get_latest_baseline
        from uuid import UUID
        
        # Try to convert policy_id to UUID for baseline lookup
        policy_id_uuid = None
        try:
            if isinstance(policy_id, str) and len(policy_id) == 36:
                policy_id_uuid = UUID(policy_id)
            elif isinstance(policy_id, UUID):
                policy_id_uuid = policy_id
        except (ValueError, AttributeError):
            pass
        
        # Try policy-specific baseline first (uses historical data before activation)
        latest_baseline = None
        if policy_id_uuid:
            latest_baseline = get_latest_baseline(current_user.tenant_id, policy_id=policy_id_uuid)
        
        # Fall back to general baseline if no policy-specific baseline exists
        if not latest_baseline:
            latest_baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
        
        if latest_baseline:
            baseline_metrics_dict = latest_baseline.get("baseline_metrics", {}) or latest_baseline.get("metrics", {})
            if baseline_metrics_dict:
                # Map baseline metric dictionary names to what predicted impact expects
                # Use policy-specific metrics (util_rate_target_per_1000_mm) if available, otherwise general (util_rate_total_per_1000_mm)
                baseline_metrics_for_prediction = {
                    "utilization_per_1k": baseline_metrics_dict.get("util_rate_target_per_1000_mm") or baseline_metrics_dict.get("util_rate_total_per_1000_mm") or baseline_metrics_dict.get("utilization_per_1k"),
                    "cost_pmpm": baseline_metrics_dict.get("allowed_pmpm_target") or baseline_metrics_dict.get("allowed_pmpm_total") or baseline_metrics_dict.get("cost_pmpm"),
                    "member_count": int(baseline_metrics_dict.get("unique_members", 0)) or int(baseline_metrics_dict.get("member_months", 10000) / 12),
                    "member_months": baseline_metrics_dict.get("member_months", 10000),
                }
                # Remove None values and zeros
                baseline_metrics_for_prediction = {k: v for k, v in baseline_metrics_for_prediction.items() if v is not None and v != 0}
                if not baseline_metrics_for_prediction:
                    baseline_metrics_for_prediction = None
    except Exception as baseline_error:
        print(f"WARNING: Could not load baseline metrics for predicted impact: {baseline_error}")
        baseline_metrics_for_prediction = None
    
    # Generate predicted impact (now with baseline metrics if available)
    predicted_impact = generate_predicted_impact_for_policy(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
        policy_levers=policy_levers,
        policy_scope=policy_scope,
        baseline_metrics=baseline_metrics_for_prediction,
    )
    
    # Convert to dict and include enhanced data (confidence intervals, ramp-up)
    predicted_impact_dict = predicted_impact.model_dump(mode='json')
    
    # Add enhanced data if available
    if hasattr(predicted_impact, '_enhanced_data'):
        predicted_impact_dict.update(predicted_impact._enhanced_data)
    
    # Store predicted impact in policy data
    policy_data["predicted_impact"] = predicted_impact_dict
    
    # Also store in metadata if it exists
    if "metadata" in policy_data:
        policy_data["metadata"] = store_predicted_impact_in_metadata(
            policy_data["metadata"],
            predicted_impact
        )
    
    # Update policy with predicted impact
    update_policy(policy_id, current_user.tenant_id, policy_data)
    
    # Return the predicted impact
    return predicted_impact.model_dump(mode='json')


@router.post("/policies/generate-predicted-impact")
async def generate_all_policies_predicted_impact(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    force: bool = False,
):
    """Generate predicted impact for all policies that don't have it (Stage 3.5) - File storage only
    
    Args:
        force: If True, regenerate predicted impact even if it already exists
    """
    from uepi_api.routers.policy_predicted_impact import (
        generate_predicted_impact_for_policy,
        store_predicted_impact_in_metadata,
        get_predicted_impact_from_metadata,
    )
    
    results = {
        "total_policies": 0,
        "generated": 0,
        "skipped": 0,
        "errors": 0,
        "details": [],
    }
    
    # Get all policies for the tenant
    policies = list_policies(current_user.tenant_id)
    results["total_policies"] = len(policies)
    
    for policy_data in policies:
        try:
            # Handle both UUID and string policy IDs
            policy_id_raw = policy_data.get("id") or policy_data.get("policy_id")
            try:
                policy_id = UUID(policy_id_raw)
            except (ValueError, TypeError):
                # Not a UUID, use as string ID
                policy_id = policy_id_raw
            policy_name = policy_data.get("name", policy_data.get("policy_name", "Unknown"))
            
            # Check if predicted impact already exists AND is complete/valid
            existing_predicted_impact = policy_data.get("predicted_impact")
            if not existing_predicted_impact:
                metadata = policy_data.get("metadata", {})
                existing_predicted_impact = get_predicted_impact_from_metadata(metadata)
            
            # Validate predicted impact is complete (has metrics with valid values)
            # Only skip if NOT forcing and impact is complete with reasonable confidence
            is_complete = False
            if existing_predicted_impact and not force:
                metrics = existing_predicted_impact.get("metrics", {})
                if metrics:
                    # Check if key metrics exist and are not None/null
                    utilization = metrics.get("utilization_change_per_1k")
                    cost = metrics.get("cost_change_pmpm")
                    confidence = metrics.get("confidence_score", 0)
                    
                    # Consider complete if it has valid values AND reasonable confidence
                    # Require confidence > 50% to ensure it's actually a valid prediction
                    # (very low confidence suggests incomplete generation or error)
                    is_complete = (
                        utilization is not None and
                        cost is not None and
                        confidence > 50.0  # Require reasonable confidence (not just > 1%)
                    )
            
            if existing_predicted_impact and is_complete and not force:
                results["skipped"] += 1
                results["details"].append({
                    "policy_id": str(policy_id),
                    "policy_name": policy_name,
                    "status": "skipped",
                    "reason": f"Predicted impact already exists (confidence: {existing_predicted_impact.get('metrics', {}).get('confidence_score', 0):.1f}%)",
                })
                continue
            
            # Extract policy levers
            policy_levers = policy_data.get("policy_levers", [])
            if not policy_levers:
                metadata = policy_data.get("metadata", {})
                logic = policy_data.get("logic", {}) or policy_data.get("policy_logic", {})
                policy_levers = (
                    metadata.get("policy_levers", []) or 
                    logic.get("policy_levers", []) or 
                    logic.get("levers", [])  # Also check "levers" field
                )
            
            if not policy_levers:
                results["skipped"] += 1
                results["details"].append({
                    "policy_id": str(policy_id),
                    "policy_name": policy_name,
                    "status": "skipped",
                    "reason": "Policy does not have policy levers",
                })
                continue
            
            policy_scope = policy_data.get("scope") or policy_data.get("metadata", {}).get("scope")
            
            # Load baseline metrics for better predictions
            baseline_metrics_for_prediction = None
            try:
                from uepi_api.storage_baselines import get_latest_baseline
                latest_baseline = get_latest_baseline(current_user.tenant_id)
                if latest_baseline:
                    baseline_metrics_dict = latest_baseline.get("baseline_metrics", {}) or latest_baseline.get("metrics", {})
                    if baseline_metrics_dict:
                        # Map baseline metric dictionary names to what predicted impact expects
                        baseline_metrics_for_prediction = {
                            # Map metric dictionary names to predicted impact expected names
                            "utilization_per_1k": baseline_metrics_dict.get("util_rate_total_per_1000_mm") or baseline_metrics_dict.get("utilization_per_1k"),
                            "cost_pmpm": baseline_metrics_dict.get("allowed_pmpm_total") or baseline_metrics_dict.get("cost_pmpm"),
                            "member_count": int(baseline_metrics_dict.get("member_months", 10000) / 12),  # Approximate from member-months
                            "member_months": baseline_metrics_dict.get("member_months", 10000),
                        }
                        # Remove None values
                        baseline_metrics_for_prediction = {k: v for k, v in baseline_metrics_for_prediction.items() if v is not None}
            except Exception as baseline_error:
                print(f"WARNING: Could not load baseline metrics for predicted impact: {baseline_error}")
                baseline_metrics_for_prediction = None
            
            # Generate predicted impact (now with baseline metrics if available)
            # Handle both UUID and string IDs for generation
            try:
                policy_id_for_generation = UUID(policy_id) if isinstance(policy_id, str) and len(policy_id) == 36 else policy_id
            except (ValueError, AttributeError):
                policy_id_for_generation = policy_id
            
            predicted_impact = generate_predicted_impact_for_policy(
                tenant_id=current_user.tenant_id,
                policy_id=policy_id_for_generation,
                policy_levers=policy_levers,
                policy_scope=policy_scope,
                baseline_metrics=baseline_metrics_for_prediction,
            )
            
            # Store predicted impact - if policy_id was a string, update it in the dict
            predicted_impact_dict = predicted_impact.model_dump(mode='json')
            # If we have a string policy_id, replace the UUID with the string
            if isinstance(policy_id, str) and not (len(policy_id) == 36 and policy_id.count('-') == 4):
                predicted_impact_dict['policy_id'] = policy_id
            
            policy_data["predicted_impact"] = predicted_impact_dict
            if "metadata" in policy_data:
                policy_data["metadata"] = store_predicted_impact_in_metadata(
                    policy_data["metadata"],
                    predicted_impact
                )
                # Also update policy_id in metadata if it's a string
                if isinstance(policy_id, str) and not (len(policy_id) == 36 and policy_id.count('-') == 4):
                    if "predicted_impact" in policy_data["metadata"]:
                        policy_data["metadata"]["predicted_impact"]["policy_id"] = policy_id
            
            # Update policy - handle both UUID and string IDs
            try:
                update_policy_id = UUID(policy_id) if isinstance(policy_id, str) and len(policy_id) == 36 else policy_id
                update_policy(update_policy_id, current_user.tenant_id, policy_data)
            except (ValueError, AttributeError):
                # Can't update with string ID directly, but we've already stored it in policy_data
                # The policy will be saved when it's next loaded
                pass
            
            results["generated"] += 1
            results["details"].append({
                "policy_id": str(policy_id),
                "policy_name": policy_name,
                "status": "generated",
                "confidence_score": predicted_impact.metrics.confidence_score,
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"ERROR generating predicted impact for policy {policy_data.get('id')}: {e}")
            print(f"Full traceback: {error_trace}")
            
            results["errors"] += 1
            policy_id_str = str(policy_data.get("id") or policy_data.get("policy_id", "unknown"))
            results["details"].append({
                "policy_id": policy_id_str,
                "policy_name": policy_data.get("name", "Unknown"),
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            })
            continue
    
    return results

