"""
Helper functions for generating and storing predicted impact (Stage 3.5)
"""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from uepi_common.analytics.predicted_impact import PredictedImpactGenerator, PredictedImpactResult


def generate_predicted_impact_for_policy(
    tenant_id: UUID,
    policy_id: UUID | str,
    policy_levers: list[Dict[str, Any]],
    policy_scope: Optional[Dict[str, Any]] = None,
    baseline_metrics: Optional[Dict[str, Any]] = None,
) -> PredictedImpactResult:
    """
    Generate predicted impact for a policy (Stage 3.5)
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID (UUID or string)
        policy_levers: List of policy levers
        policy_scope: Policy scope (lob, markets, network)
        baseline_metrics: Optional baseline metrics
        
    Returns:
        PredictedImpactResult
    """
    # Convert string ID to UUID for the model (use a placeholder UUID for string IDs)
    # The actual policy_id will be stored as string in the policy data
    if isinstance(policy_id, str):
        # For string IDs, generate a deterministic UUID from the string
        # This allows the model to work while preserving the original string ID
        import hashlib
        namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        policy_id_uuid = UUID(bytes=hashlib.md5(namespace.bytes + policy_id.encode()).digest())
    else:
        policy_id_uuid = policy_id
    
    generator = PredictedImpactGenerator(tenant_id=tenant_id)
    
    # Load latest elasticity data if available (Item 2 & 9)
    elasticity_data = None
    try:
        from uepi_api.storage_learning import get_latest_elasticity_model
        from uepi_api.storage_policies import get_policy
        
        policy = get_policy(policy_id, tenant_id)
        if policy:
            policy_type = policy.get("policy_type", "PRIOR_AUTH")
            # Get latest elasticity model for this policy type
            latest_model = get_latest_elasticity_model(
                tenant_id=tenant_id,
                policy_type=policy_type,
                service_category=None,
            )
            if latest_model and latest_model.get("elasticity_coefficients"):
                elasticity_data = latest_model.get("elasticity_coefficients")
                print(f"✅ Using latest elasticity model {latest_model.get('model_id')} (v{latest_model.get('version')}) for predicted impact")
    except Exception as e:
        print(f"⚠️ Could not load elasticity model, using defaults: {e}")
    
    # Phase 2: Use policy-specific baseline when available (same filters as baseline computation)
    if not baseline_metrics:
        from uepi_api.storage_baselines import get_latest_baseline
        policy_id_for_baseline = policy_id if isinstance(policy_id, UUID) else None
        if policy_id_for_baseline is None and isinstance(policy_id, str):
            try:
                policy_id_for_baseline = UUID(policy_id)
            except (ValueError, TypeError):
                policy_id_for_baseline = None
        # Policy baselines are stored with baseline_type=ROLLING; look by policy_id only
        policy_baseline = get_latest_baseline(tenant_id, policy_id=policy_id_for_baseline, baseline_type=None)
        if not policy_baseline:
            policy_baseline = get_latest_baseline(tenant_id, policy_id=None)
        if policy_baseline:
            baseline_metrics = policy_baseline.get("baseline_metrics", {}) or policy_baseline.get("metrics", {})
            print(f"✅ Using {'policy-specific' if policy_baseline.get('policy_id') else 'general'} baseline for prediction")
    
    # Generate predicted impact (use UUID version for the model)
    result = generator.generate_predicted_impact(
        policy_id=policy_id_uuid,
        policy_levers=policy_levers,
        policy_scope=policy_scope,
        baseline_metrics=baseline_metrics,
        elasticity_data=elasticity_data,
    )
    
    # Phase 1 & 2: Enhance with confidence intervals and time-based ramp-up
    # Store enhanced data in result for later use
    try:
        from uepi_api.services.prediction_enhancement_service import enhance_prediction_with_confidence_and_ramp_up
        
        result_dict = result.model_dump(mode='json')
        enhanced_result = enhance_prediction_with_confidence_and_ramp_up(
            tenant_id=tenant_id,
            policy_id=policy_id if isinstance(policy_id, UUID) else UUID(str(policy_id)),
            predicted_impact=result_dict,
            baseline_metrics=baseline_metrics,
        )
        
        # Store enhanced data in result object for later retrieval
        result._enhanced_data = enhanced_result
    except Exception as e:
        print(f"⚠️  Could not enhance prediction with confidence intervals/ramp-up: {e}")
        import traceback
        traceback.print_exc()
    
    # If original policy_id was a string, store it for later use
    if isinstance(policy_id, str):
        result._policy_id_str = policy_id  # Store original string ID
    
    return result


def store_predicted_impact_in_metadata(
    policy_metadata: Dict[str, Any],
    predicted_impact: PredictedImpactResult,
) -> Dict[str, Any]:
    """
    Store predicted impact in policy metadata JSON
    
    Args:
        policy_metadata: Existing policy metadata dict
        predicted_impact: PredictedImpactResult to store
        
    Returns:
        Updated policy_metadata dict
    """
    if policy_metadata is None:
        policy_metadata = {}
    
    # Convert PredictedImpactResult to dict for JSON storage
    predicted_impact_dict = predicted_impact.model_dump(mode='json')
    
    policy_metadata["predicted_impact"] = predicted_impact_dict
    
    return policy_metadata


def get_predicted_impact_from_metadata(
    policy_metadata: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Extract predicted impact from policy metadata
    
    Args:
        policy_metadata: Policy metadata dict
        
    Returns:
        Predicted impact dict if available, None otherwise
    """
    if not policy_metadata:
        return None
    
    return policy_metadata.get("predicted_impact")
