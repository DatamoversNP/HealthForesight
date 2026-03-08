"""Learning model storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.learning import ElasticityModel, ModelAccuracyHistory
from sqlalchemy import desc


def create_elasticity_model(
    tenant_id: UUID,
    model_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new elasticity model - stored in database"""
    return _create_elasticity_model(tenant_id, model_data)


def _create_elasticity_model(
    tenant_id: UUID,
    model_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create elasticity model in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        model_id = str(model_data.get("model_id") or uuid4())
        
        policy_id = None
        if model_data.get("policy_id"):
            policy_id = UUID(model_data["policy_id"]) if isinstance(model_data["policy_id"], str) else model_data["policy_id"]
        
        trained_at = datetime.fromisoformat(model_data["trained_at"].replace("Z", "+00:00")) if isinstance(model_data.get("trained_at"), str) else model_data.get("trained_at", datetime.utcnow())
        last_refresh_timestamp = datetime.fromisoformat(model_data["last_refresh_timestamp"].replace("Z", "+00:00")) if isinstance(model_data.get("last_refresh_timestamp"), str) else model_data.get("last_refresh_timestamp", datetime.utcnow())
        
        model = ElasticityModel(
            tenant_id=tenant_id,
            model_id=model_id,
            policy_id=policy_id,
            model_type=model_data.get("model_type", "LINEAR"),
            model_version=model_data.get("version", "v1.0"),
            parameters_json={
                "policy_type": model_data.get("policy_type"),
                "service_category": model_data.get("service_category"),
                "elasticity_coefficients": model_data.get("elasticity_coefficients", {}),
                "learned_from_observations": model_data.get("learned_from_observations", []),
                "refresh_reason": model_data.get("refresh_reason", "MODEL_UPDATED"),
                "last_refresh_timestamp": last_refresh_timestamp.isoformat() if isinstance(last_refresh_timestamp, datetime) else last_refresh_timestamp,
                "metadata": model_data.get("metadata", {}),
            },
            accuracy_metrics_json={
                "confidence": model_data.get("confidence", 0.0),
                "training_metrics": model_data.get("training_metrics", {}),
            },
            trained_at=trained_at,
            status="ACTIVE",
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        params = model.parameters_json if model.parameters_json else {}
        metrics = model.accuracy_metrics_json if model.accuracy_metrics_json else {}
        return {
            "model_id": model.model_id,
            "tenant_id": str(model.tenant_id),
            "version": model.model_version,
            "policy_type": params.get("policy_type"),
            "service_category": params.get("service_category"),
            "elasticity_coefficients": params.get("elasticity_coefficients", {}),
            "learned_from_observations": params.get("learned_from_observations", []),
            "confidence": metrics.get("confidence", 0.0),
            "training_metrics": metrics.get("training_metrics", {}),
            "refresh_reason": params.get("refresh_reason", "MODEL_UPDATED"),
            "last_refresh_timestamp": params.get("last_refresh_timestamp"),
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "metadata": params.get("metadata", {}),
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create elasticity model: {e}")
    finally:
        db.close()


def get_elasticity_model(tenant_id: UUID, model_id: str) -> Optional[Dict[str, Any]]:
    """Get an elasticity model by ID - from database"""
    return _get_elasticity_model(tenant_id, model_id)


def _get_elasticity_model(tenant_id: UUID, model_id: str) -> Optional[Dict[str, Any]]:
    """Get elasticity model from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        model = db.query(ElasticityModel).filter(
            ElasticityModel.tenant_id == tenant_id,
            ElasticityModel.model_id == model_id
        ).first()
        
        if not model:
            return None
        
        params = model.parameters_json if model.parameters_json else {}
        metrics = model.accuracy_metrics_json if model.accuracy_metrics_json else {}
        return {
            "model_id": model.model_id,
            "tenant_id": str(model.tenant_id),
            "version": model.model_version,
            "policy_type": params.get("policy_type"),
            "service_category": params.get("service_category"),
            "elasticity_coefficients": params.get("elasticity_coefficients", {}),
            "learned_from_observations": params.get("learned_from_observations", []),
            "confidence": metrics.get("confidence", 0.0),
            "training_metrics": metrics.get("training_metrics", {}),
            "refresh_reason": params.get("refresh_reason", "MODEL_UPDATED"),
            "last_refresh_timestamp": params.get("last_refresh_timestamp"),
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "metadata": params.get("metadata", {}),
        }
        
    except Exception as e:
        print(f"ERROR get_elasticity_model (DB): {e}")
        return None
    finally:
        db.close()


def list_elasticity_models(
    tenant_id: UUID,
    policy_type: Optional[str] = None,
    service_category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List elasticity models for a tenant - from database"""
    return _list_elasticity_models(tenant_id, policy_type, service_category)


def _list_elasticity_models(
    tenant_id: UUID,
    policy_type: Optional[str] = None,
    service_category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List elasticity models from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ElasticityModel).filter(ElasticityModel.tenant_id == tenant_id)
        models = query.order_by(desc(ElasticityModel.updated_at)).all()
        
        result = []
        for model in models:
            params = model.parameters_json if model.parameters_json else {}
            
            if policy_type and params.get("policy_type") != policy_type:
                continue
            if service_category and params.get("service_category") != service_category:
                continue
            
            metrics = model.accuracy_metrics_json if model.accuracy_metrics_json else {}
            result.append({
                "model_id": model.model_id,
                "tenant_id": str(model.tenant_id),
                "version": model.model_version,
                "policy_type": params.get("policy_type"),
                "service_category": params.get("service_category"),
                "elasticity_coefficients": params.get("elasticity_coefficients", {}),
                "learned_from_observations": params.get("learned_from_observations", []),
                "confidence": metrics.get("confidence", 0.0),
                "training_metrics": metrics.get("training_metrics", {}),
                "refresh_reason": params.get("refresh_reason", "MODEL_UPDATED"),
                "last_refresh_timestamp": params.get("last_refresh_timestamp"),
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None,
                "metadata": params.get("metadata", {}),
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_elasticity_models (DB): {e}")
        return []
    finally:
        db.close()


def get_latest_elasticity_model(
    tenant_id: UUID,
    policy_type: str,
    service_category: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get latest elasticity model for a policy type and service category"""
    models = list_elasticity_models(tenant_id, policy_type, service_category)
    return models[0] if models else None


def update_elasticity_model(
    tenant_id: UUID,
    model_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update elasticity model - stored in database"""
    return _update_elasticity_model(tenant_id, model_id, updates)


def _update_elasticity_model(
    tenant_id: UUID,
    model_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update elasticity model in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        model = db.query(ElasticityModel).filter(
            ElasticityModel.tenant_id == tenant_id,
            ElasticityModel.model_id == model_id
        ).first()
        
        if not model:
            return None
        
        if "version" in updates:
            model.model_version = updates["version"]
        if "model_type" in updates:
            model.model_type = updates["model_type"]
        
        if any(k in updates for k in ["policy_type", "service_category", "elasticity_coefficients", "learned_from_observations", "refresh_reason", "last_refresh_timestamp", "metadata"]):
            params = model.parameters_json if model.parameters_json else {}
            if "policy_type" in updates:
                params["policy_type"] = updates["policy_type"]
            if "service_category" in updates:
                params["service_category"] = updates["service_category"]
            if "elasticity_coefficients" in updates:
                params["elasticity_coefficients"] = updates["elasticity_coefficients"]
            if "learned_from_observations" in updates:
                params["learned_from_observations"] = updates["learned_from_observations"]
            if "refresh_reason" in updates:
                params["refresh_reason"] = updates["refresh_reason"]
            if "last_refresh_timestamp" in updates:
                params["last_refresh_timestamp"] = updates["last_refresh_timestamp"].isoformat() if hasattr(updates["last_refresh_timestamp"], 'isoformat') else updates["last_refresh_timestamp"]
            if "metadata" in updates:
                params["metadata"] = updates["metadata"]
            model.parameters_json = params
        
        if "confidence" in updates or "training_metrics" in updates:
            metrics = model.accuracy_metrics_json if model.accuracy_metrics_json else {}
            if "confidence" in updates:
                metrics["confidence"] = updates["confidence"]
            if "training_metrics" in updates:
                metrics["training_metrics"] = updates["training_metrics"]
            model.accuracy_metrics_json = metrics
        
        db.commit()
        db.refresh(model)
        
        params = model.parameters_json if model.parameters_json else {}
        metrics = model.accuracy_metrics_json if model.accuracy_metrics_json else {}
        return {
            "model_id": model.model_id,
            "tenant_id": str(model.tenant_id),
            "version": model.model_version,
            "policy_type": params.get("policy_type"),
            "service_category": params.get("service_category"),
            "elasticity_coefficients": params.get("elasticity_coefficients", {}),
            "learned_from_observations": params.get("learned_from_observations", []),
            "confidence": metrics.get("confidence", 0.0),
            "training_metrics": metrics.get("training_metrics", {}),
            "refresh_reason": params.get("refresh_reason", "MODEL_UPDATED"),
            "last_refresh_timestamp": params.get("last_refresh_timestamp"),
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "metadata": params.get("metadata", {}),
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_elasticity_model (DB): {e}")
        return None
    finally:
        db.close()


# Accuracy Record Functions
def create_accuracy_record(
    tenant_id: UUID,
    accuracy_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new accuracy record - stored in database"""
    return _create_accuracy_record(tenant_id, accuracy_data)


def _create_accuracy_record(
    tenant_id: UUID,
    accuracy_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create accuracy record in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        elasticity_model_id_str = accuracy_data.get("elasticity_model_id")
        elasticity_model_id_uuid = None
        if elasticity_model_id_str:
            elasticity_model = db.query(ElasticityModel).filter(
                ElasticityModel.tenant_id == tenant_id,
                ElasticityModel.model_id == elasticity_model_id_str
            ).first()
            if elasticity_model:
                elasticity_model_id_uuid = elasticity_model.id
        
        # model_accuracy_history.model_id is NOT NULL; skip insert when no elasticity model exists
        if elasticity_model_id_uuid is None:
            recorded_at = accuracy_data.get("recorded_at")
            if not recorded_at:
                recorded_at = datetime.utcnow()
            elif isinstance(recorded_at, str):
                recorded_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
            metrics = {
                "predicted_effect_size": accuracy_data.get("predicted_effect_size", 0.0),
                "observed_effect_size": accuracy_data.get("observed_effect_size", 0.0),
                "prediction_error": accuracy_data.get("prediction_error", 0.0),
                "prediction_error_pct": accuracy_data.get("prediction_error_pct", 0.0),
                "prediction_accuracy_pct": accuracy_data.get("prediction_accuracy_pct", 0.0),
                "metrics": accuracy_data.get("metrics", {}),
                "policy_id": str(accuracy_data.get("policy_id", "")) if accuracy_data.get("policy_id") else None,
                "observation_id": str(accuracy_data.get("observation_id", "")) if accuracy_data.get("observation_id") else None,
                "prediction_id": str(accuracy_data.get("prediction_id", "")) if accuracy_data.get("prediction_id") else None,
                "metadata": accuracy_data.get("metadata", {}),
            }
            return {
                "accuracy_id": None,
                "tenant_id": str(tenant_id),
                "policy_id": metrics.get("policy_id"),
                "observation_id": metrics.get("observation_id"),
                "prediction_id": metrics.get("prediction_id"),
                "elasticity_model_id": elasticity_model_id_str,
                "predicted_effect_size": metrics.get("predicted_effect_size", 0.0),
                "observed_effect_size": metrics.get("observed_effect_size", 0.0),
                "prediction_error": metrics.get("prediction_error", 0.0),
                "prediction_error_pct": metrics.get("prediction_error_pct", 0.0),
                "prediction_accuracy_pct": metrics.get("prediction_accuracy_pct", 0.0),
                "metrics": metrics.get("metrics", {}),
                "recorded_at": recorded_at.isoformat() if hasattr(recorded_at, "isoformat") else str(recorded_at),
                "metadata": metrics.get("metadata", {}),
            }
        
        # Handle recorded_at - use current time if not provided
        recorded_at = accuracy_data.get("recorded_at")
        if not recorded_at:
            recorded_at = datetime.utcnow()
        elif isinstance(recorded_at, str):
            recorded_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
        
        evaluation_date = recorded_at
        evaluation_data_period_id = UUID(accuracy_data["evaluation_data_period_id"]) if accuracy_data.get("evaluation_data_period_id") else None
        
        accuracy_record = ModelAccuracyHistory(
            tenant_id=tenant_id,
            model_id=elasticity_model_id_uuid,
            evaluation_date=evaluation_date,
            evaluation_data_period_id=evaluation_data_period_id,
            metrics_json={
                "predicted_effect_size": accuracy_data.get("predicted_effect_size", 0.0),
                "observed_effect_size": accuracy_data.get("observed_effect_size", 0.0),
                "prediction_error": accuracy_data.get("prediction_error", 0.0),
                "prediction_error_pct": accuracy_data.get("prediction_error_pct", 0.0),
                "prediction_accuracy_pct": accuracy_data.get("prediction_accuracy_pct", 0.0),
                "metrics": accuracy_data.get("metrics", {}),
                "policy_id": str(accuracy_data.get("policy_id", "")) if accuracy_data.get("policy_id") else None,
                "observation_id": str(accuracy_data.get("observation_id", "")) if accuracy_data.get("observation_id") else None,
                "prediction_id": str(accuracy_data.get("prediction_id", "")) if accuracy_data.get("prediction_id") else None,
                "metadata": accuracy_data.get("metadata", {}),
            },
        )
        
        db.add(accuracy_record)
        db.commit()
        db.refresh(accuracy_record)
        
        metrics = accuracy_record.metrics_json if accuracy_record.metrics_json else {}
        return {
            "accuracy_id": str(accuracy_record.id),
            "tenant_id": str(accuracy_record.tenant_id),
            "policy_id": metrics.get("policy_id"),
            "observation_id": metrics.get("observation_id"),
            "prediction_id": metrics.get("prediction_id"),
            "elasticity_model_id": elasticity_model_id_str,
            "predicted_effect_size": metrics.get("predicted_effect_size", 0.0),
            "observed_effect_size": metrics.get("observed_effect_size", 0.0),
            "prediction_error": metrics.get("prediction_error", 0.0),
            "prediction_error_pct": metrics.get("prediction_error_pct", 0.0),
            "prediction_accuracy_pct": metrics.get("prediction_accuracy_pct", 0.0),
            "metrics": metrics.get("metrics", {}),
            "recorded_at": accuracy_record.evaluation_date.isoformat() if accuracy_record.evaluation_date else None,
            "metadata": metrics.get("metadata", {}),
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create accuracy record: {e}")
    finally:
        db.close()


def get_accuracy_record(tenant_id: UUID, accuracy_id: str) -> Optional[Dict[str, Any]]:
    """Get an accuracy record by ID - from database"""
    return _get_accuracy_record(tenant_id, accuracy_id)


def _get_accuracy_record(tenant_id: UUID, accuracy_id: str) -> Optional[Dict[str, Any]]:
    """Get accuracy record from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        accuracy_record = db.query(ModelAccuracyHistory).filter(
            ModelAccuracyHistory.tenant_id == tenant_id,
            ModelAccuracyHistory.id == UUID(accuracy_id)
        ).first()
        
        if not accuracy_record:
            return None
        
        elasticity_model_id_str = None
        if accuracy_record.model_id:
            elasticity_model = db.query(ElasticityModel).filter(
                ElasticityModel.id == accuracy_record.model_id
            ).first()
            if elasticity_model:
                elasticity_model_id_str = elasticity_model.model_id
        
        metrics = accuracy_record.metrics_json if accuracy_record.metrics_json else {}
        return {
            "accuracy_id": str(accuracy_record.id),
            "tenant_id": str(accuracy_record.tenant_id),
            "policy_id": metrics.get("policy_id"),
            "observation_id": metrics.get("observation_id"),
            "prediction_id": metrics.get("prediction_id"),
            "elasticity_model_id": elasticity_model_id_str,
            "predicted_effect_size": metrics.get("predicted_effect_size", 0.0),
            "observed_effect_size": metrics.get("observed_effect_size", 0.0),
            "prediction_error": metrics.get("prediction_error", 0.0),
            "prediction_error_pct": metrics.get("prediction_error_pct", 0.0),
            "prediction_accuracy_pct": metrics.get("prediction_accuracy_pct", 0.0),
            "metrics": metrics.get("metrics", {}),
            "recorded_at": accuracy_record.evaluation_date.isoformat() if accuracy_record.evaluation_date else None,
            "metadata": metrics.get("metadata", {}),
        }
        
    except Exception as e:
        print(f"ERROR get_accuracy_record (DB): {e}")
        return None
    finally:
        db.close()


def list_accuracy_records(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    elasticity_model_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List accuracy records for a tenant - from database"""
    return _list_accuracy_records(tenant_id, policy_id, elasticity_model_id)


def _list_accuracy_records(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    elasticity_model_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List accuracy records from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ModelAccuracyHistory).filter(ModelAccuracyHistory.tenant_id == tenant_id)
        
        if elasticity_model_id:
            elasticity_model = db.query(ElasticityModel).filter(
                ElasticityModel.tenant_id == tenant_id,
                ElasticityModel.model_id == elasticity_model_id
            ).first()
            if elasticity_model:
                query = query.filter(ModelAccuracyHistory.model_id == elasticity_model.id)
            else:
                return []
        
        records = query.order_by(desc(ModelAccuracyHistory.evaluation_date)).all()
        
        result = []
        for accuracy_record in records:
            metrics = accuracy_record.metrics_json if accuracy_record.metrics_json else {}
            
            if policy_id:
                record_policy_id = metrics.get("policy_id")
                if record_policy_id and UUID(record_policy_id) != policy_id:
                    continue
            
            elasticity_model_id_str = None
            if accuracy_record.model_id:
                elasticity_model = db.query(ElasticityModel).filter(
                    ElasticityModel.id == accuracy_record.model_id
                ).first()
                if elasticity_model:
                    elasticity_model_id_str = elasticity_model.model_id
            
            result.append({
                "accuracy_id": str(accuracy_record.id),
                "tenant_id": str(accuracy_record.tenant_id),
                "policy_id": metrics.get("policy_id"),
                "observation_id": metrics.get("observation_id"),
                "prediction_id": metrics.get("prediction_id"),
                "elasticity_model_id": elasticity_model_id_str,
                "predicted_effect_size": metrics.get("predicted_effect_size", 0.0),
                "observed_effect_size": metrics.get("observed_effect_size", 0.0),
                "prediction_error": metrics.get("prediction_error", 0.0),
                "prediction_error_pct": metrics.get("prediction_error_pct", 0.0),
                "prediction_accuracy_pct": metrics.get("prediction_accuracy_pct", 0.0),
                "metrics": metrics.get("metrics", {}),
                "recorded_at": accuracy_record.evaluation_date.isoformat() if accuracy_record.evaluation_date else None,
                "metadata": metrics.get("metadata", {}),
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_accuracy_records (DB): {e}")
        return []
    finally:
        db.close()


def get_accuracy_history(
    tenant_id: UUID,
    policy_id: UUID,
) -> List[Dict[str, Any]]:
    """Get accuracy history for a policy"""
    return list_accuracy_records(tenant_id=tenant_id, policy_id=policy_id)
