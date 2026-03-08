"""Scenario Accuracy Tracking endpoints"""
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_scenario_accuracy import (
    link_scenario_to_policy,
    compute_scenario_accuracy,
    get_scenario_accuracy,
    get_scenario_links,
)

router = APIRouter()


class ScenarioLinkRequest(BaseModel):
    """Request to link scenario to policy"""
    scenario_analysis_id: UUID
    policy_id: UUID
    metadata: Optional[dict] = None


class ScenarioAccuracyRequest(BaseModel):
    """Request to compute scenario accuracy"""
    scenario_analysis_id: UUID
    observation_id: str


@router.post("/scenario-accuracy/link")
async def link_scenario_to_policy_route(
    link_request: ScenarioLinkRequest,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Link a what-if scenario to a policy implementation"""
    try:
        link_record = link_scenario_to_policy(
            tenant_id=current_user.tenant_id,
            scenario_analysis_id=link_request.scenario_analysis_id,
            policy_id=link_request.policy_id,
            metadata=link_request.metadata,
        )
        return link_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error linking scenario to policy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to link scenario: {str(e)}")


@router.post("/scenario-accuracy/compute")
async def compute_scenario_accuracy_route(
    accuracy_request: ScenarioAccuracyRequest,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Compute scenario accuracy by comparing predictions to observed outcomes"""
    try:
        accuracy_record = compute_scenario_accuracy(
            tenant_id=current_user.tenant_id,
            scenario_analysis_id=accuracy_request.scenario_analysis_id,
            observation_id=accuracy_request.observation_id,
        )
        return accuracy_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error computing scenario accuracy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to compute accuracy: {str(e)}")


@router.get("/scenario-accuracy")
async def get_scenario_accuracy_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    scenario_analysis_id: Optional[str] = Query(None, description="Filter by scenario analysis ID"),
    policy_id: Optional[str] = Query(None, description="Filter by policy ID"),
):
    """Get scenario accuracy records"""
    try:
        # Convert string IDs to UUID if needed
        scenario_analysis_id_uuid = None
        if scenario_analysis_id:
            try:
                scenario_analysis_id_uuid = UUID(scenario_analysis_id) if len(scenario_analysis_id) == 36 and scenario_analysis_id.count('-') == 4 else scenario_analysis_id
            except (ValueError, AttributeError):
                scenario_analysis_id_uuid = scenario_analysis_id
        
        policy_id_uuid = None
        if policy_id:
            try:
                policy_id_uuid = UUID(policy_id) if len(policy_id) == 36 and policy_id.count('-') == 4 else policy_id
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
                    policy_id_uuid = policy_id  # Use as-is if not found
        
        accuracy_records = get_scenario_accuracy(
            tenant_id=current_user.tenant_id,
            scenario_analysis_id=scenario_analysis_id_uuid,
            policy_id=policy_id_uuid,
        )
        return accuracy_records
    except Exception as e:
        import traceback
        print(f"Error getting scenario accuracy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get accuracy records: {str(e)}")


@router.get("/scenario-accuracy/links")
async def get_scenario_links_route(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    scenario_analysis_id: Optional[str] = Query(None, description="Filter by scenario analysis ID"),
    policy_id: Optional[str] = Query(None, description="Filter by policy ID"),
):
    """Get scenario-to-policy links"""
    try:
        # Convert string IDs to UUID if needed
        scenario_analysis_id_uuid = None
        if scenario_analysis_id:
            try:
                scenario_analysis_id_uuid = UUID(scenario_analysis_id) if len(scenario_analysis_id) == 36 and scenario_analysis_id.count('-') == 4 else scenario_analysis_id
            except (ValueError, AttributeError):
                scenario_analysis_id_uuid = scenario_analysis_id
        
        policy_id_uuid = None
        if policy_id:
            try:
                policy_id_uuid = UUID(policy_id) if len(policy_id) == 36 and policy_id.count('-') == 4 else policy_id
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
                    policy_id_uuid = policy_id  # Use as-is if not found
        
        links = get_scenario_links(
            tenant_id=current_user.tenant_id,
            scenario_analysis_id=scenario_analysis_id_uuid,
            policy_id=policy_id_uuid,
        )
        return links
    except Exception as e:
        import traceback
        print(f"Error getting scenario links: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get links: {str(e)}")
