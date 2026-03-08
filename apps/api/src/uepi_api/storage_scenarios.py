"""Scenario storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.scenario import Scenario
from uepi_common.models_enhanced import ScenarioRun, SensitivityParameter, ForecastDistribution


def _safe_uuid(value: Any) -> Optional[UUID]:
    """Safely convert value to UUID"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            return None
    return None


def create_scenario(
    tenant_id: UUID,
    scenario_data: Dict[str, Any]
) -> ScenarioRun:
    """Create a new scenario run - stored in database"""
    return _create_scenario(tenant_id, scenario_data)


def _create_scenario(
    tenant_id: UUID,
    scenario_data: Dict[str, Any]
) -> ScenarioRun:
    """Create scenario in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate scenario_id if not provided
        scenario_id = str(_safe_uuid(scenario_data.get("scenario_id")) or uuid4())
        
        # Parse policy_id if provided
        policy_id = None
        if scenario_data.get("policy_id"):
            policy_id = UUID(scenario_data["policy_id"]) if isinstance(scenario_data["policy_id"], str) else scenario_data["policy_id"]
        
        # Create scenario in database
        scenario = Scenario(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            name=scenario_data.get("scenario_name", scenario_data.get("name", "")),
            description=scenario_data.get("description"),
            policy_id=policy_id,
            assumptions_json={
                "parameters": scenario_data.get("parameters", {}),
                "sensitivity_parameters": scenario_data.get("sensitivity_parameters", []),
            },
            results_json=scenario_data.get("results", {}),
            scenario_type=scenario_data.get("scenario_type"),
            status=scenario_data.get("status", "DRAFT"),
            completed_at=datetime.fromisoformat(scenario_data["completed_at"].replace("Z", "+00:00")) if isinstance(scenario_data.get("completed_at"), str) else scenario_data.get("completed_at"),
        )
        
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        
        # Return Pydantic model for compatibility
        assumptions = scenario.assumptions_json if scenario.assumptions_json else {}
        parameters = assumptions.get("parameters", {})
        sensitivity_params = [SensitivityParameter(**sp) for sp in assumptions.get("sensitivity_parameters", [])]
        
        return ScenarioRun(
            scenario_id=UUID(scenario_id),
            scenario_name=scenario.name,
            parameters=parameters,
            sensitivity_parameters=sensitivity_params,
            results=scenario.results_json if scenario.results_json else {},
            created_at=scenario.created_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create scenario: {e}")
    finally:
        db.close()


def get_scenario(
    tenant_id: UUID,
    scenario_id: UUID
) -> Optional[ScenarioRun]:
    """Get a scenario by ID - from database"""
    return _get_scenario(tenant_id, scenario_id)


def _get_scenario(
    tenant_id: UUID,
    scenario_id: UUID
) -> Optional[ScenarioRun]:
    """Get scenario from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        scenario = db.query(Scenario).filter(
            Scenario.tenant_id == tenant_id,
            Scenario.scenario_id == str(scenario_id)
        ).first()
        
        if not scenario:
            return None
        
        # Convert to Pydantic model
        assumptions = scenario.assumptions_json if scenario.assumptions_json else {}
        parameters = assumptions.get("parameters", {})
        sensitivity_params = [SensitivityParameter(**sp) for sp in assumptions.get("sensitivity_parameters", [])]
        
        return ScenarioRun(
            scenario_id=UUID(scenario.scenario_id),
            scenario_name=scenario.name,
            parameters=parameters,
            sensitivity_parameters=sensitivity_params,
            results=scenario.results_json if scenario.results_json else {},
            created_at=scenario.created_at,
        )
        
    except Exception as e:
        print(f"ERROR get_scenario (DB): {e}")
        return None
    finally:
        db.close()


def list_scenarios(
    tenant_id: UUID,
    scenario_name: Optional[str] = None,
    policy_id: Optional[UUID] = None
) -> List[ScenarioRun]:
    """List all scenarios for a tenant - from database"""
    return _list_scenarios(tenant_id, scenario_name, policy_id)


def _list_scenarios(
    tenant_id: UUID,
    scenario_name: Optional[str] = None,
    policy_id: Optional[UUID] = None
) -> List[ScenarioRun]:
    """List scenarios from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc
    
    db: Session = SessionLocal()
    try:
        query = db.query(Scenario).filter(Scenario.tenant_id == tenant_id)
        
        # Filter by scenario_name if provided
        if scenario_name:
            query = query.filter(Scenario.name == scenario_name)
        
        # Filter by policy_id if provided
        if policy_id:
            query = query.filter(Scenario.policy_id == policy_id)
        
        # Sort by created_at descending (newest first)
        scenarios = query.order_by(desc(Scenario.created_at)).all()
        
        # Convert to Pydantic models for compatibility
        result = []
        for scenario in scenarios:
            assumptions = scenario.assumptions_json if scenario.assumptions_json else {}
            parameters = assumptions.get("parameters", {})
            sensitivity_params = [SensitivityParameter(**sp) for sp in assumptions.get("sensitivity_parameters", [])]
            
            result.append(ScenarioRun(
                scenario_id=UUID(scenario.scenario_id),
                scenario_name=scenario.name,
                parameters=parameters,
                sensitivity_parameters=sensitivity_params,
                results=scenario.results_json if scenario.results_json else {},
                created_at=scenario.created_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_scenarios (DB): {e}")
        return []
    finally:
        db.close()


def update_scenario(
    tenant_id: UUID,
    scenario_id: UUID,
    updates: Dict[str, Any]
) -> Optional[ScenarioRun]:
    """Update a scenario - stored in database"""
    return _update_scenario(tenant_id, scenario_id, updates)


def _update_scenario(
    tenant_id: UUID,
    scenario_id: UUID,
    updates: Dict[str, Any]
) -> Optional[ScenarioRun]:
    """Update scenario in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        scenario = db.query(Scenario).filter(
            Scenario.tenant_id == tenant_id,
            Scenario.scenario_id == str(scenario_id)
        ).first()
        
        if not scenario:
            return None
        
        # Update fields
        if "scenario_name" in updates or "name" in updates:
            scenario.name = updates.get("scenario_name") or updates.get("name", scenario.name)
        if "description" in updates:
            scenario.description = updates.get("description")
        if "status" in updates:
            scenario.status = updates.get("status")
        if "parameters" in updates or "sensitivity_parameters" in updates:
            assumptions = scenario.assumptions_json if scenario.assumptions_json else {}
            if "parameters" in updates:
                assumptions["parameters"] = updates["parameters"]
            if "sensitivity_parameters" in updates:
                assumptions["sensitivity_parameters"] = updates["sensitivity_parameters"]
            scenario.assumptions_json = assumptions
        if "results" in updates:
            scenario.results_json = updates["results"]
        if "completed_at" in updates:
            completed_at = updates["completed_at"]
            if isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            scenario.completed_at = completed_at
        
        db.commit()
        db.refresh(scenario)
        
        # Return Pydantic model
        assumptions = scenario.assumptions_json if scenario.assumptions_json else {}
        parameters = assumptions.get("parameters", {})
        sensitivity_params = [SensitivityParameter(**sp) for sp in assumptions.get("sensitivity_parameters", [])]
        
        return ScenarioRun(
            scenario_id=UUID(scenario.scenario_id),
            scenario_name=scenario.name,
            parameters=parameters,
            sensitivity_parameters=sensitivity_params,
            results=scenario.results_json if scenario.results_json else {},
            created_at=scenario.created_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update scenario: {e}")
    finally:
        db.close()
