"""
Epic 5: Behavioral Signal Detection - API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from uepi_api.auth import get_demo_current_user, CurrentUser
from uepi_api.storage_behavior_signals import (
    create_behavior_profile,
    get_behavior_profile,
    list_behavior_profiles,
    update_behavior_profile,
    create_behavior_cluster,
    get_behavior_cluster,
    list_behavior_clusters,
)
from uepi_api.storage_alert_rules import (
    create_alert_rule,
    get_alert_rule,
    list_alert_rules,
    update_alert_rule,
    create_alert_event,
    list_alert_events,
)
from uepi_common.models_enhanced import BehaviorType

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


# Behavior Profiles
@router.post("/behavior-profiles")
async def create_behavior_profile_endpoint(
    profile_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new behavior profile"""
    try:
        profile = create_behavior_profile(
            tenant_id=current_user.tenant_id,
            profile_data=profile_data,
        )
        return profile.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create behavior profile: {str(e)}")


@router.get("/behavior-profiles")
async def list_behavior_profiles_endpoint(
    behavior_type: Optional[str] = None,
    min_confidence: Optional[float] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List behavior profiles"""
    try:
        bt = BehaviorType(behavior_type) if behavior_type else None
        profiles = list_behavior_profiles(
            tenant_id=current_user.tenant_id,
            behavior_type=bt,
            min_confidence=min_confidence,
        )
        return [p.model_dump(mode='json', exclude_none=True) for p in profiles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list behavior profiles: {str(e)}")


@router.get("/behavior-profiles/{provider_id}")
async def get_behavior_profile_endpoint(
    provider_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get behavior profile for a provider"""
    try:
        profile = get_behavior_profile(
            tenant_id=current_user.tenant_id,
            provider_id=provider_id,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Behavior profile not found")
        return profile.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get behavior profile: {str(e)}")


@router.put("/behavior-profiles/{provider_id}")
async def update_behavior_profile_endpoint(
    provider_id: str,
    updates: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Update behavior profile"""
    try:
        profile = update_behavior_profile(
            tenant_id=current_user.tenant_id,
            provider_id=provider_id,
            updates=updates,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Behavior profile not found")
        return profile.model_dump(mode='json', exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update behavior profile: {str(e)}")


# Behavior Clusters
@router.post("/behavior-clusters")
async def create_behavior_cluster_endpoint(
    cluster_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new behavior cluster"""
    try:
        cluster = create_behavior_cluster(
            tenant_id=current_user.tenant_id,
            cluster_data=cluster_data,
        )
        return cluster.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create behavior cluster: {str(e)}")


@router.get("/behavior-clusters")
async def list_behavior_clusters_endpoint(
    behavior_type: Optional[str] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List behavior clusters"""
    try:
        bt = BehaviorType(behavior_type) if behavior_type else None
        clusters = list_behavior_clusters(
            tenant_id=current_user.tenant_id,
            behavior_type=bt,
        )
        return [c.model_dump(mode='json', exclude_none=True) for c in clusters]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list behavior clusters: {str(e)}")


@router.get("/behavior-clusters/{cluster_id}")
async def get_behavior_cluster_endpoint(
    cluster_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get behavior cluster"""
    try:
        cluster_uuid = UUID(cluster_id)
        cluster = get_behavior_cluster(
            tenant_id=current_user.tenant_id,
            cluster_id=cluster_uuid,
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Behavior cluster not found")
        return cluster.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cluster ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get behavior cluster: {str(e)}")


# Alert Rules
@router.post("/alert-rules")
async def create_alert_rule_endpoint(
    rule_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new alert rule"""
    try:
        rule = create_alert_rule(
            tenant_id=current_user.tenant_id,
            rule_data=rule_data,
        )
        return rule.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")


@router.get("/alert-rules")
async def list_alert_rules_endpoint(
    enabled_only: bool = False,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List alert rules"""
    try:
        rules = list_alert_rules(
            tenant_id=current_user.tenant_id,
            enabled_only=enabled_only,
        )
        return [r.model_dump(mode='json', exclude_none=True) for r in rules]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alert rules: {str(e)}")


@router.get("/alert-rules/{rule_id}")
async def get_alert_rule_endpoint(
    rule_id: str,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Get alert rule"""
    try:
        rule_uuid = UUID(rule_id)
        rule = get_alert_rule(
            tenant_id=current_user.tenant_id,
            rule_id=rule_uuid,
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return rule.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert rule: {str(e)}")


@router.put("/alert-rules/{rule_id}")
async def update_alert_rule_endpoint(
    rule_id: str,
    updates: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Update alert rule"""
    try:
        rule_uuid = UUID(rule_id)
        rule = update_alert_rule(
            tenant_id=current_user.tenant_id,
            rule_id=rule_uuid,
            updates=updates,
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return rule.model_dump(mode='json', exclude_none=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update alert rule: {str(e)}")


# Alert Events
@router.post("/alert-events")
async def create_alert_event_endpoint(
    event_data: dict,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """Create a new alert event"""
    try:
        event = create_alert_event(
            tenant_id=current_user.tenant_id,
            event_data=event_data,
        )
        return event.model_dump(mode='json', exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert event: {str(e)}")


@router.get("/alert-events")
async def list_alert_events_endpoint(
    policy_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    acknowledged_only: Optional[bool] = None,
    current_user: CurrentUser = Depends(get_demo_current_user),
):
    """List alert events"""
    try:
        policy_uuid = None
        if policy_id:
            try:
                policy_uuid = UUID(policy_id)
            except ValueError:
                # Not a UUID, convert using helper
                policy_uuid = convert_policy_id_to_uuid(policy_id, current_user.tenant_id)
        events = list_alert_events(
            tenant_id=current_user.tenant_id,
            policy_id=policy_uuid,
            provider_id=provider_id,
            acknowledged_only=acknowledged_only,
        )
        return [e.model_dump(mode='json', exclude_none=True) for e in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alert events: {str(e)}")

