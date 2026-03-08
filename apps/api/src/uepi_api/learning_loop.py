"""Learning loop logic - Learn from observations to improve predictions"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
import math

from uepi_api.storage_learning import (
    create_elasticity_model,
    get_elasticity_model,
    get_latest_elasticity_model,
    update_elasticity_model,
    create_accuracy_record,
    list_accuracy_records,
)
from uepi_api.storage_observations import get_observation
from uepi_api.storage_policies import get_policy


def calculate_prediction_accuracy(
    predicted_effect_size: float,
    observed_effect_size: float,
) -> Dict[str, Any]:
    """Calculate prediction accuracy metrics
    
    Args:
        predicted_effect_size: Predicted effect size
        observed_effect_size: Observed effect size
        
    Returns:
        Dictionary with accuracy metrics
    """
    prediction_error = observed_effect_size - predicted_effect_size
    prediction_error_pct = 0.0
    if predicted_effect_size != 0:
        prediction_error_pct = (prediction_error / abs(predicted_effect_size)) * 100
    
    prediction_accuracy_pct = 100.0 - abs(prediction_error_pct)
    
    # Calculate MAE and RMSE (simplified - in full implementation, would use multiple observations)
    mae = abs(prediction_error)
    rmse = abs(prediction_error)  # For single observation, RMSE = MAE
    
    return {
        "prediction_error": prediction_error,
        "prediction_error_pct": prediction_error_pct,
        "prediction_accuracy_pct": prediction_accuracy_pct,
        "mae": mae,
        "rmse": rmse,
        "within_range": abs(prediction_error_pct) < 20.0,  # Within 20% is considered good
    }


def record_prediction_accuracy(
    tenant_id: UUID,
    policy_id: UUID,
    observation_id: str,
    predicted_effect_size: float,
    observed_effect_size: float,
    prediction_id: Optional[str] = None,
    elasticity_model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record prediction accuracy for an observation
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        observation_id: Observation ID
        predicted_effect_size: Predicted effect size
        observed_effect_size: Observed effect size
        prediction_id: Optional prediction ID
        elasticity_model_id: Optional elasticity model ID
        
    Returns:
        Created accuracy record
    """
    accuracy_metrics = calculate_prediction_accuracy(predicted_effect_size, observed_effect_size)
    
    accuracy_data = {
        "policy_id": str(policy_id),
        "observation_id": observation_id,
        "prediction_id": prediction_id,
        "elasticity_model_id": elasticity_model_id,
        "predicted_effect_size": predicted_effect_size,
        "observed_effect_size": observed_effect_size,
        "prediction_error": accuracy_metrics["prediction_error"],
        "prediction_error_pct": accuracy_metrics["prediction_error_pct"],
        "prediction_accuracy_pct": accuracy_metrics["prediction_accuracy_pct"],
        "metrics": {
            "mae": accuracy_metrics["mae"],
            "rmse": accuracy_metrics["rmse"],
            "within_range": accuracy_metrics["within_range"],
        },
        "metadata": {},
        "recorded_at": datetime.utcnow(),  # Add timestamp
    }
    
    accuracy_record = create_accuracy_record(tenant_id=tenant_id, accuracy_data=accuracy_data)
    return accuracy_record


def update_elasticity_from_observations(
    tenant_id: UUID,
    policy_type: str,
    observations: List[Dict[str, Any]],
    service_category: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update elasticity coefficients from observations
    
    This is a simplified implementation. In production, this would use
    statistical methods (e.g., regression) to estimate elasticity coefficients.
    
    Args:
        tenant_id: Tenant ID
        policy_type: Policy type (e.g., PRIOR_AUTH)
        observations: List of observations with comparisons
        service_category: Optional service category
        
    Returns:
        Updated or created elasticity model
    """
    if not observations:
        return None
    
    # Get existing model or create new one
    existing_model = get_latest_elasticity_model(
        tenant_id=tenant_id,
        policy_type=policy_type,
        service_category=service_category,
    )
    
    # Extract prediction-observation pairs
    valid_pairs = []
    for obs in observations:
        comparisons = obs.get("comparisons", {})
        vs_predicted = comparisons.get("vs_predicted", {})
        
        if vs_predicted.get("predicted_effect_size") is not None and vs_predicted.get("observed_effect_size") is not None:
            valid_pairs.append({
                "predicted": vs_predicted.get("predicted_effect_size", 0.0),
                "observed": vs_predicted.get("observed_effect_size", 0.0),
                "observation_id": obs.get("observation_id"),
            })
    
    if not valid_pairs:
        return None
    
    # Simplified elasticity update: use average ratio
    # In production, would use regression or other statistical methods
    ratios = []
    for pair in valid_pairs:
        predicted = pair["predicted"]
        observed = pair["observed"]
        if predicted != 0:
            ratio = observed / predicted
            ratios.append(ratio)
    
    if not ratios:
        return None
    
    avg_ratio = sum(ratios) / len(ratios)
    
    # Calculate new elasticity coefficients
    # Simplified: assume utilization elasticity and cost elasticity scale similarly
    base_utilization_elasticity = -0.8  # Default baseline
    base_cost_elasticity = -0.75  # Default baseline
    
    new_utilization_elasticity = base_utilization_elasticity * avg_ratio
    new_cost_elasticity = base_cost_elasticity * avg_ratio
    
    # Calculate training metrics
    errors = [abs(pair["observed"] - pair["predicted"]) for pair in valid_pairs]
    mae = sum(errors) / len(errors) if errors else 0.0
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0
    
    # Confidence based on number of observations
    observation_count = len(valid_pairs)
    confidence = min(0.95, 0.5 + (observation_count / 20.0))  # Increases with more observations, caps at 0.95
    
    elasticity_coefficients = {
        "utilization_elasticity": new_utilization_elasticity,
        "cost_elasticity": new_cost_elasticity,
    }
    
    training_metrics = {
        "observation_count": observation_count,
        "mae": mae,
        "rmse": rmse,
    }
    
    learned_from_observations = [pair["observation_id"] for pair in valid_pairs]
    
    if existing_model:
        # Update existing model
        model_id = existing_model.get("model_id")
        next_version = existing_model.get("version", "v1.0")
        # Simple version increment (in production, would use semantic versioning)
        version_parts = next_version.lstrip("v").split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = "v" + ".".join(version_parts)
        
        updates = {
            "version": new_version,
            "elasticity_coefficients": elasticity_coefficients,
            "learned_from_observations": learned_from_observations,
            "confidence": confidence,
            "training_metrics": training_metrics,
            "refresh_reason": "MODEL_UPDATED",  # Track why model was updated
            "last_refresh_timestamp": datetime.utcnow().isoformat(),
        }
        
        updated_model = update_elasticity_model(tenant_id, model_id, updates)
        
        # Item 3: Continuous Learning Cycle - Mark affected policies for prediction refresh
        try:
            from uepi_api.storage_policies import list_policies
            all_policies = list_policies(tenant_id)
            affected_policies = [
                p for p in all_policies 
                if p.get("policy_type") == policy_type and p.get("status") in ["ACTIVE", "active"]
            ]
            
            # Mark policies with stale predictions
            for policy in affected_policies:
                policy_id = UUID(policy.get("id") or policy.get("policy_id"))
                metadata = policy.get("metadata", {})
                metadata["prediction_stale"] = True
                metadata["prediction_based_on_model_version"] = existing_model.get("version")
                metadata["latest_model_version"] = new_version
                metadata["prediction_refresh_recommended_at"] = datetime.utcnow().isoformat()
                
                from uepi_api.storage_policies import update_policy
                update_policy(policy_id, tenant_id, {"metadata": metadata})
            
            print(f"✅ Marked {len(affected_policies)} policies for prediction refresh after model update")
        except Exception as e:
            print(f"⚠️ Could not mark policies for refresh: {e}")
        
        return updated_model
    else:
        # Create new model
        model_data = {
            "version": "v1.0",
            "policy_type": policy_type,
            "service_category": service_category,
            "elasticity_coefficients": elasticity_coefficients,
            "learned_from_observations": learned_from_observations,
            "confidence": confidence,
            "training_metrics": training_metrics,
            "refresh_reason": "MODEL_UPDATED",  # Track why model was created/updated
            "metadata": {},
        }
        
        new_model = create_elasticity_model(tenant_id=tenant_id, model_data=model_data)
        return new_model


def learn_from_observation(
    tenant_id: UUID,
    observation_id: str,
) -> Dict[str, Any]:
    """Learn from an observation - main learning function
    
    This function:
    1. Gets the observation
    2. Records prediction accuracy
    3. Updates elasticity models if enough observations are available
    
    Args:
        tenant_id: Tenant ID
        observation_id: Observation ID
        
    Returns:
        Learning results dictionary
    """
    try:
        # Get observation
        observation = get_observation(tenant_id, observation_id)
        if not observation:
            return {
                "success": False,
                "error": "Observation not found",
            }
        
        policy_id = UUID(observation.get("policy_id"))
        
        # Get comparisons
        comparisons = observation.get("comparisons", {})
        vs_predicted = comparisons.get("vs_predicted", {})
        
        # Record accuracy if predicted comparison exists
        accuracy_record = None
        if vs_predicted:
            predicted_effect_size = vs_predicted.get("predicted_effect_size")
            observed_effect_size = vs_predicted.get("observed_effect_size")
            
            if predicted_effect_size is not None and observed_effect_size is not None:
                accuracy_record = record_prediction_accuracy(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                    observation_id=observation_id,
                    predicted_effect_size=predicted_effect_size,
                    observed_effect_size=observed_effect_size,
                    prediction_id=vs_predicted.get("prediction_id"),
                )
        
        # Get policy to determine policy type
        policy = get_policy(policy_id, tenant_id)
        policy_type = policy.get("policy_type", "PRIOR_AUTH") if policy else "PRIOR_AUTH"
        
        # Get all observations for this policy to update elasticity model
        from uepi_api.storage_observations import get_observations_for_policy
        policy_observations = get_observations_for_policy(tenant_id, policy_id)
        
        # Update elasticity model if we have enough observations (threshold: 3)
        elasticity_model = None
        if len(policy_observations) >= 3:
            elasticity_model = update_elasticity_from_observations(
                tenant_id=tenant_id,
                policy_type=policy_type,
                observations=policy_observations,
                service_category=None,  # Could be extracted from policy/observation
            )
        
        return {
            "success": True,
            "observation_id": observation_id,
            "accuracy_recorded": accuracy_record is not None,
            "accuracy_record_id": accuracy_record.get("accuracy_id") if accuracy_record else None,
            "elasticity_model_updated": elasticity_model is not None,
            "elasticity_model_id": elasticity_model.get("model_id") if elasticity_model else None,
        }
        
    except Exception as e:
        print(f"Error learning from observation {observation_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
        }


def get_prediction_accuracy_summary(
    tenant_id: UUID,
    policy_id: UUID,
) -> Dict[str, Any]:
    """Get prediction accuracy summary for a policy
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        
    Returns:
        Accuracy summary dictionary
    """
    accuracy_records = list_accuracy_records(tenant_id=tenant_id, policy_id=policy_id)
    
    if not accuracy_records:
        return {
            "policy_id": str(policy_id),
            "total_observations": 0,
            "average_accuracy_pct": None,
            "average_mae": None,
            "average_rmse": None,
            "records": [],
        }
    
    # Calculate averages
    accuracy_pcts = [r.get("prediction_accuracy_pct", 0.0) for r in accuracy_records]
    maes = [r.get("metrics", {}).get("mae", 0.0) for r in accuracy_records]
    rmses = [r.get("metrics", {}).get("rmse", 0.0) for r in accuracy_records]
    
    avg_accuracy_pct = sum(accuracy_pcts) / len(accuracy_pcts) if accuracy_pcts else 0.0
    avg_mae = sum(maes) / len(maes) if maes else 0.0
    avg_rmse = sum(rmses) / len(rmses) if rmses else 0.0
    
    return {
        "policy_id": str(policy_id),
        "total_observations": len(accuracy_records),
        "average_accuracy_pct": avg_accuracy_pct,
        "average_mae": avg_mae,
        "average_rmse": avg_rmse,
        "records": accuracy_records[:10],  # Return latest 10 records
    }
