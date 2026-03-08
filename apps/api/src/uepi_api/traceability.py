"""Traceability framework - Link insights to data periods and policy versions"""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import json


def add_traceability(
    insight: Dict[str, Any],
    data_period_id: Optional[str] = None,
    data_period_version: Optional[int] = None,
    policy_version_id: Optional[str] = None,
    baseline_version_id: Optional[str] = None,
    refresh_reason: Optional[str] = None,
    dependencies: Optional[list[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Add traceability metadata to an insight
    
    Args:
        insight: The insight dictionary (baseline, prediction, observation)
        data_period_id: ID of the data period used
        data_period_version: Version of the data period
        policy_version_id: ID of the policy version used
        baseline_version_id: ID of the baseline version used
        refresh_reason: Reason for refresh (NEW_DATA, POLICY_UPDATE, MANUAL, etc.)
        dependencies: List of dependent insights
        
    Returns:
        Insight dictionary with traceability metadata added
    """
    now = datetime.utcnow().isoformat()
    
    # Initialize traceability if not exists
    if "traceability" not in insight:
        insight["traceability"] = {
            "created_at": now,
            "updated_at": now,
            "refresh_count": 0,
            "dependencies": [],
        }
    else:
        insight["traceability"]["updated_at"] = now
        insight["traceability"]["refresh_count"] = insight["traceability"].get("refresh_count", 0) + 1
    
    # Update traceability fields
    traceability = insight["traceability"]
    
    if data_period_id:
        traceability["data_period_id"] = data_period_id
    if data_period_version:
        traceability["data_period_version"] = data_period_version
    if policy_version_id:
        traceability["policy_version_id"] = policy_version_id
    if baseline_version_id:
        traceability["baseline_version_id"] = baseline_version_id
    if refresh_reason:
        traceability["refresh_reason"] = refresh_reason
    if dependencies:
        traceability["dependencies"] = dependencies
    
    return insight


def get_traceability(insight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get traceability metadata from an insight"""
    return insight.get("traceability")


def query_by_traceability(
    insights: list[Dict[str, Any]],
    data_period_id: Optional[str] = None,
    policy_version_id: Optional[str] = None,
    baseline_version_id: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """Query insights by traceability criteria
    
    Args:
        insights: List of insights to filter
        data_period_id: Filter by data period ID
        policy_version_id: Filter by policy version ID
        baseline_version_id: Filter by baseline version ID
        
    Returns:
        Filtered list of insights
    """
    filtered = []
    
    for insight in insights:
        traceability = insight.get("traceability", {})
        
        # Apply filters
        if data_period_id and traceability.get("data_period_id") != data_period_id:
            continue
        if policy_version_id and traceability.get("policy_version_id") != policy_version_id:
            continue
        if baseline_version_id and traceability.get("baseline_version_id") != baseline_version_id:
            continue
        
        filtered.append(insight)
    
    return filtered


def detect_refresh_triggers(
    insight: Dict[str, Any],
    new_data_period_id: Optional[str] = None,
    new_policy_version_id: Optional[str] = None,
    new_baseline_version_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Detect if an insight needs to be refreshed
    
    Args:
        insight: The insight to check
        new_data_period_id: New data period ID (if new data arrived)
        new_policy_version_id: New policy version ID (if policy was updated)
        new_baseline_version_id: New baseline version ID (if baseline was refreshed)
        
    Returns:
        Dictionary with refresh trigger information
    """
    traceability = insight.get("traceability", {})
    
    triggers = []
    needs_refresh = False
    
    # Check data period
    if new_data_period_id and traceability.get("data_period_id") != new_data_period_id:
        triggers.append({
            "type": "NEW_DATA",
            "old_data_period_id": traceability.get("data_period_id"),
            "new_data_period_id": new_data_period_id,
        })
        needs_refresh = True
    
    # Check policy version
    if new_policy_version_id and traceability.get("policy_version_id") != new_policy_version_id:
        triggers.append({
            "type": "POLICY_UPDATE",
            "old_policy_version_id": traceability.get("policy_version_id"),
            "new_policy_version_id": new_policy_version_id,
        })
        needs_refresh = True
    
    # Check baseline version
    if new_baseline_version_id and traceability.get("baseline_version_id") != new_baseline_version_id:
        triggers.append({
            "type": "BASELINE_REFRESH",
            "old_baseline_version_id": traceability.get("baseline_version_id"),
            "new_baseline_version_id": new_baseline_version_id,
        })
        needs_refresh = True
    
    return {
        "needs_refresh": needs_refresh,
        "triggers": triggers,
        "current_traceability": traceability,
    }


def generate_audit_trail(
    insight: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate audit trail for an insight
    
    Args:
        insight: The insight to generate audit trail for
        
    Returns:
        Audit trail dictionary
    """
    traceability = insight.get("traceability", {})
    
    audit_trail = {
        "insight_id": insight.get("id") or insight.get("baseline_id") or insight.get("prediction_id") or insight.get("observation_id"),
        "insight_type": insight.get("type") or "unknown",
        "created_at": traceability.get("created_at"),
        "updated_at": traceability.get("updated_at"),
        "refresh_count": traceability.get("refresh_count", 0),
        "data_period": {
            "period_id": traceability.get("data_period_id"),
            "version": traceability.get("data_period_version"),
        },
        "policy_version": {
            "version_id": traceability.get("policy_version_id"),
        },
        "baseline_version": {
            "version_id": traceability.get("baseline_version_id"),
        },
        "dependencies": traceability.get("dependencies", []),
        "refresh_reason": traceability.get("refresh_reason"),
    }
    
    return audit_trail
