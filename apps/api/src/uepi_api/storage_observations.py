"""Observation storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.observation import Observation


def create_observation(
    tenant_id: UUID,
    observation_data: Dict[str, Any],
    input_refs: Optional[Dict[str, Any]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    triggered_by_user_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Create a new observation. Optional input_refs/config_snapshot for deterministic lineage (Phase 1)."""
    return _create_observation(
        tenant_id, observation_data,
        input_refs=input_refs,
        config_snapshot=config_snapshot,
        triggered_by_user_id=triggered_by_user_id,
    )


def _create_observation(
    tenant_id: UUID,
    observation_data: Dict[str, Any],
    input_refs: Optional[Dict[str, Any]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    triggered_by_user_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Create observation in database. Uses explicit input_refs/config_snapshot when provided."""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate observation_id if not provided
        observation_id = observation_data.get("observation_id") or str(uuid4())
        
        # Parse UUIDs first (before dates, in case there's confusion)
        policy_id = None
        if observation_data.get("policy_id"):
            policy_id_val = observation_data["policy_id"]
            if isinstance(policy_id_val, UUID):
                policy_id = policy_id_val
            else:
                policy_id = UUID(str(policy_id_val))
        
        # policy_version_id can be None or a UUID (not a string like "policy_id-v1")
        policy_version_id = None
        policy_version_id_str = observation_data.get("policy_version_id")
        if policy_version_id_str:
            try:
                # Try to parse as UUID (if it's a valid UUID string)
                if isinstance(policy_version_id_str, UUID):
                    policy_version_id = policy_version_id_str
                elif len(str(policy_version_id_str)) == 36 and str(policy_version_id_str).count('-') == 4:
                    policy_version_id = UUID(policy_version_id_str)
            except (ValueError, AttributeError):
                # If it's not a UUID (e.g., "policy_id-v1"), leave as None
                policy_version_id = None
        
        baseline_version_id = None
        if observation_data.get("baseline_version_id"):
            val = observation_data["baseline_version_id"]
            baseline_version_id = val if isinstance(val, UUID) else UUID(str(val))
        
        prediction_id = None
        if observation_data.get("prediction_id"):
            val = observation_data["prediction_id"]
            prediction_id = val if isinstance(val, UUID) else UUID(str(val))
        
        analysis_id = None
        if observation_data.get("analysis_id"):
            val = observation_data["analysis_id"]
            analysis_id = val if isinstance(val, UUID) else UUID(str(val))
        
        data_period_id = None
        if observation_data.get("data_period_id"):
            val = observation_data["data_period_id"]
            data_period_id = val if isinstance(val, UUID) else UUID(str(val))
        
        # Parse dates - handle missing or None values
        period_start_str = observation_data.get("observation_period_start")
        period_end_str = observation_data.get("observation_period_end")
        computed_at_str = observation_data.get("computed_at")
        
        def _parse_iso(s: str) -> datetime:
            # Avoid turning "...+00:00Z" into "...+00:00+00:00" (invalid)
            if s.endswith("Z"):
                s = s[:-1]
                # already has offset if it ends with +HH:MM or -HH:MM
                if len(s) < 6 or s[-3] != ":" or s[-6] not in "+-":
                    s = s + "+00:00"
            else:
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s)

        if period_start_str:
            if isinstance(period_start_str, datetime):
                period_start = period_start_str
            elif isinstance(period_start_str, str):
                period_start = _parse_iso(period_start_str)
            else:
                raise ValueError(f"observation_period_start must be datetime or string, got {type(period_start_str)}")
        else:
            raise ValueError("observation_period_start is required")
        
        if period_end_str:
            if isinstance(period_end_str, datetime):
                period_end = period_end_str
            elif isinstance(period_end_str, str):
                period_end = _parse_iso(period_end_str)
            else:
                raise ValueError(f"observation_period_end must be datetime or string, got {type(period_end_str)}")
        else:
            raise ValueError("observation_period_end is required")
        
        if computed_at_str:
            if isinstance(computed_at_str, datetime):
                computed_at = computed_at_str
            elif isinstance(computed_at_str, str):
                computed_at = _parse_iso(computed_at_str)
            else:
                computed_at = datetime.utcnow()
        else:
            computed_at = datetime.utcnow()

        # Phase 1: Create analytics run for lineage (use explicit refs/config when provided)
        from uepi_api.storage_analytics_run import create_run, complete_run, fail_run
        run = None
        run_input_refs = input_refs if input_refs is not None else {
            "policy_id": str(policy_id) if policy_id else None,
            "baseline_version_id": str(baseline_version_id) if baseline_version_id else None,
            "prediction_id": str(prediction_id) if prediction_id else None,
            "analysis_id": str(analysis_id) if analysis_id else None,
            "data_period_id": str(data_period_id) if data_period_id else None,
        }
        run_config_snapshot = config_snapshot if config_snapshot is not None else {
            "observation_period_start": period_start.isoformat() if period_start else None,
            "observation_period_end": period_end.isoformat() if period_end else None,
        }
        run = create_run(
            tenant_id=tenant_id,
            run_type="OBSERVATION",
            input_refs=run_input_refs,
            config_snapshot=run_config_snapshot,
            triggered_by_user_id=triggered_by_user_id,
            db=db,
        )

        # Phase 2: Compute verdict (versioned logic)
        from uepi_api.verdict import compute_verdict, VERDICT_RULE_VERSION
        comparisons = observation_data.get("comparisons") or {}
        behavioral = observation_data.get("behavioral_explanation") or {}
        verdict_status, verdict_reason, recommendation = compute_verdict(comparisons, behavioral)
        
        # Create observation in database
        observation = Observation(
            tenant_id=tenant_id,
            observation_id=observation_id,
            policy_id=policy_id,
            policy_version_id=policy_version_id,
            baseline_version_id=baseline_version_id,
            prediction_id=prediction_id,
            analysis_id=analysis_id,
            data_period_id=data_period_id,
            data_period_ids_json=observation_data.get("data_period_ids", []),
            observation_type=observation_data.get("observation_type", "PERIODIC"),
            observation_period_start=period_start,
            observation_period_end=period_end,
            metrics_json={
                **(observation_data.get("metrics", {}) or {}),
                "observed_measures": observation_data.get("observed_measures", {}),
            },
            comparisons_json=observation_data.get("comparisons", {}),
            behavioral_explanation_json=observation_data.get("behavioral_explanation", {}),
            analytics_run_id=run.id,
            verdict_status=verdict_status,
            verdict_reason=verdict_reason,
            recommendation=recommendation,
            verdict_rule_version=VERDICT_RULE_VERSION,
            computed_at=computed_at,
        )
        
        db.add(observation)
        db.commit()
        db.refresh(observation)

        # Phase 1: Complete run with output refs
        complete_run(
            run.id,
            output_refs={"observation_id": observation.observation_id, "observation_db_id": str(observation.id)},
            db=db,
        )
        
        # Integration: Trigger learning from observation
        try:
            from uepi_api.learning_loop import learn_from_observation
            learning_result = learn_from_observation(
                tenant_id=tenant_id,
                observation_id=observation_id,
            )
            if learning_result.get("success"):
                print(f"Learning triggered for observation {observation_id}")
        except Exception as learning_error:
            # Don't fail observation creation if learning fails
            print(f"Warning: Failed to trigger learning for observation {observation_id}: {learning_error}")
        
        # Return as dict (same format as file-based). Strip observed_measures from metrics for backward compat; expose at top level.
        _metrics = observation.metrics_json or {}
        obs_dict = {
            "observation_id": observation.observation_id,
            "tenant_id": str(observation.tenant_id),
            "policy_id": str(observation.policy_id) if observation.policy_id else None,
            "policy_version_id": str(observation.policy_version_id) if observation.policy_version_id else None,
            "data_period_id": str(observation.data_period_id) if observation.data_period_id else None,
            "data_period_ids": observation.data_period_ids_json if observation.data_period_ids_json else [],
            "observation_type": observation.observation_type,
            "observation_period_start": observation.observation_period_start.isoformat() if observation.observation_period_start else None,
            "observation_period_end": observation.observation_period_end.isoformat() if observation.observation_period_end else None,
            "baseline_version_id": str(observation.baseline_version_id) if observation.baseline_version_id else None,
            "prediction_id": str(observation.prediction_id) if observation.prediction_id else None,
            "analysis_id": str(observation.analysis_id) if observation.analysis_id else None,
            "computed_at": observation.computed_at.isoformat() if observation.computed_at else None,
            "metrics": {k: v for k, v in _metrics.items() if k != "observed_measures"},
            "observed_measures": _metrics.get("observed_measures", {}),
            "comparisons": observation.comparisons_json if observation.comparisons_json else {},
            "behavioral_explanation": observation.behavioral_explanation_json if observation.behavioral_explanation_json else {},
            "analytics_run_id": str(observation.analytics_run_id) if observation.analytics_run_id else None,
            "verdict_status": getattr(observation, "verdict_status", None),
            "verdict_reason": getattr(observation, "verdict_reason", None),
            "recommendation": getattr(observation, "recommendation", None),
            "verdict_rule_version": getattr(observation, "verdict_rule_version", None),
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
            "updated_at": observation.updated_at.isoformat() if observation.updated_at else None,
            "metadata": {},
        }
        
        # Transform to match frontend expectations
        from uepi_api.observation_transform import transform_observation_for_frontend
        return transform_observation_for_frontend(obs_dict)
        
    except Exception as e:
        db.rollback()
        try:
            if run is not None:
                fail_run(run.id, str(e), db=db)
        except Exception:
            pass
        raise ValueError(f"Failed to create observation: {e}")
    finally:
        db.close()


def get_observation(tenant_id: UUID, observation_id: str) -> Optional[Dict[str, Any]]:
    """Get an observation by ID - from database"""
    return _get_observation(tenant_id, observation_id)


def _get_observation(tenant_id: UUID, observation_id: str) -> Optional[Dict[str, Any]]:
    """Get observation from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        observation = db.query(Observation).filter(
            Observation.tenant_id == tenant_id,
            Observation.observation_id == observation_id
        ).first()
        
        if not observation:
            return None
        
        _metrics = observation.metrics_json or {}
        return {
            "observation_id": observation.observation_id,
            "tenant_id": str(observation.tenant_id),
            "policy_id": str(observation.policy_id) if observation.policy_id else None,
            "policy_version_id": str(observation.policy_version_id) if observation.policy_version_id else None,
            "data_period_id": str(observation.data_period_id) if observation.data_period_id else None,
            "data_period_ids": observation.data_period_ids_json if observation.data_period_ids_json else [],
            "observation_type": observation.observation_type,
            "observation_period_start": observation.observation_period_start.isoformat() if observation.observation_period_start else None,
            "observation_period_end": observation.observation_period_end.isoformat() if observation.observation_period_end else None,
            "baseline_version_id": str(observation.baseline_version_id) if observation.baseline_version_id else None,
            "prediction_id": str(observation.prediction_id) if observation.prediction_id else None,
            "analysis_id": str(observation.analysis_id) if observation.analysis_id else None,
            "computed_at": observation.computed_at.isoformat() if observation.computed_at else None,
            "metrics": {k: v for k, v in _metrics.items() if k != "observed_measures"},
            "observed_measures": _metrics.get("observed_measures", {}),
            "comparisons": observation.comparisons_json if observation.comparisons_json else {},
            "behavioral_explanation": observation.behavioral_explanation_json if observation.behavioral_explanation_json else {},
            "analytics_run_id": str(observation.analytics_run_id) if getattr(observation, "analytics_run_id", None) else None,
            "verdict_status": getattr(observation, "verdict_status", None),
            "verdict_reason": getattr(observation, "verdict_reason", None),
            "recommendation": getattr(observation, "recommendation", None),
            "verdict_rule_version": getattr(observation, "verdict_rule_version", None),
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
            "updated_at": observation.updated_at.isoformat() if observation.updated_at else None,
            "metadata": {},
        }
        
    except Exception as e:
        print(f"ERROR get_observation (DB): {e}")
        return None
    finally:
        db.close()


# Default limit for list to keep responses fast (pagination can request more)
LIST_OBSERVATIONS_DEFAULT_LIMIT = 200


def list_observations(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    data_period_id: Optional[str] = None,
    observation_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List observations for a tenant - from database"""
    return _list_observations(tenant_id, policy_id, data_period_id, observation_type, limit)


def _list_observations(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    data_period_id: Optional[str] = None,
    observation_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List observations from database (limited for performance)."""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc

    db: Session = SessionLocal()
    try:
        query = db.query(Observation).filter(Observation.tenant_id == tenant_id)

        if policy_id:
            query = query.filter(Observation.policy_id == policy_id)
        if data_period_id:
            query = query.filter(Observation.data_period_id == UUID(data_period_id))
        if observation_type:
            query = query.filter(Observation.observation_type == observation_type)

        limit = min(limit or LIST_OBSERVATIONS_DEFAULT_LIMIT, 500)
        observations = query.order_by(desc(Observation.computed_at)).limit(limit).all()
        
        # Convert to dict format (same as file-based)
        from uepi_api.observation_transform import transform_observation_for_frontend
        
        result = []
        for observation in observations:
            _metrics = observation.metrics_json or {}
            obs_dict = {
                "observation_id": observation.observation_id,
                "tenant_id": str(observation.tenant_id),
                "policy_id": str(observation.policy_id) if observation.policy_id else None,
                "policy_version_id": str(observation.policy_version_id) if observation.policy_version_id else None,
                "data_period_id": str(observation.data_period_id) if observation.data_period_id else None,
                "data_period_ids": observation.data_period_ids_json if observation.data_period_ids_json else [],
                "observation_type": observation.observation_type,
                "observation_period_start": observation.observation_period_start.isoformat() if observation.observation_period_start else None,
                "observation_period_end": observation.observation_period_end.isoformat() if observation.observation_period_end else None,
                "baseline_version_id": str(observation.baseline_version_id) if observation.baseline_version_id else None,
                "prediction_id": str(observation.prediction_id) if observation.prediction_id else None,
                "analysis_id": str(observation.analysis_id) if observation.analysis_id else None,
                "computed_at": observation.computed_at.isoformat() if observation.computed_at else None,
                "metrics": {k: v for k, v in _metrics.items() if k != "observed_measures"},
                "observed_measures": _metrics.get("observed_measures", {}),
                "comparisons": observation.comparisons_json if observation.comparisons_json else {},
                "behavioral_explanation": observation.behavioral_explanation_json if observation.behavioral_explanation_json else {},
                "analytics_run_id": str(observation.analytics_run_id) if getattr(observation, "analytics_run_id", None) else None,
                "verdict_status": getattr(observation, "verdict_status", None),
                "verdict_reason": getattr(observation, "verdict_reason", None),
                "recommendation": getattr(observation, "recommendation", None),
                "verdict_rule_version": getattr(observation, "verdict_rule_version", None),
                "created_at": observation.created_at.isoformat() if observation.created_at else None,
                "updated_at": observation.updated_at.isoformat() if observation.updated_at else None,
                "metadata": {},
            }
            # Transform to match frontend expectations
            result.append(transform_observation_for_frontend(obs_dict))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_observations (DB): {e}")
        return []
    finally:
        db.close()


def delete_all_observations(tenant_id: UUID) -> int:
    """Delete all observations for a tenant. Returns number of observations deleted."""
    from uepi_api.database import SessionLocal

    db: Session = SessionLocal()
    try:
        count = db.query(Observation).filter(Observation.tenant_id == tenant_id).count()
        db.query(Observation).filter(Observation.tenant_id == tenant_id).delete()
        db.commit()
        return count
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_all_observations (DB): {e}")
        return 0
    finally:
        db.close()


def get_observations_for_policy(
    tenant_id: UUID,
    policy_id: UUID,
) -> List[Dict[str, Any]]:
    """Get all observations for a policy"""
    return list_observations(tenant_id=tenant_id, policy_id=policy_id)


def get_observations_for_period(
    tenant_id: UUID,
    data_period_id: str,
) -> List[Dict[str, Any]]:
    """Get all observations for a data period"""
    return list_observations(tenant_id=tenant_id, data_period_id=data_period_id)


def update_observation(
    tenant_id: UUID,
    observation_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update an existing observation in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        observation = db.query(Observation).filter(
            Observation.tenant_id == tenant_id,
            Observation.observation_id == observation_id
        ).first()
        
        if not observation:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(observation, key):
                if key in ['observation_period_start', 'observation_period_end', 'computed_at']:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif key in ['policy_id', 'policy_version_id', 'baseline_version_id', 'prediction_id', 'analysis_id', 'data_period_id'] and value:
                    value = UUID(value) if isinstance(value, str) else value
                elif key in ['data_period_ids', 'metrics', 'comparisons', 'behavioral_explanation']:
                    # These are JSON fields, keep as dict/list
                    pass
                setattr(observation, f"{key}_json" if key in ['data_period_ids', 'metrics', 'comparisons', 'behavioral_explanation'] else key, value)
        
        db.commit()
        db.refresh(observation)
        
        _metrics = observation.metrics_json or {}
        return {
            "observation_id": observation.observation_id,
            "tenant_id": str(observation.tenant_id),
            "policy_id": str(observation.policy_id) if observation.policy_id else None,
            "policy_version_id": str(observation.policy_version_id) if observation.policy_version_id else None,
            "data_period_id": str(observation.data_period_id) if observation.data_period_id else None,
            "data_period_ids": observation.data_period_ids_json if observation.data_period_ids_json else [],
            "observation_type": observation.observation_type,
            "observation_period_start": observation.observation_period_start.isoformat() if observation.observation_period_start else None,
            "observation_period_end": observation.observation_period_end.isoformat() if observation.observation_period_end else None,
            "baseline_version_id": str(observation.baseline_version_id) if observation.baseline_version_id else None,
            "prediction_id": str(observation.prediction_id) if observation.prediction_id else None,
            "analysis_id": str(observation.analysis_id) if observation.analysis_id else None,
            "computed_at": observation.computed_at.isoformat() if observation.computed_at else None,
            "metrics": {k: v for k, v in _metrics.items() if k != "observed_measures"},
            "observed_measures": _metrics.get("observed_measures", {}),
            "comparisons": observation.comparisons_json if observation.comparisons_json else {},
            "behavioral_explanation": observation.behavioral_explanation_json if observation.behavioral_explanation_json else {},
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
            "updated_at": observation.updated_at.isoformat() if observation.updated_at else None,
            "metadata": {},
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update observation: {e}")
    finally:
        db.close()
