"""Policy predicted impact storage operations - database only"""
import json
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.predicted_impact import PolicyPredictedImpact
from uepi_api.models.policy import Policy
from sqlalchemy import or_, desc


def get_predicted_impact(policy_id: UUID | str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get predicted impact for a policy - from database
    
    Args:
        policy_id: Policy ID (UUID or string)
        tenant_id: Tenant ID
        
    Returns:
        Predicted impact dict if available, None otherwise
    """
    return _get_predicted_impact(policy_id, tenant_id)


def _get_predicted_impact(policy_id: UUID | str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get predicted impact from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
            try:
                policy_id_uuid = UUID(policy_id)
            except ValueError:
                # Not a UUID, find policy by string ID first
                policy = db.query(Policy).filter(
                    Policy.tenant_id == tenant_id,
                    or_(
                        Policy.id == policy_id,
                        Policy.policy_metadata_json['policy_id'].astext == policy_id
                    )
                ).first()
                if not policy:
                    return None
                policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
        
        # Query most recent predicted impact from database
        predicted_impact = db.query(PolicyPredictedImpact).filter(
            PolicyPredictedImpact.tenant_id == tenant_id,
            PolicyPredictedImpact.policy_id == policy_id_uuid
        ).order_by(desc(PolicyPredictedImpact.predicted_at)).first()
        
        if not predicted_impact:
            return None
        
        # Convert to dict format (same as file-based)
        # Extract all fields from metrics_json (which may contain full predicted impact)
        metrics_data = predicted_impact.metrics_json if predicted_impact.metrics_json else {}
        if isinstance(metrics_data, str):
            try:
                metrics_data = json.loads(metrics_data)
            except (json.JSONDecodeError, TypeError):
                metrics_data = {}
        if not isinstance(metrics_data, dict):
            metrics_data = {}
        
        pred_metrics = metrics_data.get("metrics", metrics_data) if isinstance(metrics_data, dict) else metrics_data
        if not isinstance(pred_metrics, dict):
            pred_metrics = {}
        
        # Phase 2.2: Ensure observation_enhancement can find utilization_change and cost_change
        # Add aliases for utilization_change_per_1k -> utilization_change, cost_change_pmpm -> cost_change
        util_change = pred_metrics.get("utilization_change_per_1k") or pred_metrics.get("utilization_change")
        cost_change = pred_metrics.get("cost_change_pmpm") or pred_metrics.get("cost_change")
        if util_change is not None and "utilization_change" not in pred_metrics:
            pred_metrics = dict(pred_metrics, utilization_change=util_change)
        if cost_change is not None and "cost_change" not in pred_metrics:
            pred_metrics = dict(pred_metrics, cost_change=cost_change)
        
        # If metrics_json contains the full predicted impact structure, extract all fields
        result = {
            "policy_id": str(predicted_impact.policy_id),
            "predicted_at": predicted_impact.predicted_at.isoformat() if predicted_impact.predicted_at else None,
            "metrics": pred_metrics,
            "model_version": predicted_impact.model_version,
            "confidence": predicted_impact.confidence,
            "prediction_method": predicted_impact.prediction_method,
            "baseline_id": str(predicted_impact.baseline_id) if predicted_impact.baseline_id else None,
            "data_period_id": str(predicted_impact.data_period_id) if predicted_impact.data_period_id else None,
        }
        
        # Extract additional fields if they exist in metrics_json
        if isinstance(metrics_data, dict):
            if "provider_response" in metrics_data:
                result["provider_response"] = metrics_data["provider_response"]
            if "patient_response" in metrics_data:
                result["patient_response"] = metrics_data["patient_response"]
            if "substitution_effects" in metrics_data:
                result["substitution_effects"] = metrics_data["substitution_effects"]
            if "warnings" in metrics_data:
                result["warnings"] = metrics_data["warnings"]
            if "limitations" in metrics_data:
                result["limitations"] = metrics_data["limitations"]
            if "baseline_reference" in metrics_data:
                result["baseline_reference"] = metrics_data["baseline_reference"]
            if "model_versions" in metrics_data:
                result["model_versions"] = metrics_data["model_versions"]
            if "confidence_intervals" in metrics_data:
                result["confidence_intervals"] = metrics_data["confidence_intervals"]
            if "ramp_up_projections" in metrics_data:
                result["ramp_up_projections"] = metrics_data["ramp_up_projections"]
        
        return result
        
    except Exception as e:
        print(f"ERROR get_predicted_impact (DB): {e}")
        return None
    finally:
        db.close()


def store_predicted_impact(
    policy_id: UUID | str,
    tenant_id: UUID,
    predicted_impact_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Store predicted impact - in database"""
    return _store_predicted_impact(policy_id, tenant_id, predicted_impact_data)


def _store_predicted_impact(
    policy_id: UUID | str,
    tenant_id: UUID,
    predicted_impact_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Store predicted impact in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
            try:
                policy_id_uuid = UUID(policy_id)
            except ValueError:
                # Not a UUID, find policy by string ID first
                policy = db.query(Policy).filter(
                    Policy.tenant_id == tenant_id,
                    or_(
                        Policy.id == policy_id,
                        Policy.policy_metadata_json['policy_id'].astext == policy_id
                    )
                ).first()
                if not policy:
                    return None
                policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
        
        # Parse predicted_at
        predicted_at = datetime.utcnow()
        if predicted_impact_data.get("predicted_at"):
            if isinstance(predicted_impact_data["predicted_at"], str):
                predicted_at = datetime.fromisoformat(predicted_impact_data["predicted_at"].replace("Z", "+00:00"))
            else:
                predicted_at = predicted_impact_data["predicted_at"]
        
        # Store full predicted impact data in metrics_json (including provider_response, patient_response, etc.)
        # This allows us to store all fields without schema changes
        full_metrics_data = {
            "metrics": predicted_impact_data.get("metrics", {}),
        }
        
        # Include additional fields if provided
        if "provider_response" in predicted_impact_data:
            full_metrics_data["provider_response"] = predicted_impact_data["provider_response"]
        if "patient_response" in predicted_impact_data:
            full_metrics_data["patient_response"] = predicted_impact_data["patient_response"]
        if "substitution_effects" in predicted_impact_data:
            full_metrics_data["substitution_effects"] = predicted_impact_data["substitution_effects"]
        if "warnings" in predicted_impact_data:
            full_metrics_data["warnings"] = predicted_impact_data["warnings"]
        if "limitations" in predicted_impact_data:
            full_metrics_data["limitations"] = predicted_impact_data["limitations"]
        if "baseline_reference" in predicted_impact_data:
            full_metrics_data["baseline_reference"] = predicted_impact_data["baseline_reference"]
        if "model_versions" in predicted_impact_data:
            full_metrics_data["model_versions"] = predicted_impact_data["model_versions"]
        if "confidence_intervals" in predicted_impact_data and predicted_impact_data["confidence_intervals"]:
            full_metrics_data["confidence_intervals"] = predicted_impact_data["confidence_intervals"]
        if "ramp_up_projections" in predicted_impact_data and predicted_impact_data["ramp_up_projections"]:
            full_metrics_data["ramp_up_projections"] = predicted_impact_data["ramp_up_projections"]
        
        # Create predicted impact in database
        predicted_impact = PolicyPredictedImpact(
            tenant_id=tenant_id,
            policy_id=policy_id_uuid,
            metrics_json=full_metrics_data,  # Store full data structure
            model_version=predicted_impact_data.get("model_version"),
            confidence=predicted_impact_data.get("confidence"),
            predicted_at=predicted_at,
            prediction_method=predicted_impact_data.get("prediction_method"),
            baseline_id=UUID(predicted_impact_data["baseline_id"]) if predicted_impact_data.get("baseline_id") else None,
            data_period_id=UUID(predicted_impact_data["data_period_id"]) if predicted_impact_data.get("data_period_id") else None,
        )
        
        db.add(predicted_impact)
        db.commit()
        db.refresh(predicted_impact)
        
        # Return as dict (same format as file-based)
        return {
            "policy_id": str(predicted_impact.policy_id),
            "predicted_at": predicted_impact.predicted_at.isoformat() if predicted_impact.predicted_at else None,
            "metrics": predicted_impact.metrics_json,
            "model_version": predicted_impact.model_version,
            "confidence": predicted_impact.confidence,
            "prediction_method": predicted_impact.prediction_method,
            "baseline_id": str(predicted_impact.baseline_id) if predicted_impact.baseline_id else None,
            "data_period_id": str(predicted_impact.data_period_id) if predicted_impact.data_period_id else None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR store_predicted_impact (DB): {e}")
        return None
    finally:
        db.close()
