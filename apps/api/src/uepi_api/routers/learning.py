"""Learning endpoints - File storage only"""
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user, require_role
from uepi_api.storage_learning import (
    create_elasticity_model,
    get_elasticity_model,
    list_elasticity_models,
    get_latest_elasticity_model,
    update_elasticity_model,
    get_accuracy_history,
    list_accuracy_records,
)
from uepi_api.learning_loop import (
    learn_from_observation,
    get_prediction_accuracy_summary,
    update_elasticity_from_observations,
)
from uepi_api.storage_observations import get_observations_for_policy


router = APIRouter()


class ElasticityModelCreate(BaseModel):
    """Elasticity model creation model"""
    policy_type: str
    service_category: Optional[str] = None
    elasticity_coefficients: dict = {}
    version: str = "v1.0"
    confidence: float = 0.0
    training_metrics: dict = {}
    metadata: dict = {}


class ElasticityModelResponse(BaseModel):
    """Elasticity model response model"""
    model_id: str
    tenant_id: UUID
    version: str
    policy_type: str
    service_category: Optional[str]
    elasticity_coefficients: dict
    learned_from_observations: List[str]
    confidence: float
    training_metrics: dict
    created_at: str
    updated_at: str
    metadata: dict


class AccuracyRecordResponse(BaseModel):
    """Accuracy record response model"""
    accuracy_id: str
    tenant_id: UUID
    policy_id: str
    observation_id: str
    prediction_id: Optional[str]
    elasticity_model_id: Optional[str]
    predicted_effect_size: float
    observed_effect_size: float
    prediction_error: float
    prediction_error_pct: float
    prediction_accuracy_pct: float
    metrics: dict
    recorded_at: str
    metadata: dict


class AccuracySummaryResponse(BaseModel):
    """Accuracy summary response model"""
    policy_id: str
    total_observations: int
    average_accuracy_pct: Optional[float]
    average_mae: Optional[float]
    average_rmse: Optional[float]
    records: List[dict]


@router.get("/learning/accuracy/{policy_id}", response_model=AccuracySummaryResponse)
async def get_prediction_accuracy_route(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get prediction accuracy summary for a policy"""
    # Convert string ID to UUID if needed
    try:
        policy_id_uuid = UUID(policy_id) if isinstance(policy_id, str) and len(policy_id) == 36 and policy_id.count('-') == 4 else policy_id
    except (ValueError, AttributeError):
        # Not a UUID, use as string - need to find the policy first to get its UUID
        from uepi_api.storage_policies import list_policies
        all_policies = list_policies(current_user.tenant_id)
        policy = next((p for p in all_policies if str(p.get('id', p.get('policy_id'))) == policy_id), None)
        if policy:
            # Use the policy's actual ID (might be UUID or string)
            actual_id = policy.get('id') or policy.get('policy_id')
            try:
                policy_id_uuid = UUID(actual_id) if isinstance(actual_id, str) and len(actual_id) == 36 else actual_id
            except (ValueError, AttributeError):
                policy_id_uuid = actual_id
        else:
            raise HTTPException(status_code=404, detail="Policy not found")
    
    summary = get_prediction_accuracy_summary(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id_uuid,
    )
    return AccuracySummaryResponse(**summary)


@router.get("/learning/accuracy/history/{policy_id}", response_model=List[AccuracyRecordResponse])
async def get_accuracy_history_route(
    policy_id: str,  # Accept both UUID and string IDs
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(100, ge=1, le=1000),
):
    """Get accuracy history for a policy"""
    # Convert string ID to UUID if needed
    try:
        policy_id_uuid = UUID(policy_id) if isinstance(policy_id, str) and len(policy_id) == 36 and policy_id.count('-') == 4 else policy_id
    except (ValueError, AttributeError):
        # Not a UUID, find policy to get its ID
        from uepi_api.storage_policies import list_policies
        all_policies = list_policies(current_user.tenant_id)
        policy = next((p for p in all_policies if str(p.get('id', p.get('policy_id'))) == policy_id), None)
        if policy:
            actual_id = policy.get('id') or policy.get('policy_id')
            try:
                policy_id_uuid = UUID(actual_id) if isinstance(actual_id, str) and len(actual_id) == 36 else actual_id
            except (ValueError, AttributeError):
                policy_id_uuid = actual_id
        else:
            raise HTTPException(status_code=404, detail="Policy not found")
    records = get_accuracy_history(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    # Apply limit
    records = records[:limit]
    return [AccuracyRecordResponse(**r) for r in records]


@router.post("/learning/update-elasticity", response_model=ElasticityModelResponse, status_code=status.HTTP_201_CREATED)
async def update_elasticity_model_route(
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN", "UM_LEADER"))],
    policy_id: UUID = Query(..., description="Policy ID"),
    policy_type: str = Query(..., description="Policy type"),
    service_category: Optional[str] = Query(None, description="Service category"),
):
    """Update elasticity model from observations for a policy"""
    # Get all observations for the policy
    observations = get_observations_for_policy(
        tenant_id=current_user.tenant_id,
        policy_id=policy_id,
    )
    
    if not observations:
        raise HTTPException(
            status_code=400,
            detail="No observations found for this policy. Cannot update elasticity model."
        )
    
    # Update elasticity model
    elasticity_model = update_elasticity_from_observations(
        tenant_id=current_user.tenant_id,
        policy_type=policy_type,
        observations=observations,
        service_category=service_category,
    )
    
    if not elasticity_model:
        raise HTTPException(
            status_code=400,
            detail="Failed to update elasticity model. Check that observations have predicted comparisons."
        )
    
    return ElasticityModelResponse(**elasticity_model)


@router.get("/learning/elasticity-models", response_model=List[ElasticityModelResponse])
async def list_elasticity_models_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    policy_type: Optional[str] = Query(None),
    service_category: Optional[str] = Query(None),
):
    """List elasticity models for the current tenant"""
    models = list_elasticity_models(
        tenant_id=current_user.tenant_id,
        policy_type=policy_type,
        service_category=service_category,
    )
    return [ElasticityModelResponse(**m) for m in models]


@router.get("/learning/elasticity-models/{model_id}", response_model=ElasticityModelResponse)
async def get_elasticity_model_route(
    model_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get an elasticity model by ID"""
    model = get_elasticity_model(tenant_id=current_user.tenant_id, model_id=model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Elasticity model not found")
    
    return ElasticityModelResponse(**model)


@router.post("/learning/learn-from-observation")
async def learn_from_observation_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    observation_id: str = Query(..., description="Observation ID"),
):
    """Trigger learning from an observation
    
    This endpoint:
    1. Records prediction accuracy
    2. Updates elasticity models if enough observations are available
    """
    result = learn_from_observation(
        tenant_id=current_user.tenant_id,
        observation_id=observation_id,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to learn from observation")
        )
    
    return result
