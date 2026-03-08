"""Scenario Accuracy Tracking - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import json
from pathlib import Path

from sqlalchemy.orm import Session
from uepi_api.models.scenario import ScenarioAccuracy as ScenarioAccuracyDB, Scenario as ScenarioDB
from sqlalchemy import desc


def link_scenario_to_policy(
    tenant_id: UUID,
    scenario_analysis_id: UUID,
    policy_id: UUID,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Link a what-if scenario (SIMULATE analysis) to a policy implementation
    
    Args:
        tenant_id: Tenant ID
        scenario_analysis_id: Analysis ID of the SIMULATE analysis (scenario)
        policy_id: Policy ID that was implemented based on this scenario
        metadata: Additional metadata (e.g., implementation_date, notes)
    
    Returns:
        Link record with scenario_id, policy_id, linked_at timestamp
    """
    from uepi_api.storage_analyses import get_analysis, get_result_index
    
    scenario_analysis = get_analysis(scenario_analysis_id, tenant_id)
    if not scenario_analysis:
        raise ValueError(f"Scenario analysis {scenario_analysis_id} not found")
    
    if scenario_analysis.get("analysis_type") != "SIMULATE":
        raise ValueError(f"Analysis {scenario_analysis_id} is not a SIMULATE analysis")
    
    result_index = get_result_index(scenario_analysis_id, tenant_id, result_type="whatif_scenario")
    if not result_index:
        raise ValueError(f"Scenario result not found for analysis {scenario_analysis_id}")
    
    data_uri = result_index.get("data_uri") or ""
    scenario_result = None
    if not data_uri or data_uri.strip() == "":
        # Result stored in database (WhatIfScenarioResult)
        from uepi_api.database import SessionLocal
        from uepi_api.models.analysis import WhatIfScenarioResult
        db = SessionLocal()
        try:
            whatif_row = db.query(WhatIfScenarioResult).filter(
                WhatIfScenarioResult.analysis_id == scenario_analysis_id,
                WhatIfScenarioResult.tenant_id == tenant_id,
            ).first()
            if whatif_row and whatif_row.result_data_json:
                scenario_result = whatif_row.result_data_json
        finally:
            db.close()
        if not scenario_result:
            raise ValueError(f"Scenario result not found in database for analysis {scenario_analysis_id}")
    elif data_uri.startswith("file://"):
        file_path = Path(data_uri.replace("file://", ""))
        if file_path.exists():
            with open(file_path, 'r') as f:
                scenario_result = json.load(f)
        else:
            raise ValueError(f"Scenario result file not found: {file_path}")
    else:
        raise ValueError(f"Unsupported result URI format: {data_uri}")
    
    scenario_id = scenario_result.get("scenario_id")
    if not scenario_id:
        raise ValueError(f"Scenario result missing scenario_id")
    
    return _link_scenario_to_policy(tenant_id, scenario_analysis_id, policy_id, scenario_id, metadata)


def _link_scenario_to_policy(
    tenant_id: UUID,
    scenario_analysis_id: UUID,
    policy_id: UUID,
    scenario_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Link scenario to policy in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        from uepi_api.storage_scenarios import list_scenarios
        scenarios = list_scenarios(tenant_id, policy_id=policy_id)
        scenario_db = None
        for s in scenarios:
            if s.get("scenario_id") == scenario_id:
                scenario_db_id = UUID(s.get("id")) if isinstance(s.get("id"), str) else s.get("id")
                scenario_db = db.query(ScenarioDB).filter(ScenarioDB.id == scenario_db_id).first()
                break
        
        if not scenario_db:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        accuracy_db = db.query(ScenarioAccuracyDB).filter(
            ScenarioAccuracyDB.scenario_id == scenario_db.id
        ).first()
        
        if not accuracy_db:
            now = datetime.utcnow()
            accuracy_db = ScenarioAccuracyDB(
                tenant_id=tenant_id,
                scenario_id=scenario_db.id,
                actual_vs_predicted_json=metadata or {},
                evaluated_at=now,
                linked_policy_id=policy_id,
                linked_at=now,
                metadata_json=metadata or {},
            )
            db.add(accuracy_db)
        else:
            accuracy_db.linked_policy_id = policy_id
            accuracy_db.linked_at = datetime.utcnow()
            if metadata:
                accuracy_db.metadata_json = metadata
        
        db.commit()
        db.refresh(accuracy_db)
        
        from uepi_api.storage_analyses import update_analysis
        existing_metadata = scenario_analysis.get("metadata", {})
        existing_metadata["linked_policy_id"] = str(policy_id)
        linked_at = getattr(accuracy_db, "linked_at", None)
        existing_metadata["linked_at"] = linked_at.isoformat() if linked_at else datetime.utcnow().isoformat()
        update_analysis(scenario_analysis_id, tenant_id, {"metadata": existing_metadata})
        
        return {
            "link_id": f"{scenario_id}_{policy_id}",
            "tenant_id": str(tenant_id),
            "scenario_analysis_id": str(scenario_analysis_id),
            "scenario_id": scenario_id,
            "policy_id": str(policy_id),
            "linked_at": accuracy_db.linked_at.isoformat() if accuracy_db.linked_at else datetime.utcnow().isoformat(),
            "metadata": accuracy_db.metadata_json if accuracy_db.metadata_json else {},
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR link_scenario_to_policy (DB): {e}")
        raise ValueError(f"Failed to link scenario to policy: {e}")
    finally:
        db.close()


def compute_scenario_accuracy(
    tenant_id: UUID,
    scenario_analysis_id: UUID,
    observation_id: str,
) -> Dict[str, Any]:
    """
    Compute accuracy metrics by comparing scenario predictions to observed outcomes
    
    Args:
        tenant_id: Tenant ID
        scenario_analysis_id: Analysis ID of the SIMULATE analysis (scenario)
        observation_id: Observation ID with observed outcomes
    
    Returns:
        Accuracy metrics including prediction_error, accuracy_percentage, etc.
    """
    from uepi_api.storage_analyses import get_analysis, get_result_index
    from uepi_api.storage_observations import get_observation
    
    scenario_analysis = get_analysis(scenario_analysis_id, tenant_id)
    if not scenario_analysis:
        raise ValueError(f"Scenario analysis {scenario_analysis_id} not found")
    
    result_index = get_result_index(scenario_analysis_id, tenant_id, result_type="whatif_scenario")
    if not result_index:
        raise ValueError(f"Scenario result not found")
    
    data_uri = result_index.get("data_uri") or ""
    scenario_result = None
    if not data_uri or data_uri.strip() == "":
        # Result stored in database (WhatIfScenarioResult)
        from uepi_api.database import SessionLocal
        from uepi_api.models.analysis import WhatIfScenarioResult
        db = SessionLocal()
        try:
            whatif_row = db.query(WhatIfScenarioResult).filter(
                WhatIfScenarioResult.analysis_id == scenario_analysis_id,
                WhatIfScenarioResult.tenant_id == tenant_id,
            ).first()
            if whatif_row and whatif_row.result_data_json:
                scenario_result = whatif_row.result_data_json
        finally:
            db.close()
        if not scenario_result:
            raise ValueError(f"Scenario result not found in database for analysis {scenario_analysis_id}")
    elif data_uri.startswith("file://"):
        file_path = Path(data_uri.replace("file://", ""))
        if file_path.exists():
            with open(file_path, 'r') as f:
                scenario_result = json.load(f)
        else:
            raise ValueError(f"Scenario result file not found: {file_path}")
    else:
        raise ValueError(f"Unsupported result URI format: {data_uri}")
    
    observation = get_observation(observation_id, tenant_id)
    if not observation:
        raise ValueError(f"Observation {observation_id} not found")
    
    predicted_metrics = scenario_result.get("projected_metrics", {})
    predicted_impact = scenario_result.get("impact_metrics", {})
    predicted_percent_changes = predicted_impact.get("percent_changes", {})
    
    observed_metrics = observation.get("metrics", {})
    observed_comparisons = observation.get("comparisons", {})
    observed_vs_baseline = observed_comparisons.get("vs_baseline", {})
    
    accuracy_metrics = {}
    
    predicted_util_pct = predicted_percent_changes.get("utilization_per_1k", 0)
    observed_util_pct = observed_vs_baseline.get("utilization_change_pct", 0)
    if predicted_util_pct != 0:
        util_error = observed_util_pct - predicted_util_pct
        util_accuracy_pct = max(0, 100 - abs(util_error / predicted_util_pct * 100)) if predicted_util_pct != 0 else 0
    else:
        util_error = observed_util_pct
        util_accuracy_pct = 100 if observed_util_pct == 0 else 0
    
    predicted_cost_pct = predicted_percent_changes.get("allowed_pmpm", 0)
    observed_cost_pct = observed_vs_baseline.get("cost_change_pct", 0)
    if predicted_cost_pct != 0:
        cost_error = observed_cost_pct - predicted_cost_pct
        cost_accuracy_pct = max(0, 100 - abs(cost_error / predicted_cost_pct * 100)) if predicted_cost_pct != 0 else 0
    else:
        cost_error = observed_cost_pct
        cost_accuracy_pct = 100 if observed_cost_pct == 0 else 0
    
    overall_accuracy_pct = (util_accuracy_pct * 0.6 + cost_accuracy_pct * 0.4)
    
    accuracy_record = {
        "accuracy_id": f"{scenario_result.get('scenario_id')}_{observation_id}",
        "tenant_id": str(tenant_id),
        "scenario_analysis_id": str(scenario_analysis_id),
        "scenario_id": scenario_result.get("scenario_id"),
        "observation_id": observation_id,
        "policy_id": observation.get("policy_id"),
        "computed_at": datetime.utcnow().isoformat(),
        "accuracy_metrics": {
            "overall_accuracy_pct": overall_accuracy_pct,
            "utilization_accuracy": {
                "predicted_pct": predicted_util_pct,
                "observed_pct": observed_util_pct,
                "error_pct": util_error,
                "accuracy_pct": util_accuracy_pct,
            },
            "cost_accuracy": {
                "predicted_pct": predicted_cost_pct,
                "observed_pct": observed_cost_pct,
                "error_pct": cost_error,
                "accuracy_pct": cost_accuracy_pct,
            },
        },
        "predicted_metrics": predicted_metrics,
        "observed_metrics": observed_metrics,
    }
    
    return _compute_scenario_accuracy(tenant_id, scenario_analysis_id, observation_id, accuracy_record)


def _compute_scenario_accuracy(
    tenant_id: UUID,
    scenario_analysis_id: UUID,
    observation_id: str,
    accuracy_record: Dict[str, Any]
) -> Dict[str, Any]:
    """Save accuracy record in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        scenario_id = accuracy_record.get("scenario_id")
        from uepi_api.storage_scenarios import list_scenarios
        scenarios = list_scenarios(tenant_id)
        scenario_db = None
        for s in scenarios:
            if s.get("scenario_id") == scenario_id:
                scenario_db_id = UUID(s.get("id")) if isinstance(s.get("id"), str) else s.get("id")
                scenario_db = db.query(ScenarioDB).filter(ScenarioDB.id == scenario_db_id).first()
                break
        
        if not scenario_db:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        accuracy_metrics = accuracy_record.get("accuracy_metrics", {})
        
        obs_uuid = UUID(observation_id) if observation_id else None
        q = db.query(ScenarioAccuracyDB).filter(ScenarioAccuracyDB.scenario_id == scenario_db.id)
        if obs_uuid is not None:
            q = q.filter(ScenarioAccuracyDB.observation_id == obs_uuid)
        accuracy_db = q.first()
        
        now = datetime.utcnow()
        meta = {
            "predicted_metrics": accuracy_record.get("predicted_metrics", {}),
            "observed_metrics": accuracy_record.get("observed_metrics", {}),
            "accuracy_metrics": accuracy_metrics,
        }
        if not accuracy_db:
            accuracy_db = ScenarioAccuracyDB(
                tenant_id=tenant_id,
                scenario_id=scenario_db.id,
                actual_vs_predicted_json=meta,
                evaluated_at=now,
                observation_id=obs_uuid,
                overall_accuracy_pct=accuracy_metrics.get("overall_accuracy_pct", 0),
                utilization_accuracy_pct=accuracy_metrics.get("utilization_accuracy", {}).get("accuracy_pct", 0),
                cost_accuracy_pct=accuracy_metrics.get("cost_accuracy", {}).get("accuracy_pct", 0),
                metadata_json=meta,
            )
            db.add(accuracy_db)
        else:
            accuracy_db.overall_accuracy_pct = accuracy_metrics.get("overall_accuracy_pct", 0)
            accuracy_db.utilization_accuracy_pct = accuracy_metrics.get("utilization_accuracy", {}).get("accuracy_pct", 0)
            accuracy_db.cost_accuracy_pct = accuracy_metrics.get("cost_accuracy", {}).get("accuracy_pct", 0)
            accuracy_db.evaluated_at = now
            accuracy_db.metadata_json = meta
        
        db.commit()
        db.refresh(accuracy_db)
        
        return accuracy_record
        
    except Exception as e:
        db.rollback()
        print(f"ERROR compute_scenario_accuracy (DB): {e}")
        raise ValueError(f"Failed to compute scenario accuracy: {e}")
    finally:
        db.close()


def get_scenario_accuracy(
    tenant_id: UUID,
    scenario_analysis_id: Optional[UUID] = None,
    policy_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Get scenario accuracy records - from database
    
    Args:
        tenant_id: Tenant ID
        scenario_analysis_id: Optional filter by scenario analysis ID
        policy_id: Optional filter by policy ID
    
    Returns:
        List of accuracy records
    """
    return _get_scenario_accuracy(tenant_id, scenario_analysis_id, policy_id)


def _get_scenario_accuracy(
    tenant_id: UUID,
    scenario_analysis_id: Optional[UUID] = None,
    policy_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Get scenario accuracy records from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ScenarioAccuracyDB).join(ScenarioDB).filter(
            ScenarioDB.tenant_id == tenant_id
        )
        
        if policy_id:
            query = query.filter(ScenarioDB.policy_id == policy_id)

        accuracy_records_db = query.order_by(desc(ScenarioAccuracyDB.evaluated_at)).limit(200).all()
        
        result = []
        for accuracy_db in accuracy_records_db:
            scenario_db = accuracy_db.scenario
            metadata = getattr(accuracy_db, "metadata_json", None) or {}
            accuracy_metrics = metadata.get("accuracy_metrics", {})
            evaluated_at = accuracy_db.evaluated_at
            observation_id = getattr(accuracy_db, "observation_id", None)
            result.append({
                "accuracy_id": f"{scenario_db.scenario_id}_{observation_id or ''}",
                "tenant_id": str(tenant_id),
                "scenario_analysis_id": str(scenario_analysis_id) if scenario_analysis_id else "",
                "scenario_id": scenario_db.scenario_id,
                "observation_id": str(observation_id) if observation_id else "",
                "policy_id": str(scenario_db.policy_id) if scenario_db.policy_id else "",
                "computed_at": evaluated_at.isoformat() if evaluated_at else datetime.utcnow().isoformat(),
                "accuracy_metrics": accuracy_metrics,
                "predicted_metrics": metadata.get("predicted_metrics", {}),
                "observed_metrics": metadata.get("observed_metrics", {}),
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR get_scenario_accuracy (DB): {e}")
        return []
    finally:
        db.close()


def get_scenario_links(
    tenant_id: UUID,
    scenario_analysis_id: Optional[UUID] = None,
    policy_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Get scenario-to-policy links - from database"""
    return _get_scenario_links(tenant_id, scenario_analysis_id, policy_id)


def _get_scenario_links(
    tenant_id: UUID,
    scenario_analysis_id: Optional[UUID] = None,
    policy_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Get scenario-to-policy links from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ScenarioAccuracyDB).join(ScenarioDB).filter(
            ScenarioDB.tenant_id == tenant_id,
            ScenarioAccuracyDB.linked_policy_id.isnot(None)
        )
        
        if policy_id:
            query = query.filter(ScenarioAccuracyDB.linked_policy_id == policy_id)
        
        accuracy_records_db = query.all()
        
        result = []
        for accuracy_db in accuracy_records_db:
            scenario_db = accuracy_db.scenario
            linked_policy_id = getattr(accuracy_db, "linked_policy_id", None)
            linked_at = getattr(accuracy_db, "linked_at", None)
            metadata_json = getattr(accuracy_db, "metadata_json", None) or {}
            result.append({
                "link_id": f"{scenario_db.scenario_id}_{linked_policy_id or ''}",
                "tenant_id": str(tenant_id),
                "scenario_analysis_id": str(scenario_analysis_id) if scenario_analysis_id else "",
                "scenario_id": scenario_db.scenario_id,
                "policy_id": str(linked_policy_id) if linked_policy_id else "",
                "linked_at": linked_at.isoformat() if linked_at else datetime.utcnow().isoformat(),
                "metadata": metadata_json,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR get_scenario_links (DB): {e}")
        return []
    finally:
        db.close()
