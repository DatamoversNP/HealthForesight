"""Uncertainty & Risk Visualization API endpoints - Epic 4"""
from typing import Annotated, List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_forecasts import (
    create_forecast,
    get_forecast,
    list_forecasts,
)
from uepi_api.storage_scenarios import (
    create_scenario,
    get_scenario,
    list_scenarios,
    update_scenario,
)
from uepi_api.storage_risks import (
    create_or_update_risk_register,
    get_risk_register,
    list_risk_registers,
    update_risk_driver,
)

router = APIRouter()


def convert_policy_id_to_uuid(policy_id: str, tenant_id: UUID) -> UUID:
    """Convert string policy ID to UUID - optimized (no expensive lookup)"""
    # Try UUID first
    try:
        return UUID(policy_id)
    except ValueError:
        # Not a UUID - generate deterministic UUID from string ID (fast, no lookup)
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())


# Request/Response Models
class ForecastCreate(BaseModel):
    metric_name: str
    point_estimate: float
    uncertainty_range: Optional[Dict[str, Any]] = None
    confidence_interval: Optional[Dict[str, Any]] = None
    distribution_data: Optional[Dict[str, Any]] = None


class SensitivityParameterCreate(BaseModel):
    parameter_name: str
    base_value: float
    min_value: float
    max_value: float
    step_size: Optional[float] = None


class ScenarioCreate(BaseModel):
    scenario_name: str
    parameters: Dict[str, float] = {}
    sensitivity_parameters: List[SensitivityParameterCreate] = []
    results: Optional[Dict[str, Any]] = None  # Metric -> forecast data


class ScenarioUpdate(BaseModel):
    scenario_name: Optional[str] = None
    parameters: Optional[Dict[str, float]] = None
    sensitivity_parameters: Optional[List[SensitivityParameterCreate]] = None
    results: Optional[Dict[str, Any]] = None


class RiskDriverCreate(BaseModel):
    driver_name: str
    impact_score: float
    uncertainty_contribution: float
    mitigation_action: Optional[str] = None
    owner: Optional[str] = None


class RiskRegisterCreate(BaseModel):
    policy_id: str
    top_drivers: List[RiskDriverCreate]
    overall_risk_score: float


class RiskDriverUpdate(BaseModel):
    impact_score: Optional[float] = None
    uncertainty_contribution: Optional[float] = None
    mitigation_action: Optional[str] = None
    owner: Optional[str] = None


# Forecast Endpoints
@router.post("/forecasts", status_code=201)
async def create_forecast_endpoint(
    forecast_data: ForecastCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new forecast distribution"""
    try:
        forecast_dict = forecast_data.model_dump(exclude_none=True)
        forecast_dict["created_at"] = datetime.utcnow().isoformat()
        
        forecast = create_forecast(
            tenant_id=current_user.tenant_id,
            forecast_data=forecast_dict,
        )
        return forecast.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create forecast: {str(e)}")


@router.get("/forecasts")
async def list_forecasts_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    metric_name: Optional[str] = Query(None),
):
    """List all forecasts for the current tenant"""
    try:
        forecasts = list_forecasts(
            tenant_id=current_user.tenant_id,
            metric_name=metric_name,
        )
        return [f.model_dump(mode='json', exclude_none=True) for f in forecasts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list forecasts: {str(e)}")


@router.get("/forecasts/{forecast_id}")
async def get_forecast_endpoint(
    forecast_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a forecast by ID"""
    try:
        forecast_uuid = UUID(forecast_id)
        forecast = get_forecast(
            tenant_id=current_user.tenant_id,
            forecast_id=forecast_uuid,
        )
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")
        return forecast.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid forecast ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast: {str(e)}")


# Scenario Endpoints
@router.post("/scenarios", status_code=201)
async def create_scenario_endpoint(
    scenario_data: ScenarioCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new scenario run"""
    try:
        scenario_dict = scenario_data.model_dump(exclude_none=True)
        scenario_dict["created_at"] = datetime.utcnow().isoformat()
        
        scenario = create_scenario(
            tenant_id=current_user.tenant_id,
            scenario_data=scenario_dict,
        )
        return scenario.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scenario: {str(e)}")


@router.get("/scenarios")
async def list_scenarios_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    scenario_name: Optional[str] = Query(None),
):
    """List all scenarios for the current tenant"""
    try:
        scenarios = list_scenarios(
            tenant_id=current_user.tenant_id,
            scenario_name=scenario_name,
        )
        return [s.model_dump(mode='json', exclude_none=True) for s in scenarios]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")


@router.get("/scenarios/{scenario_id}")
async def get_scenario_endpoint(
    scenario_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a scenario by ID"""
    try:
        scenario_uuid = UUID(scenario_id)
        scenario = get_scenario(
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_uuid,
        )
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scenario: {str(e)}")


@router.put("/scenarios/{scenario_id}")
async def update_scenario_endpoint(
    scenario_id: str,
    scenario_data: ScenarioUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a scenario"""
    try:
        scenario_uuid = UUID(scenario_id)
        updates = scenario_data.model_dump(exclude_none=True)
        
        scenario = update_scenario(
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_uuid,
            updates=updates,
        )
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scenario: {str(e)}")


# Risk Register Endpoints
@router.post("/risks", status_code=201)
async def create_risk_register_endpoint(
    risk_data: RiskRegisterCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create or update a risk register for a policy"""
    try:
        risk_dict = risk_data.model_dump(exclude_none=True)
        risk_dict["last_updated"] = datetime.utcnow().isoformat()
        
        risk_register = create_or_update_risk_register(
            tenant_id=current_user.tenant_id,
            risk_data=risk_dict,
        )
        return risk_register.model_dump(mode='json', exclude_none=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create risk register: {str(e)}")


@router.get("/risks")
async def list_risk_registers_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=1.0),
):
    """List all risk registers for the current tenant"""
    try:
        risk_registers = list_risk_registers(
            tenant_id=current_user.tenant_id,
            min_risk_score=min_risk_score,
        )
        return [r.model_dump(mode='json', exclude_none=True) for r in risk_registers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list risk registers: {str(e)}")


@router.get("/risks/policy/{policy_id}")
async def get_risk_register_endpoint(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get risk register for a policy"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        risk_register = get_risk_register(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
        )
        if not risk_register:
            # Empty register — same shape as RiskRegister (avoids 404 noise when unseeded).
            return {
                "policy_id": str(policy_uuid),
                "top_drivers": [],
                "overall_risk_score": 0.0,
                "last_updated": datetime.utcnow().isoformat(),
            }
        return risk_register.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk register: {str(e)}")


@router.put("/risks/policy/{policy_id}/drivers/{driver_name}")
async def update_risk_driver_endpoint(
    policy_id: str,
    driver_name: str,
    driver_data: RiskDriverUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a specific risk driver in a risk register"""
    try:
        policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        updates = driver_data.model_dump(exclude_none=True)
        
        risk_register = update_risk_driver(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            driver_name=driver_name,
            updates=updates,
        )
        if not risk_register:
            raise HTTPException(status_code=404, detail="Risk register not found")
        return risk_register.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update risk driver: {str(e)}")


